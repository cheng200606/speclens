"""统计检验（plan.md §2.4 / §5：生死实验用 case 级配对 McNemar）。

零第三方依赖：McNemar 用精确二项检验（math.comb），适配小样本（Phase 0 n=40）。
"""

from __future__ import annotations

import json
import math
from pathlib import Path


def mcnemar_exact(b: int, c: int) -> float:
    """双尾精确 McNemar p 值。

    b = A 对而 B 错的对子数，c = A 错而 B 对的对子数。
    p = 2 * P(X <= min(b,c))，X ~ Bin(b+c, 0.5)；封顶 1.0。
    """
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1))
    return min(1.0, 2.0 * tail / 2**n)


def _records_from_run(run_dir: Path) -> dict[str, dict]:
    """逐 case 记录 {verdict, correct}；borderline 不计入主指标。"""
    out: dict[str, dict] = {}
    for line in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        verdict = rec["resolved_verdict"]
        if verdict == "borderline":
            continue
        predicted = rec["predicted"]
        out[rec["case_id"]] = {
            "verdict": verdict,
            "correct": predicted if verdict == "violation" else not predicted,
        }
    return out


def _correctness_from_run(run_dir: Path) -> dict[str, bool]:
    """兼容旧接口：仅返回 case_id → 是否正确。"""
    return {cid: r["correct"] for cid, r in _records_from_run(run_dir).items()}


def mcnemar_between_runs(
    run_a: Path, run_b: Path, subset: str = "all"
) -> dict:
    """比较两次 run 的逐 case 正确性，返回 {"b","c","n_discordant","p"}。

    b = run_a 对而 run_b 错；c = run_a 错而 run_b 对。
    subset ∈ {all, violation, compliant}：plan.md §2.4 的判据分别看
    「检出 +10pp」与「误报 −20%」，混合整体正确率无法对应任一判据（S1-8）。
    """
    if subset not in ("all", "violation", "compliant"):
        raise ValueError(f"未知 subset={subset!r}")
    rec_a = _records_from_run(run_a)
    rec_b = _records_from_run(run_b)
    common = sorted(
        cid
        for cid in set(rec_a) & set(rec_b)
        if subset == "all" or rec_a[cid]["verdict"] == subset
    )
    b = sum(1 for cid in common if rec_a[cid]["correct"] and not rec_b[cid]["correct"])
    c = sum(1 for cid in common if not rec_a[cid]["correct"] and rec_b[cid]["correct"])
    return {
        "n_paired": len(common),
        "b_a_right_b_wrong": b,
        "c_a_wrong_b_right": c,
        "p_mcnemar_exact": mcnemar_exact(b, c),
        "subset": subset,
    }


def mcnemar_subsets(run_a: Path, run_b: Path) -> dict:
    """同时给出 overall / violation-only / compliant-only 三组配对检验。"""
    return {
        name: mcnemar_between_runs(run_a, run_b, subset=name)
        for name in ("all", "violation", "compliant")
    }
