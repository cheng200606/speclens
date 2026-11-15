"""生成全库 synthetic/mined 案例的人工复核清单（I6，论文级门槛前置）。

从 meta.yaml 逐案例提取 claim（verdict / rule_ids / notes / 文件），按规范分组输出
Markdown 复选框清单到 docs/review-I6-origins.md。人工复核通过后把 origin 改为
handcrafted 并复跑本脚本核对清零。

用法：uv run python -m bench.tools.gen_review_checklist
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "bench" / "cases"
OUT = ROOT / "docs" / "review-I6-origins.md"

SPEC_LABEL = {
    "react19": "React 19（R-xxx）",
    "airbnb": "Airbnb JS（airbnb-NNN）",
    "agents-sdk": "OpenAI Agents SDK（agents-NNN）",
    "asvs": "OWASP ASVS 5.0（asvs-V*）",
}


def review_guide(spec: str, cid: str) -> str:
    return f"VS Code 打开 bench/cases/{spec}/{cid}/：先读 meta.yaml 的 claim，再逐条对照 code/ 与规则库引句。"


def main() -> None:
    lines = [
        "# I6 · 全库 synthetic/mined 案例人工复核清单",
        "",
        "生成：`uv run python -m bench.tools.gen_review_checklist`（勿手改本清单结构；",
        "复核结论写回各案例 meta.yaml：通过 → `origin: handcrafted`，标注 `reviewed_by`；",
        "不通过 → 修代码或改 claim 后保留 synthetic。全部清零后本清单应输出 0 待复核。）",
        "",
        "复核口径（与 I2 复核一致）：",
        "1. verdict 是否成立（violation 确有规范条文支撑；compliant 确无范围内违规）；",
        "2. rule_ids 是否是「最贴」的规则（不是沾边就挂）；",
        "3. 代码是否自洽可运行（无语法错/未定义符号）；",
        "4. 范围外真实模式不算违规（见 error taxonomy fp-off-scope-true-pattern 口径）。",
        "",
    ]
    pending = 0
    for spec in ("react19", "airbnb", "agents-sdk", "asvs"):
        rows = []
        for case_dir in sorted((CASES / spec).iterdir()):
            if not case_dir.is_dir():
                continue
            meta_path = case_dir / "meta.yaml"
            if not meta_path.exists():
                continue
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            origin = meta.get("origin", "handcrafted")
            if origin not in ("synthetic", "mined"):
                continue
            pending += 1
            files = meta.get("files", [])
            notes = ""
            for ann in meta.get("annotations", []):
                notes = ann.get("notes", "")
                break
            rows.append(
                f"- [ ] **{meta.get('case_id', case_dir.name)}** · "
                f"{meta.get('verdict')} · `{', '.join(meta.get('rule_ids', []))}` · "
                f"{meta.get('difficulty', '?')} · origin={origin} · "
                f"files: {', '.join(files)}\n"
                f"      - claim: {notes}\n"
                f"      - {review_guide(spec, case_dir.name)}"
            )
        lines.append(f"## {SPEC_LABEL[spec]}（{len(rows)} 待复核）")
        lines.append("")
        lines.extend(rows)
        lines.append("")
    lines.insert(11, f"**待复核总数：{pending}**（react19/airbnb/agents-sdk/asvs 分组见下）")
    lines.insert(12, "")
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({pending} pending)")


if __name__ == "__main__":
    main()
