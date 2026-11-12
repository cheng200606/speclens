"""engine/verify 三道关测试（全离线，LLM 分支用 scripted mock）。"""

import json
from pathlib import Path

import pytest

from bench.harness.schemas import (
    RuleRecord,
    RuleVerification,
    SourceSpan,
    Trigger,
    Finding,
    FindingEvidence,
)
from engine.extract import extract_rules
from engine.verify import (
    RuleExamples,
    detect_conflicts,
    executability_test,
    grounding_score,
    verify_rules,
)

REPO = Path(__file__).resolve().parent.parent
REACT19 = REPO / "bench" / "specs" / "react19"


def _rule(
    rid: str,
    assertion: str,
    quote: str,
    level: str = "MUST",
    cues: list[str] | None = None,
) -> RuleRecord:
    return RuleRecord(
        id=rid,
        spec_id="react19",
        level=level,  # type: ignore[arg-type]
        category="T2-api-usage",
        trigger=Trigger(scenario="test", ast_cues=cues or []),
        assertion=assertion,
        source_span=SourceSpan(section="test", quote=quote),
    )


# ---------- 门 1：grounding ----------

def test_grounding_extracted_rules_all_traceable():
    rules = extract_rules(REACT19)
    from bench.harness.spec_text import assemble_spec_text

    spec_text, _ = assemble_spec_text(REACT19)
    spec_norm = __import__("engine.verify", fromlist=["_norm"])._norm(spec_text)
    scores = [grounding_score(r, spec_norm)[0] for r in rules]
    assert all(0.0 <= s <= 1.0 for s in scores)
    # 引句均逐字来自快照 → quote_in_spec 恒真，平均分不应过低
    assert sum(scores) / len(scores) >= 0.6


def test_grounding_bogus_quote_flagged():
    from bench.harness.spec_text import assemble_spec_text

    spec_text, _ = assemble_spec_text(REACT19)
    spec_norm = __import__("engine.verify", fromlist=["_norm"])._norm(spec_text)
    good = _rule("X-001", "`use` must be called inside a Component or a Hook.",
                 "`use` must be called inside a Component or a Hook.")
    bad = _rule("X-002", "Always cache promises in Redis.",
                "Promises must be stored in a Redis cluster with TTL 3600.")
    s_good, d_good = grounding_score(good, spec_norm)
    s_bad, d_bad = grounding_score(bad, spec_norm)
    assert d_good["quote_in_spec"] is True
    assert d_bad["quote_in_spec"] is False
    assert s_good > s_bad and s_bad < 0.6


def test_grounding_level_consistency():
    from bench.harness.spec_text import assemble_spec_text

    spec_text, _ = assemble_spec_text(REACT19)
    spec_norm = __import__("engine.verify", fromlist=["_norm"])._norm(spec_text)
    # SHOULD 明确、MUST 缺席的引句
    quote = "For more details on why fetching in an Effect is discouraged, see the guide."
    consistent = _rule("X-010", quote, quote, level="SHOULD")
    inconsistent = _rule("X-011", quote, quote, level="MUST")
    s_c, d_c = grounding_score(consistent, spec_norm)
    s_i, d_i = grounding_score(inconsistent, spec_norm)
    assert d_c["level_consistent"] is True
    assert d_i["level_consistent"] is False
    assert s_c > s_i


# ---------- 门 3：conflict ----------

def test_conflict_offline_duplicates_only():
    """离线模式：只报断言重复（确定性）；极性相反但语义相容的规则对不误报。"""
    d1 = _rule("B-1", "Do not call hooks inside loops.", "do not", cues=["use"])
    d2 = _rule("B-2", "Do not call hooks inside loops.", "do not", cues=["use"])
    # 极性相反但共享 cue——语义上并不矛盾（不同主题），离线模式不得报
    p1 = _rule("B-4", "`use` must be called inside a Component or a Hook.",
               "must", cues=["use"])
    p2 = _rule("B-5", "`use` cannot be called inside a try-catch block.",
               "cannot", cues=["use"])
    conflicts = detect_conflicts([d1, d2, p1, p2], adapter=None)
    assert any("duplicate" in c for c in conflicts.get("B-1", []))
    assert any("duplicate" in c for c in conflicts.get("B-2", []))
    assert not any("B-4" in c for c in conflicts.get("B-5", []))
    assert not any("B-5" in c for c in conflicts.get("B-4", []))


class _ScriptedContraAdapter:
    """LLM 矛盾判定的脚本化 mock：认为 A-4 与 A-5 矛盾，其余不矛盾。"""

    name = "scripted-contra"

    def complete_json(self, *, system, user, schema, meta=None):
        contradict = {meta["rule_id"], meta["other"]} == {"A-4", "A-5"}
        return schema.model_validate({"contradict": contradict})


def test_conflict_llm_mode_records_verdict_both_sides():
    a4 = _rule("A-4", "You must always call useState at the top level.",
               "must always", cues=["useState"])
    a5 = _rule("A-5", "Avoid calling useState inside conditions.",
               "avoid calling", cues=["useState"])
    other = _rule("A-6", "Promises passed to `use` must be cached.",
                  "must", cues=["Promise"])
    conflicts = detect_conflicts([a4, a5, other], adapter=_ScriptedContraAdapter())
    assert conflicts["A-4"] == ["A-5:llm-contradict"]
    assert conflicts["A-5"] == ["A-4:llm-contradict"]
    assert "A-6" not in conflicts


# ---------- 门 2：executability ----------

class _ScriptedExecAdapter:
    """合成固定正反例；审查阶段按代码是否含 BAD 标记决定检出。"""

    name = "scripted-exec"

    def __init__(self, neg_detected: bool = True, raise_on_synth: bool = False) -> None:
        self.neg_detected = neg_detected
        self.raise_on_synth = raise_on_synth

    def complete_json(self, *, system, user, schema, meta=None):
        if schema is RuleExamples:
            if self.raise_on_synth:
                raise RuntimeError("synth unavailable")
            return schema.model_validate(
                {"pos_example": "const ok = 1;", "neg_example": "// BAD\nconst bad = 1;"}
            )
        if self.neg_detected and "BAD" in meta.get("code_head", ""):
            return schema.model_validate(
                {"findings": [
                    Finding(
                        file="snippet.tsx",
                        line_start=1,
                        line_end=1,
                        rule_ids=[meta["rule_id"]],
                        message="violates",
                        evidence=FindingEvidence(),
                    )
                ]}
            )
        return schema.model_validate({"findings": []})


def test_executability_pass_and_fail_branches():
    rule = _rule("C-1", "`use` must be called inside a Component or a Hook.",
                 "`use` must be called inside a Component or a Hook.", cues=["use"])
    assert executability_test(rule, _ScriptedExecAdapter(True)) == "pass"
    assert executability_test(rule, _ScriptedExecAdapter(False)) == "fail"


def test_executability_offline_stays_pending():
    rules = [_rule("C-2", "Promises passed to `use` must be cached.",
                   "Promises passed to `use` must be cached.", cues=["use"])]
    out, report = verify_rules(rules, REACT19, adapter=None)
    assert out[0].verification.exec_test == "pending"
    assert report["gate2_llm"] is False


def test_executability_synth_error_flagged():
    rule = _rule("C-3", "Promises passed to `use` must be cached.",
                 "Promises passed to `use` must be cached.", cues=["use"])
    out, report = verify_rules([rule], REACT19, adapter=_ScriptedExecAdapter(raise_on_synth=True))
    assert out[0].verification.exec_test == "fail"
    assert any("exec-error" in f["reasons"] for f in report["flagged_for_review"])


# ---------- 汇总 verify_rules ----------

def test_verify_rules_end_to_end_offline_deterministic():
    rules = extract_rules(REACT19)
    out1, report1 = verify_rules(rules, REACT19)
    out2, report2 = verify_rules(rules, REACT19)
    assert report1 == report2
    assert [r.model_dump() for r in out1] == [r.model_dump() for r in out2]
    assert report1["n_rules"] == len(rules)
    assert report1["gate2_llm"] is False
    assert all(r.verification.grounding is not None for r in out1)
    # 汇总里所有 flagged 都有理由
    assert all(f["reasons"] for f in report1["flagged_for_review"])
    assert report1["n_flagged"] == len(report1["flagged_for_review"])


def test_verify_cli_smoke(tmp_path: Path):
    from engine.verify import main

    output = tmp_path / "verify-report.json"
    main(["--spec", "react19", "--repo-root", str(REPO), "--output", str(output)])
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["report"]["n_rules"] > 0
    assert all("verification" in r for r in data["rules"])
