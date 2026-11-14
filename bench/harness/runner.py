"""实验 runner（plan.md §3.4）。

每个实验一个 config.yaml，结果按「run 名 + 配置/代码哈希」归档到
experiments/runs/<run_name>-<hash>/，禁止覆盖已有 run。

I1 修订（docs/STATUS-I1.md P0-2 / P0-4）：
- `code_digest()` 把影响结果的源码与规范元数据纳入归档哈希：改代码后同配置
  不再撞目录，产物自证「这次结果是哪版代码跑出来的」。
- `temperature` / `run_index` 写入 resolved 配置并真正透传给适配器；
  `spec_max_chars` / `rules_source` 通过 `run_config` 注入，供基线可选读取。
- 记录 token / 时延 / 调用数到 `usage.json` 与 summary（支撑 §1.3 成本与 RQ4）。
- 写入 `rules_diagnostic.json`（规则来源、引句逐字校验、对齐覆盖率）与
  `spec_selection.json`（B1 纳入/省略的快照文件），使对照公平性可审计。

用法：
    uv run python -m bench.harness.runner --config experiments/configs/smoke-b0.yaml
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

import yaml

from baselines import get_baseline
from bench.harness.loader import Case, load_cases
from bench.harness.metrics import CaseOutcome, compute_metrics
from bench.harness.model_adapter import make_adapter
from bench.harness.schemas import Difficulty, Finding, Verdict
from bench.harness.spec_text import snapshot_selection

# 影响实验结果的文件；纳入 code_digest 以保证「同配置不同代码」得到不同 run 目录
_DIGEST_GLOBS = (
    "bench/harness/*.py",
    "baselines/*.py",
    "engine/*.py",
    "bench/specs/*/spec.yaml",
    "bench/specs/*/rules.yaml",
    "bench/specs/*/snapshot/manifest.yaml",
)


def config_hash(config: dict) -> str:
    payload = json.dumps(config, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def code_digest(repo_root: Path) -> str:
    """哈希所有影响实验结果的源码与规范元数据（不依赖 git，clone 即可复现）。"""
    h = hashlib.sha256()
    files: list[Path] = []
    for pattern in _DIGEST_GLOBS:
        files.extend(sorted(repo_root.glob(pattern)))
    for p in files:
        h.update(str(p.relative_to(repo_root)).replace("\\", "/").encode("utf-8"))
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


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


def build_scripted_script(cases: list[Case]) -> dict:
    """构造带已知误差模式的脚本（仅供 MockScriptedAdapter 验证评测管线）。"""
    compliant_ids = [
        c.meta.case_id
        for c in cases
        if c.meta.resolved.verdict == Verdict.COMPLIANT
    ]
    fp_case = compliant_ids[0] if compliant_ids else None
    script: dict = {}
    for case in cases:
        cid = case.meta.case_id
        detected = (
            case.meta.resolved.verdict == Verdict.VIOLATION
            and case.meta.difficulty != Difficulty.HARD
        )
        if cid == fp_case:
            detected = True  # 固定 1 个误报
        script[cid] = {
            "detected": detected,
            "rule_ids": case.meta.resolved.rule_ids,
            "file": case.meta.files[0] if case.meta.files else "code/x.tsx",
        }
    return script


def _spec_dir(repo_root: Path, config: dict) -> Path:
    spec_id = Path(config["cases_dir"]).name
    return repo_root / "bench" / "specs" / spec_id


def run(config: dict, repo_root: Path) -> Path:
    cases = load_cases(repo_root / config["cases_dir"])

    # 1) 解析配置：补齐默认值，纳入代码版本
    resolved = dict(config)
    resolved.setdefault("temperature", 0.0)
    resolved.setdefault("run_index", 0)
    resolved["code_digest"] = code_digest(repo_root)

    model_spec = resolved.get("model", "mock-perfect")
    expected = None
    script = None
    if model_spec == "mock-scripted":
        script = build_scripted_script(cases)
    elif model_spec.startswith("mock"):
        expected = build_mock_expected(
            cases, only_easy=model_spec == "mock-imperfect"
        )

    run_config = {
        key: resolved[key]
        for key in (
            "spec_max_chars",
            "rules_source",
            "litellm_num_retries",
            "litellm_timeout_s",
            "litellm_kwargs",
        )
        if key in resolved
    }
    adapter = make_adapter(
        model_spec,
        expected,
        script=script,
        temperature=float(resolved["temperature"]),
        run_config=run_config,
    )
    baseline = get_baseline(resolved["baseline"])

    run_dir = (
        repo_root
        / resolved.get("output_dir", "experiments/runs")
        / f"{resolved.get('run_name', 'run')}-{config_hash(resolved)}"
    )
    if run_dir.exists():
        raise RuntimeError(f"run 已存在，禁止覆盖（plan.md §3.4）：{run_dir}")
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / "config.resolved.yaml").write_text(
        yaml.safe_dump(resolved, allow_unicode=True, sort_keys=True), encoding="utf-8"
    )

    # 2) 对照公平性与规则来源诊断（实验前落盘，可审计）
    spec_dir = _spec_dir(repo_root, resolved)
    selection = snapshot_selection(spec_dir, resolved.get("spec_max_chars"))
    (run_dir / "spec_selection.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if resolved["baseline"] in ("m_lite", "m_verified"):
        from engine.rule_bank import build_rules, rules_source_from

        source = rules_source_from(adapter)
        _rules, diagnostic = build_rules(spec_dir, source)
        (run_dir / "rules_diagnostic.json").write_text(
            json.dumps(diagnostic, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        diagnostic = {}

    # 3) 逐 case 预测
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

    # 4) 指标 + 记账
    if resolved["baseline"] == "m_verified":
        # 验证关逐规则结果归档（I3 可诊断性，docs/STATUS-I2.md §3-1）：
        # 门 2/3 过滤了哪些规则必须在 run 目录内可审计。
        from baselines.m_verified import verify_report

        verify_snapshot = verify_report(str(spec_dir.resolve()), source)
        if verify_snapshot is not None:
            (run_dir / "verify_report.json").write_text(
                json.dumps(verify_snapshot, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    usage = getattr(adapter, "usage", None)
    usage_dict = usage.to_dict() if usage is not None else {}
    (run_dir / "usage.json").write_text(
        json.dumps(usage_dict, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    price = resolved.get("price_per_1k_tokens")
    est_cost = (
        round(usage_dict.get("total_tokens", 0) / 1000 * float(price), 6)
        if price is not None
        else None
    )

    summary = compute_metrics(outcomes)
    summary.update(
        {
            "run_name": resolved.get("run_name", "run"),
            "baseline": resolved["baseline"],
            "model": model_spec,
            "temperature": resolved["temperature"],
            "run_index": resolved["run_index"],
            "code_digest": resolved["code_digest"],
            "rules_source": run_config.get("rules_source"),
            "spec_files_used": selection["files_used"],
            "spec_files_omitted": selection["files_omitted"],
            "n_llm_calls": usage_dict.get("n_calls", 0),
            "total_tokens": usage_dict.get("total_tokens", 0),
            "latency_s": usage_dict.get("latency_s", 0.0),
            "estimated_cost_usd": est_cost,
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
