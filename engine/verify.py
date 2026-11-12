"""规则验证三道关（plan.md §2.2，本项目方法核心）：

1. grounding：规则判定标准 <-> 规范原文 entailment 双向校验
2. executability：自动合成正/反例代码，管线自审，结论需自洽
3. conflict：同场景规则的等级/判定冲突检测

低分规则进入人工复核队列。
"""

from __future__ import annotations

from bench.harness.schemas import RuleRecord


def verify_rules(rules: list[RuleRecord], spec_text: str) -> list[RuleRecord]:
    """回填每条规则的 verification 字段。M2 实现。"""
    raise NotImplementedError("engine.verify 将在 M2 实现（plan.md §4）")
