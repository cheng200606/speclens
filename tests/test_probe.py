"""新鲜度探测题库与 runner 测试。"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from bench.harness.probe import ProbeAnswer, load_probe, run_probe

REPO = Path(__file__).resolve().parent.parent
SPECS = ["react19", "agents-sdk", "asvs", "airbnb"]


def _spec_dir(spec_id: str) -> Path:
    return REPO / "bench" / "specs" / spec_id


def test_all_four_probes_have_20_groundable_questions():
    for spec_id in SPECS:
        bank = load_probe(_spec_dir(spec_id) / "freshness_probe.yaml")
        assert len(bank.questions) == 20, spec_id
        ids = [q.id for q in bank.questions]
        assert len(set(ids)) == len(ids), spec_id
        for q in bank.questions:
            assert len(q.options) == 4, (spec_id, q.id)
            # source 指向的快照文件必须真实存在
            assert (_spec_dir(spec_id) / q.source).exists(), (spec_id, q.id, q.source)


@pytest.mark.parametrize("spec_id", SPECS)
def test_probe_sources_reference_snapshot(spec_id: str):
    bank = load_probe(_spec_dir(spec_id) / "freshness_probe.yaml")
    assert all(q.source.startswith("snapshot/") for q in bank.questions)


class _FixedChoiceAdapter:
    """总是选第 fixed 项——用于验证 accuracy 口径。"""

    name = "mock-fixed"

    def __init__(self, fixed: int) -> None:
        self.fixed = fixed

    def complete_json(self, *, system, user, schema, meta=None):
        return ProbeAnswer(choice=self.fixed)


class _CorrectAdapter:
    name = "mock-correct-test"

    def complete_json(self, *, system, user, schema, meta=None):
        return ProbeAnswer(choice=meta["answer_index"])


def test_probe_accuracy_math(tmp_path: Path):
    probe = _spec_dir("react19") / "freshness_probe.yaml"
    bank = load_probe(probe)
    expected = round(
        sum(1 for q in bank.questions if q.answer_index == 0) / len(bank.questions), 4
    )
    _, summary = run_probe(probe, _FixedChoiceAdapter(0), tmp_path)
    assert summary["accuracy"] == expected
    assert summary["n_questions"] == 20

    _, perfect = run_probe(probe, _CorrectAdapter(), tmp_path)
    assert perfect["accuracy"] == 1.0


def test_probe_raw_artifacts(tmp_path: Path):
    probe = _spec_dir("asvs") / "freshness_probe.yaml"
    run_dir, _ = run_probe(probe, _CorrectAdapter(), tmp_path)
    assert (run_dir / "summary.json").exists()
    first = json.loads(
        (run_dir / "raw" / "asvs-P01.json").read_text(encoding="utf-8")
    )
    assert first["correct"] is True


def test_invalid_answer_index_rejected(tmp_path: Path):
    bad = tmp_path / "bad_probe.yaml"
    bad.write_text(
        """
spec_id: bad
created: "2026-11-13"
questions:
  - id: bad-P01
    question: "q"
    options: ["a", "b"]
    answer_index: 5
    source: "snapshot/x.md"
""",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_probe(bad)
