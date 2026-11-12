"""case 级指标（plan.md §1.3 / §5）。

- detection_rate:     violation 样本中被报告 >=1 条 finding 的比例
- false_positive_rate: compliant 样本中被报告 >=1 条 finding 的比例
- rule_match_rate:    被检出的 violation 样本中，预测规则与标注规则相交的比例

borderline 单列计数，不进主指标（其判定存在争议，混入会污染口径）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bench.harness.schemas import Finding, Verdict


@dataclass
class CaseOutcome:
    case_id: str
    resolved_verdict: Verdict
    annotated_rule_ids: list[str]
    findings: list[Finding] = field(default_factory=list)

    @property
    def predicted(self) -> bool:
        return len(self.findings) > 0

    @property
    def rule_match(self) -> bool:
        """检出的前提下，预测规则是否命中任一标注规则。"""
        if not self.predicted:
            return False
        predicted = {r for f in self.findings for r in f.rule_ids}
        return bool(predicted & set(self.annotated_rule_ids))


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def compute_metrics(outcomes: list[CaseOutcome]) -> dict:
    violations = [o for o in outcomes if o.resolved_verdict == Verdict.VIOLATION]
    compliant = [o for o in outcomes if o.resolved_verdict == Verdict.COMPLIANT]
    borderline = [o for o in outcomes if o.resolved_verdict == Verdict.BORDERLINE]

    detected = sum(o.predicted for o in violations)
    rule_matched = sum(o.predicted and o.rule_match for o in violations)
    false_positives = sum(o.predicted for o in compliant)

    return {
        "n_cases": len(outcomes),
        "n_violation": len(violations),
        "n_compliant": len(compliant),
        "n_borderline": len(borderline),
        "detection_rate": _rate(detected, len(violations)),
        "false_positive_rate": _rate(false_positives, len(compliant)),
        "rule_match_rate": _rate(rule_matched, detected),
        "borderline_predicted": sum(o.predicted for o in borderline),
        "per_case": [
            {
                "case_id": o.case_id,
                "resolved_verdict": o.resolved_verdict.value,
                "predicted": o.predicted,
                "rule_match": o.rule_match,
                "n_findings": len(o.findings),
            }
            for o in outcomes
        ],
    }
