"""规则结构化合成（M-lite 确定性版）。

从规范章节中抽取「规范句」（含 must/never/don't/avoid/discouraged/should 等
规范性措辞的长句），生成 RuleRecord（含原文溯源），不做验证——验证是 M2 的 verify。
M2 将改为 LLM 合成 + 正反例；当前确定性提取可离线复现，用于生死实验的 M-lite。

I7 跨规范泛化（I6 诊断：提取层失配是对齐坍塌的第一因）：
- 章节先剥围栏代码块（```），句子再滤表格行/HTML 锚点残片；
- ASVS 式「Verify that ...」计为 MUST；
- 路由 cues 从「React 白名单」泛化为「任意反引号标识符」（路由 v2 另有
  通用词黑名单兜底），非 React 规范终于有可用路由键。
"""

from __future__ import annotations

import re
from pathlib import Path

from engine.ingest import parse_document

_NORMATIVE = re.compile(
    r"\b(must(?:n't)?|never|do not|don't|cannot|should(?:n't)?|avoid|discouraged|always|required|verify)\b",
    re.I,
)
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`*])")
_FENCED_CODE = re.compile(r"```.*?```", re.S)
_INLINE_CODE_BLOCK = re.compile(r"^\s*```.*$", re.M)
# 代码块哨兵：句子跨代码块边界合并后引句不再逐字（门 1 会正确拒绝），
# 含哨兵的候选直接丢弃（I7，替代此前会伪造「跨块逐字」的空格替换）。
_CODE_SENTINEL = "@@CODE@@"
# 常见 React 标识符 → 路由线索（优先保留；其余反引号标识符按出现序补足）
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
_ANY_IDENT = re.compile(r"`([A-Za-z][A-Za-z0-9_.\-]{1,40})`")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_HTML_ANCHOR = re.compile(r"<a\s+name=\"[^\"]*\">\s*</a>", re.I)
_BULLET = re.compile(r"^\s*[*\-+]\s+")
_LIST_NUM = re.compile(r"^\s*(?:\(?\d+(?:\.\d+)*\)?\.?\s+)")


def _clean_sentence(sentence: str) -> str:
    """去列表符号/HTML 锚点/markdown 链接外壳/编号前缀，保留正文。

    顺序敏感：链接先转文本（[5.1](#x) → 5.1），编号前缀才能被剥离。
    """
    sentence = _HTML_ANCHOR.sub("", sentence)
    sentence = _BULLET.sub("", sentence)
    sentence = _MD_LINK.sub(r"\1", sentence)
    sentence = _LIST_NUM.sub("", sentence)
    return re.sub(r"\s+", " ", sentence).strip()


def _is_table_row(sentence: str) -> bool:
    """markdown 表格行残片（agents-sdk 断言噪声主源）。"""
    return sentence.startswith("|") or sentence.count(" | ") >= 2


def _strip_code(text: str) -> str:
    """章节级剥围栏代码块（airbnb 代码示例是引句噪声主源）。

    以哨兵替换而非空格：跨块合并的句子会被 @CODE@ 标记并在候选过滤中剔除。
    """
    text = _FENCED_CODE.sub(f"\n\n{_CODE_SENTINEL}\n\n", text)
    return _INLINE_CODE_BLOCK.sub(f"\n{_CODE_SENTINEL}", text)


def _detect_cues(sentence: str) -> list[str]:
    """React 优先，其次任意反引号标识符（I7 泛化；去纯数字/过短词）。"""
    backticked = [w for w in _REACT_IDENT.findall(sentence) if w in _CUE_WORDS]
    if backticked:
        return sorted(set(backticked))[:4]
    generic = [
        w
        for w in _ANY_IDENT.findall(sentence)
        if w not in _CUE_WORDS and not w.rstrip(".0123456789").isdigit() and len(w) >= 2
    ]
    if generic:
        seen: dict[str, None] = {}
        for w in generic:
            seen.setdefault(w, None)
        return list(seen)[:4]
    plain = [w for w in _CUE_WORDS if re.search(rf"\b{w}\b", sentence, re.I)]
    return sorted(set(plain))[:4]


_IMPERATIVE = re.compile(
    r"^(use|do not use|always use|never use|prefer|avoid|wrap|write|group|place)\b",
    re.I,
)


def _normative_level(sentence: str) -> str | None:
    if re.search(
        r"\b(must|never|do not|don't|cannot|required|verify)\b", sentence, re.I
    ):
        # ASVS 式「Verify that ...」是可验证 MUST 需求（I7）
        return "MUST"
    if re.search(
        r"\b(should(?:n't)?|avoid|discouraged|prefer|recommended)\b", sentence, re.I
    ):
        return "SHOULD"
    if _IMPERATIVE.match(sentence):
        # 风格指南式祈使句（「Use X over Y」「Use X rather than mutating」）
        # 是规范句，但语力弱于 MUST，记 SHOULD（I7）
        return "SHOULD"
    return None


def _auto_max_rules(spec_dir: Path) -> int:
    """I7：预算随规范规模自适应——逐节轮转需 ≥ 节数才能覆盖全部章节
    （asvs 351 个需求节，cap 60 会在 V2 附近耗尽而漏掉 V5–V7 的 canonical 规则）。"""
    n_sections = len(parse_document(spec_dir))
    return max(60, min(n_sections, 400))


def extract_rules(
    spec_dir: Path,
    spec_id: str = "react19",
    max_rules: int | None = None,
    max_per_section: int = 3,
) -> list[RuleRecord]:  # noqa: F821
    from bench.harness.schemas import (
        RuleRecord,  # 局部导入避免与类型注解循环
        SourceSpan,
        Trigger,
    )

    if max_rules is None:
        max_rules = _auto_max_rules(spec_dir)

    rules: list[RuleRecord] = []
    seen_quotes: set[str] = set()

    # 先逐节收集候选（每节至多 max_per_section），再跨节轮转采选——
    # I7：ASVS 351 节 × 文档顺序收割会在 cap 内只覆盖前几章，canonical 规则
    # 散布 V1–V14；轮转保证每个章节都有确定性的代表进入候选集。
    # 候选来源 = 列表行（bullet 行自带边界，airbnb 式无句末标点的清单不粘连）
    # ∪ 句子切片；行优先（更精确），键去重。
    per_section: list[list[tuple[str, str, dict]]] = []
    for sec in parse_document(spec_dir):
        text = _strip_code(sec["text"])
        pieces = [*text.splitlines(), *_SENTENCE.split(text)]
        cands: list[tuple[str, str, dict]] = []
        seen_local: set[str] = set()
        for raw in pieces:
            sentence = _clean_sentence(raw)
            if len(sentence) < 25 or len(sentence) > 400:
                continue
            if "@@CODE@@" in sentence or "@@CODE@@" in raw:
                continue  # 跨代码块边界的合并句，引句不可能逐字
            if "`{" in sentence or "```" in raw or _is_table_row(sentence):
                continue  # 代码块/锚点/表格残片不是规范句
            level = _normative_level(sentence)
            if level is None:
                continue  # _normative_level 已含 must/should/verify/祈使四路判定
            key = sentence[:80]
            if key in seen_quotes or key in seen_local:
                continue
            seen_local.add(key)
            cands.append((level, sentence, sec))
            if len(cands) >= max_per_section:
                break
        if cands:
            per_section.append(cands)

    seq = 0
    rnd = 0
    while len(rules) < max_rules:
        added = False
        for cands in per_section:
            if len(rules) >= max_rules:
                break
            if rnd < len(cands):
                level, sentence, sec = cands[rnd]
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
                added = True
        if not added:
            break
        rnd += 1
    return rules


def _SENTENCE_was_normative(sentence: str) -> bool:
    return _NORMATIVE.search(sentence) is not None
