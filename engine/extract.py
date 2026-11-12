"""规则结构化合成：候选规则句 -> RuleRecord（触发条件 / 判定标准 / 正反例 / 溯源）。"""

from __future__ import annotations

from bench.harness.schemas import RuleRecord


def extract_rules(markdown_text: str, spec_id: str) -> list[RuleRecord]:
    raise NotImplementedError("engine.extract 将在 M2 实现（plan.md §4）")
