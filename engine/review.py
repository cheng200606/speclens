"""分层审查执行：确定性层（AST/正则） -> LLM 对照层（规则+判定标准+正反例） -> 聚合去重。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding, RuleRecord


def review_code(
    case: Case, rules: list[RuleRecord], adapter: ModelAdapter
) -> list[Finding]:
    raise NotImplementedError("engine.review 将在 M2 实现（plan.md §4）")
