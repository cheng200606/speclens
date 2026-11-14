"""runner 记账、对照公平性与复现性（I1 P0-2 / P0-4）。"""

import json
from pathlib import Path

import pytest
import yaml

from bench.harness.runner import build_scripted_script, code_digest, run

REPO = Path(__file__).resolve().parent.parent


def _config(tmp_path: Path, **extra) -> dict:
    cfg = {
        "run_name": "pytest-accounting",
        "baseline": "b1_full_spec",
        "cases_dir": "bench/cases/react19",
        "model": "mock-scripted",
        "temperature": 0.2,
        "run_index": 2,
        "output_dir": str(tmp_path / "runs"),
    }
    cfg.update(extra)
    return cfg


def test_b1_uses_full_spec_without_silent_truncation(tmp_path: Path):
    run_dir = run(_config(tmp_path), REPO)
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    selection = json.loads((run_dir / "spec_selection.json").read_text(encoding="utf-8"))
    assert summary["spec_files_omitted"] == []
    assert len(summary["spec_files_used"]) == 6
    assert "reference-react-useTransition.md" in summary["spec_files_used"]
    assert selection["truncated"] is False
    assert selection["included_chars"] == 236158


def test_explicit_budget_is_recorded(tmp_path: Path):
    run_dir = run(_config(tmp_path, spec_max_chars=50_000), REPO)
    selection = json.loads((run_dir / "spec_selection.json").read_text(encoding="utf-8"))
    assert selection["truncated"] is True
    assert selection["files_omitted"]
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["spec_files_omitted"] == selection["files_omitted"]


def test_usage_reproducibility_and_no_overwrite(tmp_path: Path):
    cfg = _config(tmp_path)
    run_dir = run(cfg, REPO)
    usage = json.loads((run_dir / "usage.json").read_text(encoding="utf-8"))
    assert usage["n_calls"] == 17
    assert usage["total_tokens"] > 0
    assert usage["by_phase"]
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["temperature"] == 0.2
    assert summary["run_index"] == 2
    assert summary["code_digest"] == code_digest(REPO)
    resolved = yaml.safe_load((run_dir / "config.resolved.yaml").read_text(encoding="utf-8"))
    assert resolved["code_digest"] == summary["code_digest"]
    with pytest.raises(RuntimeError, match="禁止覆盖"):
        run(cfg, REPO)
    # 重复运行（run_index 不同）应得到不同目录
    run_dir2 = run(_config(tmp_path, run_index=3), REPO)
    assert run_dir2 != run_dir


def test_engine_runs_write_rule_diagnostics(tmp_path: Path):
    run_dir = run(
        _config(tmp_path, baseline="m_lite", rules_source="aligned"), REPO
    )
    diag = json.loads((run_dir / "rules_diagnostic.json").read_text(encoding="utf-8"))
    assert diag["oracle_leakage"] is False
    assert diag["quote_check"]["all_verbatim"] is True
    assert diag["alignment"]["n_matched"] >= 7


def test_scripted_script_error_pattern():
    from bench.harness.loader import load_cases
    from bench.harness.schemas import Difficulty, Verdict

    cases = load_cases(REPO / "bench" / "cases" / "react19")
    script = build_scripted_script(cases)
    hard_violations = [
        c.meta.case_id
        for c in cases
        if c.meta.resolved.verdict == Verdict.VIOLATION
        and c.meta.difficulty == Difficulty.HARD
    ]
    assert all(not script[cid]["detected"] for cid in hard_violations)
    compliants = [
        c.meta.case_id
        for c in cases
        if c.meta.resolved.verdict == Verdict.COMPLIANT
    ]
    assert sum(1 for cid in compliants if script[cid]["detected"]) == 1
