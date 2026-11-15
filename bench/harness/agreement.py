"""标注一致性与基准体检（plan.md §1.3 / §2.3.3；docs/STATUS-I1.md P0-5）。

提供两类产物：
1. **Cohen's κ**：按 verdict 三分类计算双标一致性；规则集合另用平均 Jaccard 报告
   （κ 不适合多标签集合，混算会失真）。无双标样本时返回 None，不伪造 0 或 1。
2. **基准体检**：逐规范给出样本量、verdict / difficulty / origin 分布、hard 占比、
   双标覆盖率、规则 ID 是否落在冻结规则库内、引句是否逐字可溯源，并给出
   明确的未达标清单（Go / No-Go 依据）。

用法：
    uv run python -m bench.harness.agreement --root . --json experiments/reports/bench-health.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import yaml

from bench.harness.schemas import CaseMeta

HARD_RATIO_MIN = 0.20  # plan.md §2.3.2
LITMUS_CASES_MIN = 40  # plan.md §2.4
FULL_CASES_MIN = 240  # plan.md §1.3
KAPPA_MIN = 0.60  # plan.md §1.3


def cohens_kappa(pairs: list[tuple[str, str]]) -> float | None:
    """两标注人 verdict 的 Cohen's κ；样本为 0 或期望一致率退化时返回 None。"""
    if not pairs:
        return None
    labels = sorted({v for pair in pairs for v in pair})
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in labels)
    if pe >= 1.0:
        return None
    return round((po - pe) / (1.0 - pe), 4)


def mean_jaccard(pairs: list[tuple[set[str], set[str]]]) -> float | None:
    """多标签 rule_ids 的集合一致性（平均 Jaccard），与 κ 分开报告。"""
    if not pairs:
        return None
    scores = []
    for a, b in pairs:
        u = a | b
        scores.append(len(a & b) / len(u) if u else 1.0)
    return round(sum(scores) / len(scores), 4)


def _load_meta(path: Path) -> CaseMeta:
    return CaseMeta.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def validate_bench(repo_root: Path) -> dict:
    """返回可 JSON 序列化的体检报告；不修改任何文件。"""
    cases_root = repo_root / "bench" / "cases"
    specs_root = repo_root / "bench" / "specs"
    per_spec: dict[str, dict] = {}
    all_pairs: list[tuple[str, str]] = []
    all_rule_pairs: list[tuple[set[str], set[str]]] = []
    warnings: list[str] = []

    for spec_dir in sorted(p for p in cases_root.iterdir() if p.is_dir()):
        spec_id = spec_dir.name
        cases = [_load_meta(p / "meta.yaml") for p in sorted(spec_dir.iterdir()) if (p / "meta.yaml").exists()]
        verdicts = Counter(m.resolved.verdict.value for m in cases)
        difficulty = Counter(m.difficulty.value for m in cases)
        origin = Counter(m.origin.value for m in cases)

        pairs: list[tuple[str, str]] = []
        rule_pairs: list[tuple[set[str], set[str]]] = []
        dual = 0
        for m in cases:
            anns = m.annotations
            if len(anns) >= 2:
                dual += 1
                pairs.append((anns[0].verdict.value, anns[1].verdict.value))
                rule_pairs.append((set(anns[0].rule_ids), set(anns[1].rule_ids)))
        all_pairs.extend(pairs)
        all_rule_pairs.extend(rule_pairs)

        # RQ4 仓库集（react19-repo 等）共享基础规范的冻结规则库
        bank_spec = spec_id.removesuffix("-repo")
        bank_path = specs_root / bank_spec / "rules.yaml"
        canonical_ids: set[str] = set()
        quote_check = None
        if bank_path.exists():
            data = yaml.safe_load(bank_path.read_text(encoding="utf-8")) or {}
            canonical_ids = {r["id"] for r in data.get("rules", [])}
            from engine.rule_bank import load_rule_bank, validate_quotes

            quote_check = validate_quotes(
                load_rule_bank(specs_root / bank_spec), specs_root / bank_spec
            )
        referenced = {
            rid
            for m in cases
            for rid in [*m.rule_ids, *m.resolved.rule_ids]
        }
        unknown = sorted(referenced - canonical_ids) if canonical_ids else []

        hard_ratio = round(difficulty.get("hard", 0) / len(cases), 4) if cases else None
        per_spec[spec_id] = {
            "n_cases": len(cases),
            "verdict": dict(verdicts),
            "difficulty": dict(difficulty),
            "origin": dict(origin),
            "hard_ratio": hard_ratio,
            "n_dual_annotated": dual,
            "dual_coverage": round(dual / len(cases), 4) if cases else None,
            "kappa_verdict": cohens_kappa(pairs),
            "kappa_available": bool(pairs),
            "rule_set_jaccard": mean_jaccard(rule_pairs),
            "canonical_rule_ids": sorted(canonical_ids),
            "unknown_referenced_rule_ids": unknown,
            "quote_check": quote_check,
        }
        if hard_ratio is not None and hard_ratio < HARD_RATIO_MIN:
            warnings.append(
                f"{spec_id}: hard 样本占比 {hard_ratio:.1%} < {HARD_RATIO_MIN:.0%}"
            )
        if unknown:
            warnings.append(f"{spec_id}: 标注引用了冻结规则库之外的 ID {unknown}")
        if quote_check and not quote_check["all_verbatim"]:
            warnings.append(
                f"{spec_id}: {len(quote_check['missing_quote_rule_ids'])} 条规则引句非逐字"
            )

    total = sum(s["n_cases"] for s in per_spec.values())
    kappa = cohens_kappa(all_pairs)
    if kappa is None:
        warnings.append(
            "Cohen's κ 无法计算：全量集双标样本为 0（plan.md §2.3.3 降级预案尚未执行）"
        )
    elif kappa < KAPPA_MIN:
        warnings.append(f"Cohen's κ = {kappa} < {KAPPA_MIN}，需修订标注指南并重标")
    if total < LITMUS_CASES_MIN:
        warnings.append(f"样本总数 {total} < 生死实验最低线 {LITMUS_CASES_MIN}")
    if total < FULL_CASES_MIN:
        warnings.append(f"样本总数 {total} < 全量集最低线 {FULL_CASES_MIN}")

    specs_with_cases = sum(1 for s in per_spec.values() if s["n_cases"] > 0)
    n_specs = len(list(p for p in specs_root.iterdir() if p.is_dir()))
    if specs_with_cases < n_specs:
        warnings.append(
            f"仅 {specs_with_cases}/{n_specs} 份规范有标注样本，RQ1/RQ3 跨规范分解不可行"
        )

    return {
        "n_specs_total": n_specs,
        "n_specs_with_cases": specs_with_cases,
        "n_cases_total": total,
        "kappa_verdict_overall": kappa,
        "kappa_available": bool(all_pairs),
        "rule_set_jaccard_overall": mean_jaccard(all_rule_pairs),
        "thresholds": {
            "kappa_min": KAPPA_MIN,
            "hard_ratio_min": HARD_RATIO_MIN,
            "litmus_cases_min": LITMUS_CASES_MIN,
            "full_cases_min": FULL_CASES_MIN,
        },
        "per_spec": per_spec,
        "warnings": warnings,
        "schema_errors": [],
    }


def format_text(report: dict) -> str:
    lines = [
        "# SpecLens-Bench 基准体检",
        "",
        f"- 规范：{report['n_specs_total']} 份（有样本 {report['n_specs_with_cases']} 份）",
        f"- 样本：{report['n_cases_total']} 条",
        f"- Cohen's κ（verdict）：{report['kappa_verdict_overall'] if report['kappa_available'] else 'N/A（无双标样本）'}",
        f"- 规则集合平均 Jaccard：{report['rule_set_jaccard_overall']}",
        "",
        "## 逐规范",
        "",
        "| spec | n | violation | compliant | borderline | hard 占比 | 双标数 | κ | 引句逐字 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for sid, s in report["per_spec"].items():
        q = s["quote_check"]
        lines.append(
            f"| {sid} | {s['n_cases']} | {s['verdict'].get('violation', 0)} "
            f"| {s['verdict'].get('compliant', 0)} | {s['verdict'].get('borderline', 0)} "
            f"| {s['hard_ratio']} | {s['n_dual_annotated']} "
            f"| {s['kappa_verdict'] if s['kappa_available'] else 'N/A'} "
            f"| {q['all_verbatim'] if q else 'N/A'} |"
        )
    lines += ["", "## 未达标项", ""]
    lines += [f"- {w}" for w in report["warnings"]] or ["- 无"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SpecLens 基准体检与标注一致性")
    parser.add_argument("--root", default=".", help="仓库根目录")
    parser.add_argument("--json", default=None, help="JSON 报告输出路径")
    args = parser.parse_args(argv)

    report = validate_bench(Path(args.root).resolve())
    print(format_text(report))
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[speclens] bench health -> {out}")


if __name__ == "__main__":
    main()
