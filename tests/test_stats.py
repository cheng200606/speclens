"""McNemar 精确检验与跨 run 比较测试。"""

import json
from pathlib import Path

from bench.harness.stats import mcnemar_between_runs, mcnemar_exact


def test_mcnemar_no_discordant_pairs():
    assert mcnemar_exact(0, 0) == 1.0


def test_mcnemar_all_one_direction():
    # b=10, c=0：p = 2 * C(10,0) / 2^10
    assert abs(mcnemar_exact(10, 0) - 2 / 1024) < 1e-12
    # 对称性
    assert mcnemar_exact(0, 10) == mcnemar_exact(10, 0)


def test_mcnemar_bounded_and_symmetric():
    p = mcnemar_exact(3, 7)
    assert 0.0 < p <= 1.0
    assert p == mcnemar_exact(7, 3)


def test_mcnemar_between_runs_from_results(tmp_path: Path):
    def _write_run(d: Path, verdicts: dict[str, tuple[str, bool]]) -> Path:
        d.mkdir(parents=True)
        with (d / "results.jsonl").open("w", encoding="utf-8") as f:
            for cid, (verdict, predicted) in verdicts.items():
                f.write(
                    json.dumps(
                        {
                            "case_id": cid,
                            "resolved_verdict": verdict,
                            "predicted": predicted,
                        }
                    )
                    + "\n"
                )
        return d

    verdicts = {
        "TS-001": ("violation", True),
        "TS-002": ("compliant", False),
        "TS-003": ("violation", False),
        "TS-005": ("borderline", True),  # borderline 不计
    }
    run_a = _write_run(tmp_path / "a", verdicts)
    # run_b：TS-003 修正（run_a 错对）、TS-001 漏检（run_a 对错）
    run_b = _write_run(
        tmp_path / "b",
        {
            "TS-001": ("violation", False),
            "TS-002": ("compliant", False),
            "TS-003": ("violation", True),
            "TS-005": ("borderline", False),
        },
    )
    stats = mcnemar_between_runs(run_a, run_b)
    assert stats["n_paired"] == 3
    assert stats["b_a_right_b_wrong"] == 1
    assert stats["c_a_wrong_b_right"] == 1
    assert stats["p_mcnemar_exact"] == 1.0
