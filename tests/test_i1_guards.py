"""I1 防误读与验证关上限（probe 隔离 / 冲突检测 cap / McNemar 分组 / 报告标记）。"""

import json
from pathlib import Path

import pytest

from bench.harness.probe import ProbeAnswer, run_probe
from bench.harness.schemas import RuleRecord, SourceSpan, Trigger
from bench.harness.stats import mcnemar_between_runs, mcnemar_subsets
from engine.verify import detect_conflicts
from experiments.make_report import make_report

REPO = Path(__file__).resolve().parent.parent


# ---------- probe 跨模型隔离 ----------

class _Adapter:
    def __init__(self, name: str) -> None:
        self.name = name

    def complete_json(self, *, system, user, schema, meta=None):
        return ProbeAnswer(choice=(meta or {})["answer_index"])


def test_probe_runs_are_isolated_by_model(tmp_path: Path):
    probe = REPO / "bench" / "specs" / "asvs" / "freshness_probe.yaml"
    d1, _ = run_probe(probe, _Adapter("model-alpha"), tmp_path)
    d2, _ = run_probe(probe, _Adapter("model-beta"), tmp_path)
    assert d1 != d2
    assert "model-alpha" in d1.name and "model-beta" in d2.name
    with pytest.raises(RuntimeError, match="禁止覆盖"):
        run_probe(probe, _Adapter("model-alpha"), tmp_path)
    d3, _ = run_probe(probe, _Adapter("model-alpha"), tmp_path, force=True)
    assert d3 == d1


# ---------- 冲突检测 LLM 调用数上限 ----------

def _rule(rid: str, assertion: str) -> RuleRecord:
    return RuleRecord(
        id=rid,
        spec_id="test",
        level="MUST",
        category="T2-api-usage",
        trigger=Trigger(ast_cues=["use"], scenario="test"),
        assertion=assertion,
        source_span=SourceSpan(section="test", quote=assertion),
    )


class _CountingAdapter:
    name = "counting"

    def __init__(self) -> None:
        self.n = 0

    def complete_json(self, *, system, user, schema, meta=None):
        self.n += 1
        return schema.model_validate({"contradict": False})


def test_conflict_detection_caps_llm_calls():
    rules = [_rule(f"C-{i:03d}", f"rule number {i} about use") for i in range(20)]
    adapter = _CountingAdapter()
    stats: dict = {}
    detect_conflicts(rules, adapter=adapter, max_pairs=5, stats=stats)
    assert adapter.n == 5
    assert stats["n_pairs_checked"] == 5
    assert stats["within_cap"] is True
    assert stats["n_pairs_skipped_by_cap"] > 0


# ---------- 分组 McNemar ----------

def _write_run(d: Path, rows: list[dict]) -> Path:
    d.mkdir(parents=True)
    with (d / "results.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return d


def test_mcnemar_subsets(tmp_path: Path):
    a = _write_run(
        tmp_path / "a",
        [
            {"case_id": "V1", "resolved_verdict": "violation", "predicted": True},
            {"case_id": "C1", "resolved_verdict": "compliant", "predicted": False},
            {"case_id": "B1", "resolved_verdict": "borderline", "predicted": True},
        ],
    )
    b = _write_run(
        tmp_path / "b",
        [
            {"case_id": "V1", "resolved_verdict": "violation", "predicted": False},
            {"case_id": "C1", "resolved_verdict": "compliant", "predicted": True},
            {"case_id": "B1", "resolved_verdict": "borderline", "predicted": False},
        ],
    )
    subsets = mcnemar_subsets(a, b)
    assert subsets["all"]["n_paired"] == 2
    assert subsets["violation"]["b_a_right_b_wrong"] == 1
    assert subsets["compliant"]["b_a_right_b_wrong"] == 1
    assert mcnemar_between_runs(a, b, subset="violation")["subset"] == "violation"


# ---------- 报告对 mock 的强制标记 ----------

def test_report_marks_mock_runs_non_scientific(tmp_path: Path):
    runs = tmp_path / "runs"
    for name, baseline in (("g-b0", "b0_zero_shot"), ("g-b1", "b1_full_spec")):
        d = runs / f"{name}-x"
        (d / "raw").mkdir(parents=True, exist_ok=True)
        (d / "config.resolved.yaml").write_text(
            f"baseline: {baseline}\nmodel: mock-perfect\n", encoding="utf-8"
        )
        (d / "summary.json").write_text(
            json.dumps(
                {
                    "baseline": baseline,
                    "model": "mock-perfect",
                    "n_cases": 17,
                    "detection_rate": 1.0,
                    "false_positive_rate": 0.0,
                    "rule_match_rate": 1.0,
                    "code_digest": "abc",
                }
            ),
            encoding="utf-8",
        )
        (d / "results.jsonl").write_text("", encoding="utf-8")
    out = make_report(runs, tmp_path / "report.md", prefix="g")
    text = out.read_text(encoding="utf-8")
    assert "NON-SCIENTIFIC" in text
    assert "不给出 Go/No-Go 判读" in text
    assert "本次判读：不出具" in text
    assert "分组配对检验" in text
