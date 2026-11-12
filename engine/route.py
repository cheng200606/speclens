"""规则路由（M-lite 确定性版）：规则找代码，而非代码检索规则。

每条规则的 trigger.ast_cues 与代码文本做命中判断；无 cues 的规则视为全局适用。
M2 将升级为 AST 特征（tree-sitter）+ 章节级路由。
"""

from __future__ import annotations

from bench.harness.schemas import RuleRecord


def route_rules(rules: list[RuleRecord], code_text: str) -> list[RuleRecord]:
    """返回对该代码文本适用的规则子集。"""
    applicable: list[RuleRecord] = []
    for rule in rules:
        cues = rule.trigger.ast_cues
        if not cues or any(
            _cue_hit(cue, code_text) for cue in cues
        ):
            applicable.append(rule)
    return applicable


def _cue_hit(cue: str, code_text: str) -> bool:
    import re

    if cue == "use":
        return re.search(r"\buse\(", code_text) is not None
    return re.search(rf"\b{re.escape(cue)}\b", code_text, re.I) is not None
