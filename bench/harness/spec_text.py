"""规范全文文本拼装（B1 全文注入与 M-lite 提取的共同输入）。

按 snapshot/manifest.yaml 的顺序拼接快照文件，做轻度清洗并限制总长度。
CSV 快照（如 ASVS）转为「ReqID (Lx): description」行。
"""

from __future__ import annotations

import csv
import io
import re
from functools import lru_cache
from pathlib import Path

import yaml

from bench.harness.loader import Case, load_spec

_CACHE: dict[tuple[str, int], tuple[str, list[str]]] = {}


def load_snapshot_files(spec_dir: Path) -> list[Path]:
    """按 manifest.yaml 声明的顺序返回快照文件（缺文件时跳过）。"""
    manifest_path = spec_dir / "snapshot" / "manifest.yaml"
    if not manifest_path.exists():
        return []
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    files: list[Path] = []
    for entry in manifest.get("files", []):
        p = spec_dir / "snapshot" / entry["file"]
        if p.exists():
            files.append(p)
    return files


def clean_react_md(text: str) -> str:
    """react.dev 导出 md 含站点组件标签；剥离 frontmatter 与包装标签，保留正文与代码块。"""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    for tag in (
        "Intro",
        "InlineToc",
        "Recipes",
        "DeepDive",
        "Note",
        "YouWillLearn",
        "ConsoleBlock",
        "Pitfall",
    ):
        text = re.sub(rf"</?{tag}>", "", text)
    text = re.sub(r"\{/\*.*?\*/\}", "", text)
    return text.strip()


def csv_to_text(path: Path) -> str:
    """ASVS 类 CSV 快照 → 每行一条「ReqID (Lx): description」。"""
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    lines = []
    for r in rows:
        req_id = r.get("req_id", "")
        desc = r.get("req_description", "").replace("\n", " ")
        lines.append(f"{req_id} (L{r.get('L', '?')}): {desc}")
    return "\n".join(lines)


def assemble_spec_text(
    spec_dir: Path, max_chars: int | None = None
) -> tuple[str, list[str]]:
    """返回 (规范全文文本, 实际纳入的文件名列表)。

    max_chars=None 表示**不截断**（默认）。此前默认 200_000 会静默丢弃超限
    快照文件，使 B1 全文基线看不到完整规范，破坏控制变量（见 docs/STATUS-I1.md S0-3）。
    需要复现「长上下文受限」场景时显式传入 max_chars，并通过
    snapshot_selection() 把被丢弃的文件写入 run 产物。
    """
    spec = load_spec(spec_dir)
    parts: list[str] = []
    used: list[str] = []
    total = 0
    for p in load_snapshot_files(spec_dir):
        if p.suffix == ".csv":
            body = csv_to_text(p)
        else:
            body = p.read_text(encoding="utf-8")
            if spec.spec_id == "react19":
                body = clean_react_md(body)
        if max_chars is not None and total + len(body) > max_chars:
            continue
        parts.append(f"## Snapshot file: {p.name}\n\n{body}")
        used.append(p.name)
        total += len(body)
    header = (
        f"# Specification: {spec.name} (version {spec.version or 'n/a'}), "
        f"license {spec.license}\n\n"
    )
    return header + "\n\n".join(parts), used


def snapshot_selection(spec_dir: Path, max_chars: int | None = None) -> dict:
    """返回快照文件纳入/省略情况，供 runner 写入 run 产物（可审计对照公平性）。"""
    all_files = [p.name for p in load_snapshot_files(spec_dir)]
    _text, used = get_spec_text(spec_dir, max_chars)
    omitted = [f for f in all_files if f not in used]
    return {
        "spec_id": load_spec(spec_dir).spec_id,
        "max_chars": max_chars,
        "files_used": used,
        "files_omitted": omitted,
        "n_files_total": len(all_files),
        "n_files_used": len(used),
        "included_chars": len(_text),
        "truncated": bool(omitted),
    }


def get_spec_text(spec_dir: Path, max_chars: int | None = None) -> tuple[str, list[str]]:
    """带进程内缓存的 assemble_spec_text（B1 逐 case 复用，避免重复读盘）。"""
    key = (str(spec_dir.resolve()), max_chars)
    if key not in _CACHE:
        _CACHE[key] = assemble_spec_text(spec_dir, max_chars)
    return _CACHE[key]


def spec_text_for_case(
    case: Case, max_chars: int | None = None
) -> tuple[str, list[str]]:
    """由 case 路径定位其规范目录（bench/cases/<spec>/<ID> → bench/specs/<spec>）。"""
    spec_dir = spec_dir = case.spec_dir()
    return get_spec_text(spec_dir, max_chars)
