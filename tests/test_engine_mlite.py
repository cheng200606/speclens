"""M-lite 引擎链路测试：ingest → extract → route → review（全离线）。"""

from pathlib import Path

from baselines import get_baseline
from bench.harness.loader import load_cases
from engine.extract import extract_rules
from engine.ingest import parse_document
from engine.route import route_rules

REPO = Path(__file__).resolve().parent.parent
REACT19 = REPO / "bench" / "specs" / "react19"


class _EchoRuleAdapter:
    """遵循「规则找代码」契约：meta 带 rule_id 时返回空 findings 的合法输出。"""

    name = "mock-echo-rule"

    def complete_json(self, *, system, user, schema, meta=None):
        return schema.model_validate({"findings": []})


def test_ingest_sections_have_sources():
    sections = parse_document(REACT19)
    assert len(sections) >= 10
    assert all(s["source"].endswith(".md") for s in sections)
    assert any("use" in s["section"].lower() for s in sections)


def test_extract_rules_grounding_and_levels():
    rules = extract_rules(REACT19)
    assert 10 <= len(rules) <= 400  # I7 adaptive cap 随规范规模
    for r in rules:
        assert r.level in ("MUST", "SHOULD")
        assert r.source_span.quote == r.assertion  # 溯源即断言原文
        assert len(r.assertion) >= 25  # I7 行候选最短 25 字符
    assert any(r.level == "MUST" for r in rules)
    # 规范句已知存在于快照：use 必须在组件或 Hook 内调用
    assert any("must be called inside a Component or a Hook" in r.assertion for r in rules)


def test_extract_rules_deterministic():
    assert extract_rules(REACT19) == extract_rules(REACT19)


def test_route_matches_cues():
    rules = extract_rules(REACT19)
    code_with_use_effect = "import { useEffect } from 'react';\nuseEffect(() => {});"
    applicable = route_rules(rules, code_with_use_effect)
    # 至少有一条 useEffect 相关规则被路由到
    assert any(
        "useEffect" in r.trigger.ast_cues or not r.trigger.ast_cues for r in applicable
    )


def test_m_lite_registered_and_offline_predictable():
    baseline = get_baseline("m_lite")
    assert baseline.BASELINE_ID == "m_lite"
    cases = load_cases(REPO / "bench" / "cases" / "react19")
    findings = baseline.predict_case(cases[0], _EchoRuleAdapter())
    assert findings == []


def test_b1_registered_and_prompt_contains_spec():
    from baselines import b1_full_spec

    cases = load_cases(REPO / "bench" / "cases" / "react19")
    case = cases[0]
    spec_text, used = __import__(
        "bench.harness.spec_text", fromlist=["spec_text_for_case"]
    ).spec_text_for_case(case)
    prompt = b1_full_spec.build_user_prompt(case, spec_text)
    assert "# Specification document" in prompt
    assert case.read_file(case.meta.files[0]) in prompt
    assert used


def test_b1_predict_with_mock_expected():
    from bench.harness.runner import build_mock_expected

    baseline = get_baseline("b1_full_spec")
    cases = load_cases(REPO / "bench" / "cases" / "react19")
    from bench.harness.model_adapter import MockPerfectAdapter

    adapter = MockPerfectAdapter(build_mock_expected(cases))
    findings = baseline.predict_case(cases[0], adapter)
    assert findings and findings[0].case_id == "TS-001"
    assert findings[0].rule_ids == ["R-001"]


# ---------------------------------------------------------------- I9① review_prompt 轴

def test_review_prompt_variant_scoped_v2():
    """scoped-v2 追加范围纪律段；v1 不变；非法变体报错。"""
    from bench.harness.model_adapter import make_adapter
    from bench.harness.schemas import RuleRecord, SourceSpan, Trigger
    from engine.review import _prompt_variant, _rule_prompt

    def adapter(cfg):
        return make_adapter("mock-perfect", {}, temperature=0.0, run_config=cfg)

    r = RuleRecord(
        id="R-001", spec_id="react19", level="MUST", category="T2-api-usage",
        assertion="x", source_span=SourceSpan(section="s", quote="q"),
        trigger=Trigger(scenario="s", ast_cues=[]),
    )
    assert _prompt_variant(adapter({})) == "v1"
    assert _prompt_variant(adapter({"review_prompt": "scoped-v2"})) == "scoped-v2"
    v1, v2 = _rule_prompt(r, "code", "v1"), _rule_prompt(r, "code", "scoped-v2")
    assert v2.startswith(v1)
    assert "verbatim in every finding" in v2 and "speculative" in v2
    assert "speculative" not in v1
    try:
        _prompt_variant(adapter({"review_prompt": "bogus"}))
        raise AssertionError("bogus review_prompt 应报错")
    except ValueError:
        pass
