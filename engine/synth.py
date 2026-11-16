"""LLM 规则合成原型（M2 方向，I8④）。

确定性提取器（extract.py）覆盖词面形态有限的规则；本模块验证 LLM 合成路线：
逐节提示模型产出候选规则（assertion 概括 + **逐字引句** + 级别 + 代码词元 cues），
并对每条引句做**逐字预校验**（_norm 后必须是章节文本子串）——不过校验的候选
直接丢弃并计数，保证产出引句可过门 1（与 I7 的「溯源行是唯一真源」一致）。

本原型不进入 M 管线对比（基准表仍用确定性提取器）；作为 M2 方向的可行性证据：
引句逐字率、对齐覆盖率、与冻结库的匹配质量。产出落盘
experiments/reports/synth-{spec}-{model_tag}.json。
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from bench.harness.model_adapter import ModelAdapter
from bench.harness.schemas import RuleRecord, SourceSpan, Trigger
from engine.extract import _strip_code
from engine.ingest import parse_document
from engine.verify import _content_words, _norm


class SynthRule(BaseModel):
    assertion: str = Field(description="One-sentence English normative statement")
    quote: str = Field(description="VERBATIM substring of the given section text")
    level: str = Field(description="MUST or SHOULD")
    cues: list[str] = Field(default_factory=list, description="Up to 3 identifiers likely in code")


class SynthOutput(BaseModel):
    rules: list[SynthRule] = Field(default_factory=list)


_SYSTEM = (
    "You extract candidate coding-standard rules from a specification section. "
    "For each normative requirement in the section output: assertion (one-sentence "
    "English summary), quote (a VERBATIM substring copied exactly from the section "
    "text, 15-220 characters, containing the requirement wording), level "
    "(MUST for hard requirements, SHOULD for recommendations), and cues (up to 3 "
    "identifiers or API names likely to appear in code following/violating this rule). "
    'Respond ONLY with JSON: {"rules": [...]}. Output no more than 4 rules.'
)


def _section_calls(spec_dir: Path, max_sections: int) -> list[dict]:
    """按规范性词密度选前 max_sections 个章节（确定性）。"""
    scored = []
    for i, sec in enumerate(parse_document(spec_dir)):
        text = _strip_code(sec["text"])
        dens = sum(
            1
            for w in ("must", "should", "verify", "never", "always", "avoid", "required")
            if w in text.lower()
        )
        scored.append((-dens, len(text) or 1, i, sec))
    scored.sort(key=lambda t: (t[0], t[1], t[2]))
    return [s[3] for s in scored[:max_sections]]


def synthesize_rules_llm(
    spec_dir: Path,
    spec_id: str,
    adapter: ModelAdapter,
    max_sections: int = 12,
    max_rules: int = 48,
) -> tuple[list[RuleRecord], dict]:
    """逐节 LLM 合成候选规则；引句逐字预校验，不过校验即丢弃。"""
    rules: list[RuleRecord] = []
    report = {
        "spec_id": spec_id,
        "model": adapter.name,
        "n_sections_prompted": 0,
        "n_rules_raw": 0,
        "n_quotes_verbatim": 0,
        "n_quotes_invalid": 0,
        "invalid_examples": [],
    }
    seq = 0
    for sec in _section_calls(spec_dir, max_sections):
        report["n_sections_prompted"] += 1
        text = _strip_code(sec["text"])
        norm_text = _norm(text)
        try:
            out: SynthOutput = adapter.complete_json(
                system=_SYSTEM,
                user=f"Specification section ({sec['section']}):\n\n{text[:6000]}",
                schema=SynthOutput,
                meta={"phase": "synthesize", "section": sec["section"]},
            )
        except Exception as exc:  # noqa: BLE001 - 单节失败不弃整体（fail-soft）
            report.setdefault("section_errors", []).append(
                {"section": sec["section"], "error": str(exc)[:200]}
            )
            continue
        for sr in out.rules[:4]:
            report["n_rules_raw"] += 1
            if _norm(sr.quote) not in norm_text or not _norm(sr.quote):
                report["n_quotes_invalid"] += 1
                if len(report["invalid_examples"]) < 5:
                    report["invalid_examples"].append(sr.quote[:120])
                continue
            report["n_quotes_verbatim"] += 1
            seq += 1
            rules.append(
                RuleRecord(
                    id=f"{spec_id}-llm-{seq:03d}",
                    spec_id=spec_id,
                    level=sr.level.upper() if sr.level.upper() in ("MUST", "SHOULD") else "SHOULD",
                    category="T2-api-usage",
                    trigger=Trigger(scenario=sec["section"], ast_cues=sr.cues[:3]),
                    assertion=sr.assertion,
                    source_span=SourceSpan(section=sec["section"], quote=sr.quote),
                )
            )
            if len(rules) >= max_rules:
                return rules, report
    return rules, report


def llm_coverage_diagnostic(
    spec_dir: Path, rules: list[RuleRecord]
) -> dict:
    """LLM 合成规则 ↔ 冻结库对齐覆盖（复用 rule_bank 对齐器）。"""
    from engine.rule_bank import align_rules, load_rule_bank

    canonical = load_rule_bank(spec_dir)
    ar = align_rules(rules, canonical).report
    return {
        "n_canonical": ar.n_canonical,
        "n_matched": ar.n_matched,
        "coverage": ar.coverage,
        "unmatched_canonical_ids": ar.unmatched_canonical_ids,
        "n_content_words_llm": sum(len(_content_words(r.assertion)) for r in rules),
    }
