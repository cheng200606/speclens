"""逐规则对照审查（M-lite 版）：对每条适用规则 + 代码文件做一次 LLM 对照检查。

证据链输入（rule.assertion + source_span.quote）在 prompt 中给全；
聚合去重与证据链回填在 M2 完善。

I9①：`review_prompt: scoped-v2`（run_config 轴）启用范围纪律提示——离线诊断
（bench/tools/route_v4_diag.py）证明 matched 全局的 FP 在路由层不可削减
（缺控制型违规与无关文件词法不可分，三政策 × 4 规范量化），FP 杠杆移到
审查层：只审当前规则、不报引句里出现的需求 ID、rule_ids 用给定 ID。
**缺控制型违规不受约束**（主题整体缺席但恰好构成违规是 asvs 检出的主要
来源——「必须存在 X」被「没有 X」违反，任何「主题缺席即不报」的指令都会
直接砍检出，故 v2 只做范围纪律与软校准，不做缺席判定）。
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

_SCOPED_V2_EXTRA = (
    "\nDecide only whether this code violates the rule above as stated. "
    "Exactly one rule is under review: do not report other requirements "
    "(including requirement IDs that appear in the specification text), "
    "general style preferences, or improvements. "
    "Use the rule id given above verbatim in every finding's rule_ids. "
    "If the connection between the code and this rule is speculative, "
    "report no finding."
)

PROMPT_VARIANTS = ("v1", "scoped-v2")


def _prompt_variant(adapter: "ModelAdapter") -> str:
    cfg = getattr(adapter, "run_config", None) or {}
    value = cfg.get("review_prompt", "v1")
    if value not in PROMPT_VARIANTS:
        raise ValueError(f"配置中的 review_prompt 非法：{value!r}")
    return value


def _rule_prompt(rule: RuleRecord, code: str, variant: str = "v1") -> str:
    prompt = (
        f"Rule (level {rule.level}): {rule.assertion}\n"
        f"Specification text: \"{rule.source_span.quote}\"\n"
        f"Section: {rule.trigger.scenario}\n"
        f"\nDoes the following code violate this rule? "
        f'Report violations only.\n\n```tsx\n{code}\n```'
    )
    if variant == "scoped-v2":
        prompt += _SCOPED_V2_EXTRA
    return prompt


def check_code_against_rule(
    rule: RuleRecord, code: str, adapter: ModelAdapter, case_id: str | None = None
) -> list[Finding]:
    """单规则 × 单段代码的对照检查（verify 第二关自洽测试复用同一入口）。"""
    variant = _prompt_variant(adapter)
    out: FindingsOutput = adapter.complete_json(
        system=(
            "You are a code reviewer checking code against ONE explicit rule. "
            'Respond ONLY with JSON: {"findings": [...]} (same finding schema '
            "as before); empty findings when the rule is not violated."
        ),
        user=_rule_prompt(rule, code, variant),
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
