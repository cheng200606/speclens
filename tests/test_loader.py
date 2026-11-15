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


def test_load_all_cases():
    cases = load_cases(CASES_DIR)
    by_id = {c.meta.case_id: c.meta.resolved.verdict.value for c in cases}
    assert len(by_id) == 112  # TS-001..TS-112（I5 四批 + 2 mined）
    assert by_id["TS-001"] == "violation"
    assert by_id["TS-002"] == "compliant"
    assert by_id["TS-005"] == "borderline"
    assert by_id["TS-012"] == "violation"
    assert by_id["TS-013"] == "compliant"
    assert by_id["TS-017"] == "borderline"
    # I2 扩样（TS-018..TS-040）判定抽查
    assert by_id["TS-018"] == "compliant"
    assert by_id["TS-026"] == "compliant"
    assert by_id["TS-034"] == "violation"
    assert by_id["TS-035"] == "borderline"
    assert by_id["TS-036"] == "borderline"
    assert by_id["TS-040"] == "violation"
    # verdict 分布（I2 扩样后：合规占比 ≥30%）
    assert sum(v == "violation" for v in by_id.values()) == 59
    assert sum(v == "compliant" for v in by_id.values()) == 49
    assert sum(v == "borderline" for v in by_id.values()) == 4


def test_frozen_rules_have_violation_and_compliant():
    """每条冻结规则都至少有 1 个违规样本和 1 个合规样本（I2 扩样目标）。"""
    rules = yaml.safe_load(
        (REPO / "bench" / "specs" / "react19" / "rules.yaml").read_text(encoding="utf-8")
    )
    frozen = {r["id"] for r in rules["rules"]}
    seen: dict[str, set[str]] = {}
    for case in load_cases(CASES_DIR):
        verdict = case.meta.resolved.verdict.value
        for rid in case.meta.resolved.rule_ids:
            seen.setdefault(rid, set()).add(verdict)
    assert set(seen) == frozen, "有冻结规则无任何样本覆盖"
    for rid in sorted(frozen):
        assert "violation" in seen[rid], f"{rid} 缺违规样本"
        assert "compliant" in seen[rid], f"{rid} 缺合规样本"


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
