"""规则结构化合成（M-lite 确定性版）。

从规范章节中抽取「规范句」（含 must/never/don't/avoid/discouraged/should 等
规范性措辞的长句），生成 RuleRecord（含原文溯源），不做验证——验证是 M2 的 verify。
M2 将改为 LLM 合成 + 正反例；当前确定性提取可离线复现，用于生死实验的 M-lite。
"""

from __future__ import annotations

import re
from pathlib import Path

from engine.ingest import parse_document

_NORMATIVE = re.compile(
    r"\b(must(?:n't)?|never|do not|don't|cannot|should(?:n't)?|avoid|discouraged|always|required)\b",
    re.I,
)
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`*])")
# 常见 React 标识符 → 路由线索
_CUE_WORDS = [
    "use",
    "useEffect",
    "useActionState",
    "useOptimistic",
    "useTransition",
    "Suspense",
    "useContext",
    "Promise",
    "startTransition",
    "context",
]
_REACT_IDENT = re.compile(r"`([A-Za-z][A-Za-z0-9_.]*)`")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_BULLET = re.compile(r"^\s*[*\-+]\s+")


def _clean_sentence(sentence: str) -> str:
    """去列表符号与 markdown 链接外壳，保留正文（含反引号标识符）。"""
    sentence = _BULLET.sub("", sentence)
    sentence = _MD_LINK.sub(r"\1", sentence)
    return re.sub(r"\s+", " ", sentence).strip()


def _detect_cues(sentence: str) -> list[str]:
    backticked = [w for w in _REACT_IDENT.findall(sentence) if w in _CUE_WORDS]
    if backticked:
        return sorted(set(backticked))[:4]
    plain = [w for w in _CUE_WORDS if re.search(rf"\b{w}\b", sentence, re.I)]
    return sorted(set(plain))[:4]


def _normative_level(sentence: str) -> str | None:
    if re.search(r"\b(must|never|do not|don't|cannot|required)\b", sentence, re.I):
        return "MUST"
    if re.search(
        r"\b(should(?:n't)?|avoid|discouraged|prefer|recommended)\b", sentence, re.I
    ):
        return "SHOULD"
    return None


def extract_rules(
    spec_dir: Path,
    spec_id: str = "react19",
    max_rules: int = 60,
    max_per_section: int = 2,
) -> list[RuleRecord]:  # noqa: F821
    from bench.harness.schemas import (
        RuleRecord,  # 局部导入避免与类型注解循环
        SourceSpan,
        Trigger,
    )

    rules: list[RuleRecord] = []
    seen_quotes: set[str] = set()
    seq = 0
    for sec in parse_document(spec_dir):
        kept = 0
        for raw in _SENTENCE.split(sec["text"]):
            sentence = _clean_sentence(raw)
            if len(sentence) < 40 or len(sentence) > 400 or "`{" in sentence:
                continue
            level = _normative_level(sentence)
            if level is None or not _SENTENCE_was_normative(sentence):
                continue
            key = sentence[:80]
            if key in seen_quotes:
                continue
            seen_quotes.add(key)
            seq += 1
            rules.append(
                RuleRecord(
                    id=f"{spec_id}-auto-{seq:03d}",
                    spec_id=spec_id,
                    level=level,  # type: ignore[arg-type]
                    category="T2-api-usage",
                    trigger=Trigger(
                        scenario=sec["section"], ast_cues=_detect_cues(sentence)
                    ),
                    assertion=sentence,
                    source_span=SourceSpan(section=sec["section"], quote=sentence),
                )
            )
            kept += 1
            if kept >= max_per_section or len(rules) >= max_rules:
                break
        if len(rules) >= max_rules:
            break
    return rules


def _SENTENCE_was_normative(sentence: str) -> bool:
    return _NORMATIVE.search(sentence) is not None
