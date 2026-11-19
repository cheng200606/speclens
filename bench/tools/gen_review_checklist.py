"""生成全库 synthetic/mined/ai-reviewed 案例的人工复核清单（I6 起，I9 修订）。

从 meta.yaml 逐案例提取 claim（verdict / rule_ids / notes / 文件），按规范分组输出
Markdown 复选框清单到 docs/review-I6-origins.md。

待复核口径（I9）：三类案例需要**真人**签核——
- ``synthetic``：AI 起草、尚无任何复核；
- ``mined``：真实仓库挖掘、尚无人工复核；
- ``ai-reviewed``：AI 起草并经「AI 代人工」复核（I9 前被误标为 handcrafted），
  仍缺真人签核，故留在清单内；
通过后把 origin 改为 ``handcrafted`` 并写 ``reviewed_by``（签名），
复跑本脚本核对清零。

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

# 仍需真人签核的来源（I9：ai-reviewed = AI 起草 + AI 代复核，缺真人签核）
PENDING_ORIGINS = ("synthetic", "mined", "ai-reviewed")

# 复核重点随来源不同：已 AI 代复核的案例请重点看「AI 复核是否与规范原文一致」
ORIGIN_HINT = {
    "synthetic": "AI 起草，无任何复核——请逐条对照规范原文裁定。",
    "mined": "取自真实仓库修复提交——请核对 claim 与修复前的代码事实。",
    "ai-reviewed": "AI 起草并经 AI 代复核（未经真人签核）——请重点核对复核结论本身。",
}


def review_guide(spec: str, cid: str) -> str:
    return f"VS Code 打开 bench/cases/{spec}/{cid}/：先读 meta.yaml 的 claim，再逐条对照 code/ 与规则库引句。"


def main() -> None:
    lines = [
        "# I6 · 全库 synthetic/mined/ai-reviewed 案例人工复核清单",
        "",
        "生成：`uv run python -m bench.tools.gen_review_checklist`（勿手改本清单结构；",
        "复核结论写回各案例 meta.yaml：通过 → `origin: handcrafted` 并写 `reviewed_by`（签名）；",
        "不通过 → 修代码或改 claim 后保留原 origin。全部清零后本清单应输出 0 待复核。）",
        "",
        "复核口径（与 I2 复核一致）：",
        "1. verdict 是否成立（violation 确有规范条文支撑；compliant 确无范围内违规）；",
        "2. rule_ids 是否是「最贴」的规则（不是沾边就挂）；",
        "3. 代码是否自洽可运行（无语法错/未定义符号）；",
        "4. 范围外真实模式不算违规（见 error taxonomy fp-off-scope-true-pattern 口径）。",
        "",
        "> `ai-reviewed` 一档（I9 新增）：案例由 AI 起草并经「AI 代人工」复核，**尚未取得",
        "> 真人签核**，因此仍列在本清单内待复核——与 `handcrafted`（人工撰写且人工复核）",
        "> 不同档，勿直接采信。详见 `docs/LIMITATIONS.md` §2。",
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
            if origin not in PENDING_ORIGINS:
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
                f"      - 复核重点：{ORIGIN_HINT.get(origin, '')}\n"
                f"      - {review_guide(spec, case_dir.name)}"
            )
        lines.append(f"## {SPEC_LABEL[spec]}（{len(rows)} 待复核）")
        lines.append("")
        lines.extend(rows)
        lines.append("")
    # 待复核总数放在「复核口径」段之后、引言说明之前——用锚点定位而非行号
    # （行号会随说明段长度漂移，曾把计数插进引言中间）。
    anchor = "> `ai-reviewed` 一档（I9 新增）"
    idx = next(i for i, line in enumerate(lines) if line.startswith(anchor))
    lines.insert(idx, f"**待复核总数：{pending}**（react19/airbnb/agents-sdk/asvs 分组见下）")
    lines.insert(idx + 1, "")
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({pending} pending)")


if __name__ == "__main__":
    main()
