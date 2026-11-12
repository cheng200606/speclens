"""证据链回填与审查结果聚合（plan.md §2.2 / §3.3）。

证据链：finding -> rule_id -> 规范原文 quote -> 代码行。
- attach_evidence：用规则库回填 finding.evidence（不覆盖已有非空值）。
- deduplicate：精确去重（同文件/行/规则/消息）+ 同文件同规则集合的重叠行合并。
- aggregate：attach_evidence + deduplicate + 按文件/行号/严重度排序的最终报告。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bench.harness.schemas import Finding, RuleRecord

if TYPE_CHECKING:  # pragma: no cover
    pass

_SEVERITY_RANK = {"info": 1, "warning": 2, "error": 3}
_LINE_GAP = 2  # 行距 ≤2 视为重叠合并窗口


def attach_evidence(findings: list[Finding], rules: list[RuleRecord]) -> list[Finding]:
    """按 rule_id 查规则库，回填证据链（已有非空值不覆盖）。未知规则跳过。"""
    by_id = {r.id: r for r in rules}
    for f in findings:
        for rid in f.rule_ids:
            rule = by_id.get(rid)
            if rule is None:
                continue
            if not f.evidence.rule_quote:
                f.evidence.rule_quote = rule.source_span.quote
            if not f.evidence.explanation:
                f.evidence.explanation = (
                    f"Violates [{rule.id}] (level {rule.level}, "
                    f"section: {rule.trigger.scenario}): {rule.assertion}"
                )
            break  # 首个命中规则作为主证据
    return findings


def _overlaps(a: tuple[int, int], b: tuple[int, int], gap: int = _LINE_GAP) -> bool:
    return a[0] <= b[1] + gap and b[0] <= a[1] + gap


def deduplicate(findings: list[Finding]) -> list[Finding]:
    """精确去重 + 同文件同规则集合的重叠行合并（保留最高严重度的代表）。"""
    # 1) 精确去重
    seen: set[tuple] = set()
    unique: list[Finding] = []
    for f in findings:
        key = (f.file, f.line_start, f.line_end, frozenset(f.rule_ids), f.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)

    # 2) 同 (file, rule_ids) 桶内按行合并重叠区间
    buckets: dict[tuple[str, frozenset], list[Finding]] = {}
    for f in unique:
        buckets.setdefault((f.file, frozenset(f.rule_ids)), []).append(f)

    merged: list[Finding] = []
    for (_file, _rids), group in buckets.items():
        group.sort(key=lambda f: (f.line_start, f.line_end))
        current = group[0]
        for f in group[1:]:
            if _overlaps((current.line_start, current.line_end), (f.line_start, f.line_end)):
                current.line_start = min(current.line_start, f.line_start)
                current.line_end = max(current.line_end, f.line_end)
                if _SEVERITY_RANK[f.severity] > _SEVERITY_RANK[current.severity]:
                    current.severity = f.severity
                    current.message = f.message
                    current.evidence = f.evidence
                # 合并双方 rule_ids 的并集（保序）
                for rid in f.rule_ids:
                    if rid not in current.rule_ids:
                        current.rule_ids.append(rid)
            else:
                merged.append(current)
                current = f
        merged.append(current)
    return merged


def aggregate(findings: list[Finding], rules: list[RuleRecord]) -> list[Finding]:
    """完整聚合管线：证据链回填 → 去重 → 排序（文件/行号/严重度降序）。"""
    evidenced = attach_evidence(findings, rules)
    deduped = deduplicate(evidenced)
    return sorted(
        deduped,
        key=lambda f: (f.file, f.line_start, -_SEVERITY_RANK[f.severity]),
    )
