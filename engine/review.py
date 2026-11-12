"""逐规则对照审查（M-lite 版）：对每条适用规则 + 代码文件做一次 LLM 对照检查。

证据链输入（rule.assertion + source_span.quote）在 prompt 中给全；
聚合去重与证据链回填在 M2 完善。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bench.harness.schemas import FindingsOutput
from engine.route import route_rules

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding, RuleRecord

MAX_RULES_PER_FILE = 25


def _rule_prompt(rule: RuleRecord, code: str) -> str:
    return (
        f"Rule (level {rule.level}): {rule.assertion}\n"
        f"Specification text: \"{rule.source_span.quote}\"\n"
        f"Section: {rule.trigger.scenario}\n"
        f"\nDoes the following code violate this rule? "
        f'Report violations only.\n\n```tsx\n{code}\n```'
    )


def check_code_against_rule(
    rule: RuleRecord, code: str, adapter: ModelAdapter, case_id: str | None = None
) -> list[Finding]:
    """单规则 × 单段代码的对照检查（verify 第二关自洽测试复用同一入口）。"""
    out: FindingsOutput = adapter.complete_json(
        system=(
            "You are a code reviewer checking code against ONE explicit rule. "
            'Respond ONLY with JSON: {"findings": [...]} (same finding schema '
            "as before); empty findings when the rule is not violated."
        ),
        user=_rule_prompt(rule, code),
        schema=FindingsOutput,
        meta={
            "case_id": case_id,
            "rule_id": rule.id,
            "level": rule.level,
            "phase": "review",
            "code_head": code[:200],  # 供测试/自适应 adapter 判别输入
        },
    )
    for f in out.findings:
        if case_id:
            f.case_id = case_id
        if rule.id not in f.rule_ids:
            f.rule_ids = [rule.id, *f.rule_ids]
    return out.findings


def review_code(
    case: Case, rules: list[RuleRecord], adapter: ModelAdapter
) -> list[Finding]:
    findings: list[Finding] = []
    for name in case.meta.files:
        code = case.read_file(name)
        applicable = route_rules(rules, code)[:MAX_RULES_PER_FILE]
        for rule in applicable:
            findings.extend(
                check_code_against_rule(rule, code, adapter, case_id=case.meta.case_id)
            )
    return findings
