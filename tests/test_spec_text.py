"""spec_text 拼装测试。"""

from pathlib import Path

from bench.harness.loader import load_cases
from bench.harness.spec_text import assemble_spec_text, csv_to_text, spec_text_for_case

REPO = Path(__file__).resolve().parent.parent


def test_react19_assembly_contains_grounding_quote():
    text, used = assemble_spec_text(REPO / "bench" / "specs" / "react19")
    # 来自快照的逐字句（R-006 引句）
    assert "use` must be called inside a Component or a Hook" in text
    assert used, "至少纳入一个快照文件"
    assert "reference-react-use.md" in used


def test_react19_assembly_strips_frontmatter():
    text, _ = assemble_spec_text(REPO / "bench" / "specs" / "react19")
    assert not text.lstrip().startswith("---")


def test_asvs_csv_conversion():
    text, used = assemble_spec_text(REPO / "bench" / "specs" / "asvs")
    assert "V2.2.1" in text and "(L1):" in text
    assert used == ["asvs-5.0.0-en.csv", "README-upstream.md"]


def test_max_chars_cap():
    text, used = assemble_spec_text(
        REPO / "bench" / "specs" / "react19", max_chars=5000
    )
    assert len(text) < 5000 + 2000  # 头部开销
    assert len(used) < 6  # 大文件被跳过


def test_spec_text_for_case():
    cases = load_cases(REPO / "bench" / "cases" / "react19")
    text, used = spec_text_for_case(cases[0])
    assert "Specification: React" in text
    assert used
