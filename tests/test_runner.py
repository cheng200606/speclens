"""runner 端到端测试：mock 适配器跑通 smoke 配置并校验指标。"""

import json
from pathlib import Path

from bench.harness.runner import run

REPO = Path(__file__).resolve().parent.parent


def _config(tmp_path: Path, model: str) -> dict:
    return {
        "run_name": "pytest-smoke",
        "baseline": "b0_zero_shot",
        "cases_dir": "bench/cases/react19",
        "model": model,
        "output_dir": str(tmp_path / "runs"),
    }


def test_mock_perfect_run(tmp_path: Path):
    run_dir = run(_config(tmp_path, "mock-perfect"), REPO)
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["baseline"] == "b0_zero_shot"
    assert summary["n_cases"] == 5
    assert summary["detection_rate"] == 1.0
    assert summary["false_positive_rate"] == 0.0
    assert summary["rule_match_rate"] == 1.0
    assert summary["n_borderline"] == 1


def test_mock_imperfect_run_metric_math(tmp_path: Path):
    # 违规样本：TS-001(medium)/TS-003(easy)/TS-004(easy)；imperfect 只报 easy
    run_dir = run(_config(tmp_path, "mock-imperfect"), REPO)
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["detection_rate"] == round(2 / 3, 4)
    assert summary["false_positive_rate"] == 0.0


def test_run_artifacts_layout(tmp_path: Path):
    run_dir = run(_config(tmp_path, "mock-perfect"), REPO)
    assert (run_dir / "results.jsonl").exists()
    assert (run_dir / "config.resolved.yaml").exists()
    assert (run_dir / "raw" / "TS-001.json").exists()
    lines = (run_dir / "results.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
    first = json.loads(lines[0])
    assert first["case_id"] == "TS-001"
    assert first["predicted"] is True
