"""标注一致性与基准体检（I1 P0-5）。"""

from pathlib import Path

from bench.harness.agreement import cohens_kappa, mean_jaccard, validate_bench

REPO = Path(__file__).resolve().parent.parent


def test_kappa_known_values():
    assert cohens_kappa([]) is None
    assert cohens_kappa([("violation", "violation")] * 10) is None  # 退化：pe=1
    k = cohens_kappa(
        [("violation", "violation")] * 5
        + [("compliant", "compliant")] * 4
        + [("violation", "compliant")] * 1
    )
    # po=0.9, pe=0.5 → κ=0.8
    assert k == 0.8


def test_mean_jaccard():
    assert mean_jaccard([]) is None
    assert mean_jaccard([({"R-001"}, {"R-001"})]) == 1.0
    assert mean_jaccard([({"R-001"}, set())]) == 0.0


def test_bench_health_reports_real_gaps_honestly():
    report = validate_bench(REPO)
    assert report["n_cases_total"] == 92  # 40 生死 + 18 仓库集 + 10 airbnb + 8 agents-sdk + 16 asvs
    aux = report["per_spec"]["react19-repo"]
    assert aux["n_cases"] == 18  # RQ4 仓库梯度集（共享 react19 规则库）
    assert report["n_specs_total"] == 4
    assert report["n_specs_with_cases"] == 5  # react19 + react19-repo + airbnb + agents-sdk + asvs
    assert report["kappa_available"] is False
    assert report["kappa_verdict_overall"] is None
    r19 = report["per_spec"]["react19"]
    assert r19["hard_ratio"] == 0.225  # I2 复核 TS-028 hard→medium 后 9/40
    assert r19["n_dual_annotated"] == 0
    assert r19["quote_check"]["all_verbatim"] is True
    assert r19["unknown_referenced_rule_ids"] == []
    joined = " ".join(report["warnings"])
    # 40 已达生死实验最低线，故不再报该警告；仍如实报告 κ 缺失 / 全量集缺口 / 单规范
    assert "κ" in joined
    assert "92 < 全量集最低线 240" in joined
    assert "生死实验最低线" not in joined
