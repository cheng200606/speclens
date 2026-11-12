"""M-verified（完整方法 M）测试：verify 过滤 + trace + 聚合，全离线。"""

from pathlib import Path

from baselines import get_baseline
from bench.harness.loader import load_cases
from bench.harness.runner import build_mock_expected
from bench.harness.model_adapter import MockPerfectAdapter
from engine.verify import verify_rules

REPO = Path(__file__).resolve().parent.parent
REACT19 = REPO / "bench" / "specs" / "react19"


def _excluded_ids() -> set[str]:
    rules = list(get_baseline("m_verified")._verified_rules(str(REACT19.resolve())))
    return {r.id for r in rules if get_baseline("m_verified")._excluded(r)}


def test_m_verified_registered():
    baseline = get_baseline("m_verified")
    assert baseline.BASELINE_ID == "m_verified"


def test_m_verified_offline_filters_flagged_rules():
    # 离线 verify（adapter=None）：gate1 过滤后剩 40 条规则（44 - 4 条低 grounding）
    rules = list(get_baseline("m_verified")._verified_rules(str(REACT19.resolve())))
    excluded = {r.id for r in rules if get_baseline("m_verified")._excluded(r)}
    assert len(excluded) == 4
    kept = {r.id for r in rules} - excluded
    assert len(kept) == 40


def test_m_verified_end_to_end_with_mock():
    baseline = get_baseline("m_verified")
    cases = load_cases(REPO / "bench" / "cases" / "react19")
    adapter = MockPerfectAdapter(build_mock_expected(cases))
    case = cases[0]  # TS-001 (violation)
    findings = baseline.predict_case(case, adapter)
    assert findings, "mock 下 TS-001 应产出 findings"
    excluded = _excluded_ids()
    for f in findings:
        # 证据链已回填（trace）
        assert f.evidence.rule_quote
        assert f.evidence.explanation
        # 主证据规则不在被排除集合中
        assert f.rule_ids[0] not in excluded
    # 聚合去重：无精确重复
    keys = [
        (f.file, f.line_start, f.line_end, frozenset(f.rule_ids), f.message)
        for f in findings
    ]
    assert len(keys) == len(set(keys))


def test_verify_gate_unavailable_stays_pending():
    """MockPerfectAdapter 无法合成 RuleExamples 形状 => 门 2 不可用 => pending 而非 fail。"""
    from bench.harness.model_adapter import MockPerfectAdapter

    rules = list(get_baseline("m_verified")._verified_rules(str(REACT19.resolve())))
    out, report = verify_rules(rules, REACT19, adapter=MockPerfectAdapter({}))
    assert all(r.verification.exec_test == "pending" for r in out)
    assert report["gate2_llm"] is True
