"""证据链构建：finding -> rule_id -> 规范原文 span -> 代码行，输出可审计报告。"""

from __future__ import annotations

from bench.harness.schemas import Finding, RuleRecord


def attach_evidence(
    findings: list[Finding], rules: list[RuleRecord]
) -> list[Finding]:
    """回填 evidence.rule_quote / explanation。M2 实现。"""
    raise NotImplementedError("engine.trace 将在 M2 实现（plan.md §4）")
