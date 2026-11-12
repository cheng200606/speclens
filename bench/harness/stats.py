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


def _correctness_from_run(run_dir: Path) -> dict[str, bool]:
    """从 results.jsonl 读出逐 case 的「正确性」：
    violation → 报告了 finding 即正确；compliant → 未报告即正确；borderline 不计。
    """
    out: dict[str, bool] = {}
    for line in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec["resolved_verdict"] == "borderline":
            continue
        predicted = rec["predicted"]
        out[rec["case_id"]] = (
            predicted if rec["resolved_verdict"] == "violation" else not predicted
        )
    return out


def mcnemar_between_runs(run_a: Path, run_b: Path) -> dict:
    """比较两次 run 的逐 case 正确性，返回 {"b","c","n_discordant","p"}。

    b = run_a 对而 run_b 错；c = run_a 错而 run_b 对。
    """
    corr_a = _correctness_from_run(run_a)
    corr_b = _correctness_from_run(run_b)
    common = sorted(set(corr_a) & set(corr_b))
    b = sum(1 for cid in common if corr_a[cid] and not corr_b[cid])
    c = sum(1 for cid in common if not corr_a[cid] and corr_b[cid])
    return {
        "n_paired": len(common),
        "b_a_right_b_wrong": b,
        "c_a_wrong_b_right": c,
        "p_mcnemar_exact": mcnemar_exact(b, c),
    }
