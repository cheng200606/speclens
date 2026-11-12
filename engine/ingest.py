"""文档解析：规范网页/Markdown -> 章节树 -> 候选规则句筛选（MUST/禁止等）。"""

from __future__ import annotations

from pathlib import Path


def parse_document(path: Path) -> list[dict]:
    """返回章节树：[{section, text, source_span}]。M2 实现。"""
    raise NotImplementedError("engine.ingest 将在 M2 实现（plan.md §4）")
