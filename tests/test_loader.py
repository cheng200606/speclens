"""loader 与 schema 校验测试。"""

from pathlib import Path

import pytest
import yaml

from bench.harness.loader import load_cases, load_spec

REPO = Path(__file__).resolve().parent.parent
CASES_DIR = REPO / "bench" / "cases" / "react19"


def test_load_spec_react19():
    spec = load_spec(REPO / "bench" / "specs" / "react19")
    assert spec.spec_id == "react19"
    assert spec.license == "CC-BY-4.0"
    assert spec.status == "snapshot"
    assert spec.snapshot_date is not None
    assert spec.freshness_probe == "freshness_probe.yaml"


def test_load_five_seed_cases():
    cases = load_cases(CASES_DIR)
    by_id = {c.meta.case_id: c.meta.resolved.verdict.value for c in cases}
    assert by_id == {
        "TS-001": "violation",
        "TS-002": "compliant",
        "TS-003": "violation",
        "TS-004": "violation",
        "TS-005": "borderline",
    }


def test_case_files_readable():
    for case in load_cases(CASES_DIR):
        for rel in case.meta.files:
            assert (case.root / rel).exists()
            assert len(case.read_file(rel)) > 0


def test_difficulty_coverage():
    meta = {c.meta.case_id: c.meta for c in load_cases(CASES_DIR)}
    assert meta["TS-001"].difficulty.value == "medium"
    assert meta["TS-005"].difficulty.value == "hard"


def test_case_id_mismatch_rejected(tmp_path: Path):
    case_dir = tmp_path / "XX-999"
    case_dir.mkdir()
    (case_dir / "meta.yaml").write_text(
        yaml.safe_dump(
            {
                "case_id": "TS-014",
                "verdict": "compliant",
                "difficulty": "easy",
                "rule_ids": [],
                "origin": "handcrafted",
                "files": [],
                "resolved": {"verdict": "compliant", "rule_ids": []},
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="case_id 与目录名不一致"):
        load_cases(tmp_path)
