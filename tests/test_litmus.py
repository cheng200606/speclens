"""生死实验端到端测试：三配置 mock 跑通 → 报告生成。"""

import json
from pathlib import Path

from experiments.make_report import make_report
from bench.harness.runner import run

REPO = Path(__file__).resolve().parent.parent


def _run_config(tmp_path: Path, run_name: str, baseline: str) -> dict:
    return {
        "run_name": run_name,
        "baseline": baseline,
        "cases_dir": "bench/cases/react19",
        "model": "mock-perfect",
        "output_dir": str(tmp_path / "runs"),
    }


def test_litmus_end_to_end(tmp_path: Path):
    run(_run_config(tmp_path, "litmus-b0", "b0_zero_shot"), REPO)
    run(_run_config(tmp_path, "litmus-b1", "b1_full_spec"), REPO)
    run(_run_config(tmp_path, "litmus-mlite", "m_lite"), REPO)
    run(_run_config(tmp_path, "litmus-mverified", "m_verified"), REPO)

    report = make_report(
        tmp_path / "runs", tmp_path / "reports" / "litmus.md", prefix="litmus"
    )
    text = report.read_text(encoding="utf-8")
    assert "生死实验报告" in text
    for label in ("| B0 |", "| B1 |", "| M-lite |", "| M-verified |"):
        assert label in text
    # 四配置两两配对 = 6 组，mock-perfect 下结果完全一致 → p=1.0
    assert text.count("vs") >= 6
    assert "p_mcnemar" not in text  # 表格里用 p 表头
    assert "| B0 vs B1 | 15 | 0 | 0 | 1.0 |" in text  # 17 cases - 2 borderline = 15
    assert "| B0 vs M-verified | 15 | 0 | 0 | 1.0 |" in text
    assert "No-Go" in text  # 判读标准存在

    # summary 数值一致性（mock-perfect 完美预测；m_verified 经 gate1 过滤后仍全检出）
    for run_dir in (tmp_path / "runs").glob("litmus-*"):
        s = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        assert s["detection_rate"] == 1.0
        assert s["false_positive_rate"] == 0.0
