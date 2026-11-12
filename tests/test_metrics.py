"""指标口径测试（plan.md §1.3 的检测率/误报率定义）。"""

from bench.harness.metrics import CaseOutcome, compute_metrics
from bench.harness.schemas import Finding, FindingEvidence, Verdict


def _finding(rule_id: str) -> Finding:
    return Finding(
        file="code/a.tsx",
        line_start=1,
        line_end=1,
        rule_ids=[rule_id],
        message="x",
        evidence=FindingEvidence(rule_quote="q", explanation="e"),
    )


def _violation(case_id: str, rules: list[str], findings: list[Finding]):
    return CaseOutcome(case_id, Verdict.VIOLATION, rules, findings)


def _compliant(case_id: str, rules: list[str], findings: list[Finding]):
    return CaseOutcome(case_id, Verdict.COMPLIANT, rules, findings)


def test_perfect_reviewer():
    outcomes = [
        _violation("A-001", ["R-001"], [_finding("R-001")]),
        _compliant("A-002", ["R-001"], []),
        _violation("A-003", ["R-003"], [_finding("R-003")]),
    ]
    m = compute_metrics(outcomes)
    assert m["detection_rate"] == 1.0
    assert m["false_positive_rate"] == 0.0
    assert m["rule_match_rate"] == 1.0
    assert m["n_borderline"] == 0


def test_missed_and_false_positive():
    outcomes = [
        _violation("A-001", ["R-001"], []),  # 漏报
        _compliant("A-002", ["R-001"], [_finding("R-002")]),  # 误报
        _violation("A-003", ["R-003"], [_finding("R-009")]),  # 检出但规则不命中
    ]
    m = compute_metrics(outcomes)
    # detection 按「有 finding 即检出」计：A-003 检出、A-001 漏报 -> 1/2
    assert m["detection_rate"] == 0.5
    assert m["false_positive_rate"] == 1.0
    # 检出的 1 条中预测规则 R-009 与标注 R-003 不相交 -> 0/1
    assert m["rule_match_rate"] == 0.0


def test_borderline_excluded_from_main_rates():
    outcomes = [
        CaseOutcome("A-004", Verdict.BORDERLINE, ["R-005"], [_finding("R-005")]),
    ]
    m = compute_metrics(outcomes)
    assert m["detection_rate"] is None
    assert m["false_positive_rate"] is None
    assert m["n_borderline"] == 1
    assert m["borderline_predicted"] == 1


def test_rule_match_requires_intersection():
    outcome = _violation("A-001", ["R-001", "R-002"], [_finding("R-002")])
    assert outcome.rule_match is True
