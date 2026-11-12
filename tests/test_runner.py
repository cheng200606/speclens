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


def _expected_counts() -> tuple[int, float]:
    """按 bench 当前样本动态计算期望值（样本扩充时测试不需改）。"""
    from bench.harness.loader import load_cases
    from bench.harness.schemas import Difficulty, Verdict

    cases = load_cases(REPO / "bench" / "cases" / "react19")
    violations = [c for c in cases if c.meta.resolved.verdict == Verdict.VIOLATION]
    easy = [c for c in violations if c.meta.difficulty == Difficulty.EASY]
    return len(cases), round(len(easy) / len(violations), 4)


def test_mock_perfect_run(tmp_path: Path):
    run_dir = run(_config(tmp_path, "mock-perfect"), REPO)
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    n_cases, _ = _expected_counts()
    assert summary["baseline"] == "b0_zero_shot"
    assert summary["n_cases"] == n_cases
    assert summary["detection_rate"] == 1.0
    assert summary["false_positive_rate"] == 0.0
    assert summary["rule_match_rate"] == 1.0
    assert summary["n_borderline"] == 2


def test_mock_imperfect_run_metric_math(tmp_path: Path):
    # imperfect 只报 easy 违规样本，期望检出率按当前 bench 动态计算
    run_dir = run(_config(tmp_path, "mock-imperfect"), REPO)
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    _, expected_detection = _expected_counts()
    assert summary["detection_rate"] == expected_detection
    assert summary["false_positive_rate"] == 0.0


def test_run_artifacts_layout(tmp_path: Path):
    run_dir = run(_config(tmp_path, "mock-perfect"), REPO)
    assert (run_dir / "results.jsonl").exists()
    assert (run_dir / "config.resolved.yaml").exists()
    assert (run_dir / "raw" / "TS-001.json").exists()
    lines = (run_dir / "results.jsonl").read_text(encoding="utf-8").strip().splitlines()
    n_cases, _ = _expected_counts()
    assert len(lines) == n_cases
    first = json.loads(lines[0])
    assert first["case_id"] == "TS-001"
    assert first["predicted"] is True
