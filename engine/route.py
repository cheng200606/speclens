"""规则路由（M-lite 确定性版）：规则找代码，而非代码检索规则。

每条规则的 trigger.ast_cues 与代码文本做命中判断。
I5 路由 v2：**无 cues 的规则不再全局适用**——从 assertion/quote 的英文内容词
自动派生路由键（仓库级实验中 25/44 条规则无 cues，全局适用会使 M 路径成本
随文件数爆炸，docs/STATUS-I5.md D1）。派生规则：取 assertion 的英文内容词中
最长的至多 3 个；断言无英文内容词时回退全局（保持保守，宁可多审不漏审）。
M2 仍将升级为 AST 特征（tree-sitter）+ 章节级路由。
"""

from __future__ import annotations

import re
from collections import Counter

from bench.harness.schemas import RuleRecord

_GENERIC = {
    # TS/JS 与文档叙述中的通用词——作为路由键会命中几乎所有源码文件
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "that", "this", "it", "is", "are", "be", "as", "by", "not", "you", "your",
    "from", "will", "can", "if", "when", "then", "than", "so", "its", "their",
    "must", "should", "may", "instead", "always", "never", "called", "inside",
    "function", "return", "returns", "value", "values", "set", "get", "state",
    "component", "components", "render", "rendering", "rendered", "props",
    "data", "code", "hooks", "hook", "effect", "effects", "dependency",
    "dependencies", "conditional", "statement", "statements", "type", "types",
    "export", "import", "const", "default", "string", "number", "object",
    "array", "boolean", "whatever", "things", "thing", "update", "updates",
    "updating", "call", "calls", "called", "using", "used", "use", "new",
    "each", "both", "some", "only", "also", "because", "these", "those",
    "should", "would", "could", "current", "argument", "arguments",
    # I8：叙述性 prose 高频词（ASVS 需求描述风格）——作 cue 会泛命中或挤占前 3
    "application", "applications", "verify", "implementation", "implemented",
    "designed", "ensures", "ensure", "including", "uses", "based", "user",
    "users", "protection", "security", "access",
}

# 规范内部需求编号（V6.2.9 / 6.2.9）——只存在于规范文本，永不出现在被审代码；
# 作首位 cue 会让全部规则路由 0 命中（I8 诊断：asvs 12 条 matched 全灭的直接原因）。
_SPEC_ID_TOKEN = re.compile(r"^V?\d+(?:\.\d+)*$")


def _derived_cues(rule: RuleRecord) -> list[str]:
    """从 assertion/quote 的英文 token 派生路由键。

    排序策略：驼峰/点分 token（reducerAction、promise.status——通常是 API 面）
    优先，其余按长度；过滤尾部标点、通用词黑名单与规范需求编号（I8）；至多 3 个。
    """
    tokens: list[str] = []
    for text in (rule.assertion, rule.source_span.quote if rule.source_span else ""):
        for t in re.findall(r"[A-Za-z][A-Za-z0-9_.]{2,}", text or ""):
            t = t.strip("._")
            if len(t) >= 3 and t.lower() not in _GENERIC and not _SPEC_ID_TOKEN.match(t):
                tokens.append(t)
    tokens = sorted(set(tokens), key=lambda t: (not any(c.isupper() for c in t[1:]), "." not in t, -len(t)))
    return tokens[:3]


def _effective_cues(rule: RuleRecord) -> tuple[list[str], bool]:
    """(有效 cues, 是否全局)。显式 cues 优先；否则派生；派生为空则全局。"""
    if rule.trigger.ast_cues:
        return rule.trigger.ast_cues, False
    derived = _derived_cues(rule)
    return derived, not derived


_IDENT_PARTS = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_CAMEL_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def _code_tokens(code_text: str) -> set[str]:
    """代码标识符 → 小写词元集合：按 `_` 切分 + 驼峰切分（get_password →
    {get, password}；HTTPException → {http, exception}）。cue 与词元精确
    比对（含复数折叠），规避子串误命中。"""
    tokens: set[str] = set()
    for ident in _IDENT_PARTS.findall(code_text):
        for part in _CAMEL_SPLIT.split(ident):
            part = part.lower().strip("_")
            if len(part) >= 3:
                tokens.add(part)
    return tokens


def _cue_variants(cue: str) -> set[str]:
    """cue 的形态变体：passwords → {passwords, password}；TOTPs → {totps, totp}。"""
    m = re.match(r"^(.+?)(ies|es|s)$", cue)
    if m and len(m.group(1)) >= 4 and not cue.endswith("ss"):
        base = m.group(1)
        return {cue.lower(), base.lower()}
    return {cue.lower()}


def route_rules(
    rules: list[RuleRecord], code_text: str, max_per_file: int = 30
) -> list[RuleRecord]:
    """返回对该代码文本适用的规则子集。

    I8 成本闸门 + 特异性排名：命中 = cue（含复数折叠）∈ 代码词元集。
    排序键 = 命中 cue 的库内文档频率（携带该 cue 的规则数——稀有 cue 高特异性）
    升序、命中数降序；每文件至多 max_per_file 条（泛命中洪泛的确定性上限；
    react19 词元精确匹配下 3-15 条/文件不受影响）。
    """
    tokens = _code_tokens(code_text)
    cue_df: Counter[str] = Counter()
    for rule in rules:
        for cue in set(_effective_cues(rule)[0]):
            cue_df[cue] += 1

    matched: list[tuple[int, int, int, int, RuleRecord]] = []
    synthesized: list[tuple[int, int, int, int, RuleRecord]] = []
    for idx, rule in enumerate(rules):
        cues, is_global = _effective_cues(rule)
        is_matched = not rule.id.startswith("X-")
        if is_global:
            # 对齐规则全局兜底（I8 不对称路由）：matched 规则是被测方法的
            # 核心产出且数量有界（≤12/规范），全局配对保证「必须使用 X」型
            # 规则（违规文件缺少 X 词元，词汇路由原理性盲区）可达审查；
            # 溯源信息不涉及标注（无泄漏）。X-规则无兜底——成本闸门。
            if is_matched:
                matched.append((-1, 0, 0, idx, rule))
            else:
                synthesized.append((0, 0, 0, idx, rule))
            continue
        hits = [
            cue
            for cue in cues
            if cue in ("use", "useHook")
            and _cue_hit(cue, code_text)
            or _cue_variants(cue) & tokens
        ]
        if not hits:
            if is_matched:
                matched.append((-1, 0, 0, idx, rule))  # cue 未命中仍全局配对
            continue
        best_df = min(cue_df[c] for c in hits)
        bucket = matched if is_matched else synthesized
        bucket.append((best_df, -len(hits), -max(len(h) for h in hits), idx, rule))
    matched.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
    synthesized.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
    return [r for *_, r in (matched + synthesized)][:max_per_file]


def _cue_hit(cue: str, code_text: str) -> bool:
    if cue == "use":
        return re.search(r"\buse\(", code_text) is not None
    if cue == "useHook":
        # 任意 Hook 调用（useState/useEffect/useRef/...）——R-004 类规则的 API 面
        return re.search(r"\buse[A-Z]\w*\s*\(", code_text) is not None
    # I8 形态折叠：规范用复数（passwords/administrators/TOTPs），代码用单数
    # （password/administrator/TOTP）——词尾 s/es/ies 可选化，词边界保留。
    # 纯后缀可选化不扩大命中面（base 前缀更长或等长，误命中风险可忽略）。
    m = re.match(r"^(.+?)(ies|es|s)$", cue)
    if m and len(m.group(1)) >= 4 and not cue.endswith("ss"):
        base = m.group(1)
        tail = cue[len(base):]
        alt = "(?:ies|y)" if tail == "ies" else re.escape(tail)
        return _stem_search(base, alt, code_text) is not None
    return _stem_search(cue, "", code_text) is not None


def _stem_search(base: str, tail: str, code_text: str) -> bool:
    """snake_case 友好的 cue 命中：两端禁止紧邻字母（snake/kebab 词内不算），
    但允许 `_`/`-` 相邻——`password_changed_at`、`get_password` 均可命中
    （安全类代码标识符以 snake_case 为主，\b 会全部漏掉，I8 诊断）。"""
    return re.search(rf"(?<![A-Za-z]){re.escape(base)}{tail}(?![A-Za-z])", code_text, re.I) is not None
