"""engine/trace：证据链回填 + 聚合去重测试。"""

from bench.harness.schemas import Finding, FindingEvidence, RuleRecord, SourceSpan, Trigger
from engine.trace import aggregate, attach_evidence, deduplicate


def _rule(rid: str, quote: str) -> RuleRecord:
    return RuleRecord(
        id=rid,
        spec_id="react19",
        level="MUST",
        category="T2-api-usage",
        trigger=Trigger(scenario="test section", ast_cues=[]),
        assertion=quote,
        source_span=SourceSpan(section="test section", quote=quote),
    )


def _finding(
    file: str,
    line_start: int,
    line_end: int,
    rule_ids: list[str],
    message: str = "m",
    severity: str = "warning",
    evidence: FindingEvidence | None = None,
) -> Finding:
    return Finding(
        file=file,
        line_start=line_start,
        line_end=line_end,
        rule_ids=rule_ids,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        evidence=evidence or FindingEvidence(),
    )


RULES = [
    _rule("R-001", "`use` must be called inside a Component or a Hook."),
    _rule("R-003", "Effects must return a cleanup function."),
]


def test_attach_evidence_fills_empty_only():
    findings = [
        _finding("a.tsx", 1, 2, ["R-001"]),
        _finding(
            "b.tsx",
            3,
            4,
            ["R-003"],
            evidence=FindingEvidence(rule_quote="custom", explanation="custom"),
        ),
        _finding("c.tsx", 5, 6, ["UNKNOWN-RULE"]),
    ]
    out = attach_evidence(findings, RULES)
    assert out[0].evidence.rule_quote == "`use` must be called inside a Component or a Hook."
    assert "[R-001]" in out[0].evidence.explanation
    # 已有证据不覆盖
    assert out[1].evidence.rule_quote == "custom"
    # 未知规则：保持空
    assert out[2].evidence.rule_quote == ""


def test_deduplicate_exact_and_overlap():
    findings = [
        _finding("a.tsx", 1, 3, ["R-001"], message="x"),
        _finding("a.tsx", 1, 3, ["R-001"], message="x"),  # 精确重复
        _finding("a.tsx", 2, 5, ["R-001"], message="y", severity="error"),  # 重叠合并
        _finding("a.tsx", 20, 22, ["R-001"]),  # 不重叠，保留
        _finding("b.tsx", 1, 2, ["R-003"]),
    ]
    out = deduplicate(findings)
    a_r1 = [f for f in out if f.file == "a.tsx" and frozenset(f.rule_ids) == {"R-001"}]
    assert len(a_r1) == 2  # 合并为 1（1-5）+ 独立 1（20-22）
    merged = next(f for f in a_r1 if f.line_start == 1)
    assert merged.line_end == 5
    assert merged.severity == "error" and merged.message == "y"
    assert len(out) == 3


def test_deduplicate_keeps_different_rule_sets():
    findings = [
        _finding("a.tsx", 1, 3, ["R-001"], message="m1"),
        _finding("a.tsx", 1, 3, ["R-003"], message="m2"),  # 不同规则集：不合并
    ]
    assert len(deduplicate(findings)) == 2


def test_aggregate_sorts_and_attaches():
    findings = [
        _finding("b.tsx", 1, 2, ["R-003"]),
        _finding("a.tsx", 10, 12, ["R-001"], severity="info"),
        _finding("a.tsx", 1, 2, ["R-001"]),
    ]
    out = aggregate(findings, RULES)
    assert [(f.file, f.line_start) for f in out] == [
        ("a.tsx", 1),
        ("a.tsx", 10),
        ("b.tsx", 1),
    ]
    assert all(f.evidence.rule_quote for f in out)
