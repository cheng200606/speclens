"""冻结规则库与 ID 对齐（I1 P0-1）。"""

from pathlib import Path

import pytest

from bench.harness.model_adapter import MockPerfectAdapter
from engine.rule_bank import (
    align_rules,
    build_rules,
    load_rule_bank,
    rules_source_from,
    validate_quotes,
)

REPO = Path(__file__).resolve().parent.parent
REACT19 = REPO / "bench" / "specs" / "react19"


def test_canonical_bank_has_12_verbatim_quotes():
    rules = load_rule_bank(REACT19)
    assert len(rules) == 12
    assert [r.id for r in rules] == [f"R-{i:03d}" for i in range(1, 13)]
    check = validate_quotes(rules, REACT19)
    assert check["all_verbatim"], check["missing_quote_rule_ids"]
    assert check["n_verbatim"] == 12


def test_alignment_is_one_to_one_and_relabels_only_ids():
    from engine.extract import extract_rules

    canonical = load_rule_bank(REACT19)
    synthesized = extract_rules(REACT19, spec_id="react19")
    out = align_rules(synthesized, canonical)
    ids = [r.id for r in out.rules]
    assert len(ids) == len(set(ids)), "对齐后不得出现重复 ID"
    assert out.report.n_matched >= 7
    assert out.report.n_matched <= out.report.n_canonical
    assert out.report.coverage == round(out.report.n_matched / 12, 4)
    assert len({m["canonical_id"] for m in out.report.matches}) == out.report.n_matched
    # 只重标注 ID：规则内容必须与合成规则逐条一致
    for original, relabeled in zip(synthesized, out.rules):
        assert relabeled.assertion == original.assertion
        assert relabeled.source_span.quote == original.source_span.quote
        assert relabeled.synthesis_id == original.id
    # canonical 规则对象本身不得进入规则集（避免标注泄漏）
    assert all(r.assertion and r.source_span.quote for r in out.rules)
    assert out.report.unmatched_canonical_ids


def test_build_rules_sources_and_oracle_flag():
    canonical, diag_c = build_rules(REACT19, "canonical")
    assert len(canonical) == 12
    assert diag_c["oracle_leakage"] is True

    aligned, diag_a = build_rules(REACT19, "aligned")
    assert len(aligned) == 44
    assert diag_a["oracle_leakage"] is False
    assert diag_a["alignment"]["n_matched"] >= 7
    assert diag_a["quote_check"]["all_verbatim"]

    synthesized, diag_s = build_rules(REACT19, "synthesized")
    assert len(synthesized) == 44
    assert all(r.id.startswith("react19-auto-") for r in synthesized)
    assert diag_s["rules_source"] == "synthesized"

    with pytest.raises(ValueError):
        build_rules(REACT19, "unknown")


def test_rules_source_from_adapter_run_config():
    plain = MockPerfectAdapter({})
    assert rules_source_from(plain) == "synthesized"
    configured = MockPerfectAdapter({}, run_config={"rules_source": "aligned"})
    assert rules_source_from(configured) == "aligned"
    with pytest.raises(ValueError):
        rules_source_from(MockPerfectAdapter({}, run_config={"rules_source": "bogus"}))
