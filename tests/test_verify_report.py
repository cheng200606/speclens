"""I3 可诊断性：runner 必须把 M-verified 验证关逐规则结果归档为 verify_report.json。"""

import json
from pathlib import Path

from bench.harness.runner import run

REPO = Path(__file__).resolve().parent.parent


def test_runner_archives_verify_report(tmp_path: Path):
    cfg = {
        "run_name": "pytest-verify-report",
        "baseline": "m_verified",
        "cases_dir": "bench/cases/react19",
        "model": "mock-perfect",
        "output_dir": str(tmp_path / "runs"),
    }
    run_dir = run(cfg, REPO)
    vr = json.loads((run_dir / "verify_report.json").read_text(encoding="utf-8"))

    # 结构完整性：44 条合成规则逐条有 gate 结果与排除判定
    assert vr["policy"] == "fail-open"  # I3：仅确定性门 1 排除，门 2/3 只标记
    assert vr["n_rules"] == 44
    assert vr["n_kept"] + vr["n_excluded"] == 44
    assert vr["n_kept"] == 44  # I4 归一化修复后门 1 离线零排除（防回归不变量）
    assert len(vr["rules"]) == 44
    ids = {r["id"] for r in vr["rules"]}
    assert len(ids) == 44  # 无重复 ID

    # 逐规则字段
    first = vr["rules"][0]
    for key in ("id", "synthesis_id", "level", "grounding", "exec_test", "excluded", "exclusion_reasons"):
        assert key in first

    # mock 适配器不支持合成：门 2 全部 pending（不伪造），排除只来自 grounding/conflicts
    assert vr["verify_summary"]["gate2_exec_counts"]["pending"] == 44
    assert vr["exclusion_reason_counts"].get("exec-fail", 0) == 0
    assert vr["review_flag_counts"].get("exec-fail", 0) == 0  # pending 不标 exec-fail

    # 汇总报告随附（原 verify_rules 的返回不再被丢弃）
    assert vr["verify_summary"]["n_rules"] == 44
    assert vr["verify_summary"]["n_flagged"] == 0


def test_runner_omits_verify_report_for_other_baselines(tmp_path: Path):
    cfg = {
        "run_name": "pytest-no-verify-report",
        "baseline": "b0_zero_shot",
        "cases_dir": "bench/cases/react19",
        "model": "mock-perfect",
        "output_dir": str(tmp_path / "runs"),
    }
    run_dir = run(cfg, REPO)
    assert not (run_dir / "verify_report.json").exists()
