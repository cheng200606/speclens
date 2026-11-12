"""文档解析（M-lite 确定性版）：规范快照 → 章节树。

M2 将升级为 LLM 辅助解析；当前实现纯确定性，可离线复现。
"""

from __future__ import annotations

import re
from pathlib import Path

from bench.harness.spec_text import assemble_spec_text

_HEADING = re.compile(r"^(#{2,4})\s+(.+)$", re.M)
_FILE_SPLIT = re.compile(r"^## Snapshot file: (.+?)$", re.M)


def parse_document(spec_dir: Path, max_chars: int = 200_000) -> list[dict]:
    """返回章节列表 [{source, section, text}]。

    先按「## Snapshot file:」分块定位来源文件，再在每个文件内按 markdown
    heading（##/###/####）切章节。
    """
    text, _ = assemble_spec_text(spec_dir, max_chars=max_chars)
    sections: list[dict] = []
    parts = _FILE_SPLIT.split(text)  # [前言, 文件名, 正文, 文件名, 正文, ...]
    for i in range(1, len(parts), 2):
        source = parts[i].strip()
        body = parts[i + 1]
        matches = list(_HEADING.finditer(body))
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
