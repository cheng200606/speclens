"""文档解析（M-lite 确定性版）：规范快照 → 章节树。

M2 将升级为 LLM 辅助解析；当前实现纯确定性，可离线复现。

I7：非 markdown 来源（ASVS 类 CSV→文本）没有 heading，此前整文件被静默丢弃
（asvs 只剩 README 的 5.7K 字符可提取 → 2 条垃圾规则）。现在 CSV 转写块按
「ReqID (Lx): desc」行识别，并按 ReqID 的章节前缀（如 V6.2）分组为章节。
"""

from __future__ import annotations

import re
from pathlib import Path

from bench.harness.spec_text import assemble_spec_text

_HEADING = re.compile(r"^(#{2,4})\s+(.+)$", re.M)
_FILE_SPLIT = re.compile(r"^## Snapshot file: (.+?)$", re.M)
_CSV_REQ_LINE = re.compile(r"^([A-Za-z]?[\d.]+[.\w-]*)\s*\(L\d+\):\s*(.+)$", re.M)
_REQ_CHAPTER = re.compile(r"^(V[\d.]+|\d+(?:\.\d+)*)")


def _csv_sections(body: str) -> list[dict]:
    """CSV 转写文本（无 heading）→ 按需求行识别并按章节前缀分组。"""
    sections: list[dict] = []
    matches = list(_CSV_REQ_LINE.finditer(body))
    if not matches:
        return sections
    groups: dict[str, list[str]] = {}
    order: list[str] = []
    for m in matches:
        req_id, desc = m.group(1), m.group(2).strip()
        cm = _REQ_CHAPTER.match(req_id)
        chapter = cm.group(1) if cm else "MISC"
        if chapter not in groups:
            groups[chapter] = []
            order.append(chapter)
        groups[chapter].append(f"{req_id}: {desc}")
    for chapter in order:
        text = "\n".join(groups[chapter])
        if len(text) < 40:
            continue
        sections.append(
            {"source": "csv", "section": f"Requirements {chapter}", "text": text}
        )
    return sections


def parse_document(spec_dir: Path, max_chars: int = 200_000) -> list[dict]:
    """返回章节列表 [{source, section, text}]。

    先按「## Snapshot file:」分块定位来源文件，再在每个文件内按 markdown
    heading（##/###/####）切章节；无 heading 的 CSV 转写块按需求行分组
    （I7，见模块 docstring）。
    """
    text, _ = assemble_spec_text(spec_dir, max_chars=max_chars)
    sections: list[dict] = []
    parts = _FILE_SPLIT.split(text)  # [前言, 文件名, 正文, 文件名, 正文, ...]
    for i in range(1, len(parts), 2):
        source = parts[i].strip()
        body = parts[i + 1]
        matches = list(_HEADING.finditer(body))
        if not matches:
            sections.extend(_csv_sections(body))
            continue
        for j, m in enumerate(matches):
            end = matches[j + 1].start() if j + 1 < len(matches) else len(body)
            content = body[m.end() : end].strip()
            if len(content) < 40:  # 过短的纯目录块跳过
                continue
            sections.append(
                {
                    "source": source,
                    "section": m.group(2).strip(),
                    "text": content,
                }
            )
    return sections
