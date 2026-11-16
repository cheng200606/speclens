"""I8④ LLM 规则合成原型测试：引句逐字预校验 + 失败容错。"""

import json
from pathlib import Path
from unittest.mock import patch

from bench.harness.schemas import RuleRecord
from engine.synth import SynthOutput, SynthRule, llm_coverage_diagnostic, synthesize_rules_llm

REPO = Path(__file__).resolve().parent.parent
SPEC = REPO / "bench" / "specs" / "airbnb"


class _FakeAdapter:
    name = "fake-synth"

    def __init__(self, payload: list[dict] | None = None, fail: bool = False, only_section: str | None = None):
        self.payload = payload or []
        self.fail = fail
        self.only_section = only_section

    def complete_json(self, *, system, user, schema, meta=None):
        if self.fail:
            raise RuntimeError("boom")
        if self.only_section is not None and meta and meta.get("section") != self.only_section:
            return SynthOutput(rules=[])
        return SynthOutput(rules=[SynthRule(**r) for r in self.payload])


def test_synth_rejects_nonverbatim_quotes():
    """引句不是章节逐字子串 → 丢弃并计数（门 1 前置校验）。"""
    from engine.extract import _strip_code
    from engine.ingest import parse_document
    from engine.synth import _section_calls

    first = _section_calls(SPEC, 1)[0]
    text = _strip_code(first["text"])
    # 从真实章节文本取一句作为「逐字」引句（测试对提取器改动鲁棒）
    real_quote = next(
        s.strip()
        for s in text.replace("`", "").split(". ")
        if len(s.strip()) >= 40
    )
    adapter = _FakeAdapter(
        [
            {"assertion": real_quote[:60], "quote": real_quote, "level": "MUST", "cues": ["const"]},
            {"assertion": "Fabricated rule.", "quote": "This sentence does not exist in the section at all.", "level": "MUST", "cues": []},
        ],
        only_section=first["section"],
    )
    rules, report = synthesize_rules_llm(SPEC, "airbnb", adapter, max_sections=3, max_rules=48)
    assert report["n_quotes_verbatim"] == 1
    assert report["n_quotes_invalid"] == 1
    assert len(rules) == 1
    assert rules[0].id.startswith("airbnb-llm-")


def test_synth_survives_section_errors():
    """单节 LLM 失败 → fail-soft 记录，不弃整体。"""
    adapter = _FakeAdapter(fail=True)
    rules, report = synthesize_rules_llm(SPEC, "airbnb", adapter, max_sections=2, max_rules=48)
    assert rules == []
    assert report["n_sections_prompted"] >= 1
    assert report.get("section_errors")


def test_synth_llm_coverage_diagnostic_shape():
    """对齐诊断返回冻结库口径的覆盖结构。"""
    rules = [
        RuleRecord(
            id="airbnb-llm-001",
            spec_id="airbnb",
            level="MUST",
            category="T2-api-usage",
            assertion="dummy",
            source_span={"section": "s", "quote": "x"},
            trigger={"scenario": "s", "ast_cues": []},
        )
    ]
    diag = llm_coverage_diagnostic(SPEC, rules)
    assert diag["n_canonical"] == 8
    assert diag["coverage"] == diag["n_matched"] / diag["n_canonical"]
