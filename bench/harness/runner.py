"""实验 runner（plan.md §3.4）。

每个实验一个 config.yaml，结果按「run 名 + 配置哈希」归档到
experiments/runs/<run_name>-<hash>/，禁止覆盖已有 run。

用法：
    uv run python -m bench.harness.runner --config experiments/configs/smoke-b0.yaml
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import yaml

from baselines import get_baseline
from bench.harness.loader import Case, load_cases
from bench.harness.metrics import CaseOutcome, compute_metrics
from bench.harness.model_adapter import make_adapter
from bench.harness.schemas import Difficulty, Finding, Verdict


def config_hash(config: dict) -> str:
    payload = json.dumps(config, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def build_mock_expected(
    cases: list[Case], only_easy: bool = False
) -> dict[str, list[dict]]:
    """由标注构造 mock 适配器的期望输出（仅用于离线冒烟，不参与真实评测）。"""
    expected: dict[str, list[dict]] = {}
    for case in cases:
        if case.meta.resolved.verdict != Verdict.VIOLATION:
            continue
        if only_easy and case.meta.difficulty != Difficulty.EASY:
            continue
        file = case.meta.files[0] if case.meta.files else "code/component.tsx"
        expected[case.meta.case_id] = [
            {
                # difficulty 仅作为 mock 适配器的过滤元数据，Finding schema 会忽略
                "difficulty": case.meta.difficulty.value,
                "file": file,
                "line_start": 1,
                "line_end": 1,
                "rule_ids": case.meta.resolved.rule_ids,
                "severity": "error",
                "message": f"mock violation of {case.meta.resolved.rule_ids}",
                "evidence": {"rule_quote": "", "explanation": "mock"},
            }
        ]
    return expected


def run(config: dict, repo_root: Path) -> Path:
    cases = load_cases(repo_root / config["cases_dir"])

    model_spec = config.get("model", "mock-perfect")
    expected = None
    if model_spec.startswith("mock"):
        expected = build_mock_expected(cases, only_easy=model_spec == "mock-imperfect")
    adapter = make_adapter(model_spec, expected)

    baseline = get_baseline(config["baseline"])

    run_dir = (
        repo_root
        / config.get("output_dir", "experiments/runs")
        / f"{config.get('run_name', 'run')}-{config_hash(config)}"
    )
    if run_dir.exists():
        raise RuntimeError(f"run 已存在，禁止覆盖（plan.md §3.4）：{run_dir}")
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "config.resolved.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=True), encoding="utf-8"
    )

    outcomes: list[CaseOutcome] = []
    with (run_dir / "results.jsonl").open("w", encoding="utf-8") as results_file:
        for case in cases:
            findings: list[Finding] = baseline.predict_case(case, adapter)
            for f in findings:
                f.case_id = case.meta.case_id
            (run_dir / "raw" / f"{case.meta.case_id}.json").write_text(
                json.dumps(
                    [f.model_dump() for f in findings], ensure_ascii=False, indent=2
                ),
                encoding="utf-8",
            )
            outcomes.append(
                CaseOutcome(
                    case_id=case.meta.case_id,
                    resolved_verdict=case.meta.resolved.verdict,
                    annotated_rule_ids=case.meta.resolved.rule_ids,
                    findings=findings,
                )
            )
            results_file.write(
                json.dumps(
                    {
                        "case_id": case.meta.case_id,
                        "resolved_verdict": case.meta.resolved.verdict.value,
                        "predicted": case_outcome_bool(findings),
                        "findings": [f.model_dump() for f in findings],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    summary = compute_metrics(outcomes)
    summary.update(
        {
            "run_name": config.get("run_name", "run"),
            "baseline": config["baseline"],
            "model": model_spec,
            "created": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }
    )
    (run_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return run_dir


def case_outcome_bool(findings: list[Finding]) -> bool:
    return len(findings) > 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SpecLens 实验 runner")
    parser.add_argument("--config", required=True, help="实验配置 YAML 路径")
    parser.add_argument("--repo-root", default=None, help="仓库根目录（默认当前目录）")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    run_dir = run(config, repo_root)

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    printable = {k: v for k, v in summary.items() if k != "per_case"}
    print(f"[speclens] run completed -> {run_dir}")
    print(json.dumps(printable, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
