"""生死实验报告生成器（plan.md §2.4）。

从 experiments/runs/ 下按前缀、baseline 与（可选）模型定位最新 run，
汇总总体指标并做两两配对 McNemar（含分组检验），输出 Markdown 报告。

I1 修订（docs/STATUS-I1.md P1-1）：
- 任一 run 使用 mock-* 适配器 → 报告标记 `NON-SCIENTIFIC`，**不给出 Go/No-Go 判读**，
  避免把「四个 1.0」误读成方法已验证；判读标准仍列出，但注明仅适用于真实模型。
- 新增按 violation / compliant 分组的配对检验，对应 §2.4 的两条独立判据。
- 支持 `--model` 过滤，避免多模型 / 多次运行的 run 被 mtime 混选。

用法：
    uv run python -m experiments.make_report --runs experiments/runs --prefix litmus
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

import yaml

from bench.harness.model_adapter import is_mock_model
from bench.harness.stats import mcnemar_between_runs, mcnemar_subsets

_ENTRIES = [
    ("B0", "b0_zero_shot"),
    ("B1", "b1_full_spec"),
    ("M-lite", "m_lite"),
    ("M-verified", "m_verified"),
]
_SUBSET_LABELS = {"all": "全部", "violation": "仅违规(检出)", "compliant": "仅合规(误报)"}


def _latest_run(
    runs_dir: Path, baseline_id: str, prefix: str, model: str | None = None
) -> Path | None:
    best: Path | None = None
    for d in runs_dir.glob(f"{prefix}-*"):
        cfg_path = d / "config.resolved.yaml"
        if not cfg_path.exists():
            continue
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        if cfg.get("baseline") != baseline_id:
            continue
        if model is not None and cfg.get("model") != model:
            continue
        if best is None or d.stat().st_mtime > best.stat().st_mtime:
            best = d
    return best


def make_report(
    runs_dir: Path,
    output: Path,
    prefix: str = "litmus",
    model: str | None = None,
) -> Path:
    found = {
        label: _latest_run(runs_dir, bid, prefix, model)
        for label, bid in _ENTRIES
    }
    found = {k: v for k, v in found.items() if v is not None}
    if not found:
        raise SystemExit(f"runs 目录中没有前缀为 {prefix!r} 的 run：{runs_dir}")

    summaries = {
        label: json.loads((d / "summary.json").read_text(encoding="utf-8"))
        for label, d in found.items()
    }
    # B3 静态检查是确定性基线（不调用 LLM），mock adapter 仅作接口占位，
    # 其指标有科学意义（docs/STATUS-I4.md）。
    mock_runs = [
        label
        for label, s in summaries.items()
        if is_mock_model(s.get("model", "")) and s.get("baseline") != "b3_static"
    ]
    scientific = not mock_runs

    lines = [
        "# 生死实验报告（Litmus Experiment）",
        "",
        f"- 生成时间：{_dt.datetime.now(_dt.timezone.utc).isoformat()}",
        f"- runs 目录：`{runs_dir}`（前缀 `{prefix}`，模型过滤 `{model or '不过滤'}`）",
        "",
    ]
    if scientific:
        lines += ["**STATUS: SCIENTIFIC（真实模型运行）**", ""]
    else:
        lines += [
            "**STATUS: NON-SCIENTIFIC（mock adapter，指标无科学意义）**",
            "",
            f"> ⚠️ 以下配置的模型为确定性 mock：{', '.join(mock_runs)}。",
            "> 本报告**不给出 Go/No-Go 判读**；所有数值只用于验证评测链路的机械正确性。",
            "> 真实运行请把 config 中的 `model` 换成 litellm 模型串后重跑全部配置。",
            "",
        ]
    lines += [
        "> 说明：`model` 为 mock-* 时报告仅验证机械流程，指标不可写入论文；",
        "> 判读标准（§3）只在全部配置为真实模型时适用。",
        "",
        "## 1. 配置与总体指标",
        "",
        "| 配置 | baseline | 模型 | n_cases | 检出率 | 误报率 | 规则命中率 |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, s in summaries.items():
        lines.append(
            f"| {label} | {s['baseline']} | {s['model']} | {s['n_cases']} "
            f"| {s['detection_rate']} | {s['false_positive_rate']} "
            f"| {s['rule_match_rate']} |"
        )

    lines += [
        "",
        "## 2. 两两配对 McNemar（精确二项，borderline 不计）",
        "",
        "| 对比 | 配对 n | A对B错 | A错B对 | p |",
        "|---|---|---|---|---|",
    ]
    labels = list(found)
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            st = mcnemar_between_runs(found[labels[i]], found[labels[j]])
            lines.append(
                f"| {labels[i]} vs {labels[j]} | {st['n_paired']} "
                f"| {st['b_a_right_b_wrong']} | {st['c_a_wrong_b_right']} "
                f"| {st['p_mcnemar_exact']} |"
            )

    lines += [
        "",
        "## 2b. 分组配对检验（§2.4 的检出与误报是两条独立判据）",
        "",
        "| 对比 | 子集 | 配对 n | A对B错 | A错B对 | p |",
        "|---|---|---|---|---|---|",
    ]
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            subsets = mcnemar_subsets(found[labels[i]], found[labels[j]])
            for key in ("violation", "compliant"):
                st = subsets[key]
                lines.append(
                    f"| {labels[i]} vs {labels[j]} | {_SUBSET_LABELS[key]} "
                    f"| {st['n_paired']} | {st['b_a_right_b_wrong']} "
                    f"| {st['c_a_wrong_b_right']} | {st['p_mcnemar_exact']} |"
                )

    lines += [
        "",
        "## 3. 判读标准（plan.md §2.4；仅适用于真实模型运行）",
        "",
        "- **Go（方法）**：M-lite 显著优于 B1（检出 +10pp 或误报 −20%，McNemar p<0.1）→ 扩全量",
        "- **Go（规模/成本）**：B1 ≈ M-lite 但 B1 成本/上下文爆表 → 主打 RQ4",
        "- **No-Go（方法）**：B1 全面占优且无成本劣势 → 转 RQ1+RQ3 measurement study",
        "",
    ]
    if not scientific:
        lines += [
            "**本次判读：不出具**（存在 mock 运行）。",
            "",
        ]

    lines += ["## 4. 复现信息（run 产物）", ""]
    for label, s in summaries.items():
        lines.append(
            f"- {label}: `{found[label]}` · code_digest=`{s.get('code_digest', 'n/a')}` "
            f"· temperature={s.get('temperature', 'n/a')} "
            f"· run_index={s.get('run_index', 'n/a')} "
            f"· n_llm_calls={s.get('n_llm_calls', 'n/a')} "
            f"· total_tokens={s.get('total_tokens', 'n/a')}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SpecLens 生死实验报告")
    parser.add_argument("--runs", default="experiments/runs")
    parser.add_argument("--output", default=None, help="报告输出路径（默认 experiments/reports/litmus-<date>.md）")
    parser.add_argument("--prefix", default="litmus")
    parser.add_argument("--model", default=None, help="只汇总该模型的 run，避免混用")
    args = parser.parse_args(argv)

    runs_dir = Path(args.runs)
    if args.output:
        output = Path(args.output)
    else:
        today = _dt.date.today().isoformat()
        output = Path("experiments/reports") / f"litmus-{today}.md"
    path = make_report(runs_dir, output, args.prefix, args.model)
    print(f"[speclens] litmus report -> {path}")


if __name__ == "__main__":
    main()
