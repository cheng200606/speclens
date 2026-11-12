"""生死实验报告生成器（plan.md §2.4）。

从 experiments/runs/ 下按前缀与 baseline 字段定位最新 run，
汇总总体指标并做两两配对 McNemar，输出 Markdown 报告。

用法：
    uv run python -m experiments.make_report --runs experiments/runs --prefix litmus
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

import yaml

from bench.harness.stats import mcnemar_between_runs

_ENTRIES = [("B0", "b0_zero_shot"), ("B1", "b1_full_spec"), ("M-lite", "m_lite")]


def _latest_run(runs_dir: Path, baseline_id: str, prefix: str) -> Path | None:
    best: Path | None = None
    for d in runs_dir.glob(f"{prefix}-*"):
        cfg_path = d / "config.resolved.yaml"
        if not cfg_path.exists():
            continue
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        if cfg.get("baseline") != baseline_id:
            continue
        if best is None or d.stat().st_mtime > best.stat().st_mtime:
            best = d
    return best


def make_report(runs_dir: Path, output: Path, prefix: str = "litmus") -> Path:
    found = {label: _latest_run(runs_dir, bid, prefix) for label, bid in _ENTRIES}
    found = {k: v for k, v in found.items() if v is not None}
    if not found:
        raise SystemExit(f"runs 目录中没有前缀为 {prefix!r} 的 run：{runs_dir}")

    lines = [
        "# 生死实验报告（Litmus Experiment）",
        "",
        f"- 生成时间：{_dt.datetime.now(_dt.timezone.utc).isoformat()}",
        f"- runs 目录：`{runs_dir}`（前缀 `{prefix}`）",
        "",
        "> ⚠️ 若 model 为 mock-*，本报告仅验证机械流程，指标无科学意义；",
        "> 真实运行请将 configs 中 model 换成 litellm 模型串后重跑三个配置。",
        "",
        "## 1. 配置与总体指标",
        "",
        "| 配置 | baseline | 模型 | n_cases | 检出率 | 误报率 | 规则命中率 |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, d in found.items():
        s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
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
        "## 3. 判读标准（plan.md §2.4）",
        "",
        "- **Go（方法）**：M-lite 显著优于 B1（检出 +10pp 或误报 −20%，McNemar p<0.1）→ 扩全量",
        "- **Go（规模/成本）**：B1 ≈ M-lite 但 B1 成本/上下文爆表 → 主打 RQ4",
        "- **No-Go（方法）**：B1 全面占优且无成本劣势 → 转 RQ1+RQ3 measurement study",
        "",
        "## 4. 附：run 目录",
        "",
    ]
    for label, d in found.items():
        lines.append(f"- {label}: `{d}`")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SpecLens 生死实验报告")
    parser.add_argument("--runs", default="experiments/runs")
    parser.add_argument("--output", default=None, help="报告输出路径（默认 experiments/reports/litmus-<date>.md）")
    parser.add_argument("--prefix", default="litmus")
    args = parser.parse_args(argv)

    runs_dir = Path(args.runs)
    if args.output:
        output = Path(args.output)
    else:
        today = _dt.date.today().isoformat()
        output = Path("experiments/reports") / f"litmus-{today}.md"
    path = make_report(runs_dir, output, args.prefix)
    print(f"[speclens] litmus report -> {path}")


if __name__ == "__main__":
    main()
