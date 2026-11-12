"""规则路由：每条规则声明适用特征（trigger.scenario + ast_cues），

对代码库批量扫描「哪些文件/符号适用该规则」——规则找代码，而非代码检索规则。
这是与 RAG 式方案的本质差异（漏检由规则覆盖决定，不由检索命中决定）。
"""

from __future__ import annotations

from bench.harness.schemas import RuleRecord


def route_rules(rules: list[RuleRecord], repo_dir: str) -> dict[str, list[str]]:
    """返回 {rule_id: [适用文件路径]}。M2 实现。"""
    raise NotImplementedError("engine.route 将在 M2 实现（plan.md §4）")
