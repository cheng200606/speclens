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
}


def _derived_cues(rule: RuleRecord) -> list[str]:
    """从 assertion/quote 的英文 token 派生路由键。

    排序策略：驼峰/点分 token（reducerAction、promise.status——通常是 API 面）
    优先，其余按长度；过滤尾部标点与通用词黑名单；至多 3 个。
    """
    tokens: list[str] = []
    for text in (rule.assertion, rule.source_span.quote if rule.source_span else ""):
        for t in re.findall(r"[A-Za-z][A-Za-z0-9_.]{2,}", text or ""):
            t = t.strip("._")
            if len(t) >= 3 and t.lower() not in _GENERIC:
                tokens.append(t)
    tokens = sorted(set(tokens), key=lambda t: (not any(c.isupper() for c in t[1:]), "." not in t, -len(t)))
    return tokens[:3]


def _effective_cues(rule: RuleRecord) -> tuple[list[str], bool]:
    """(有效 cues, 是否全局)。显式 cues 优先；否则派生；派生为空则全局。"""
    if rule.trigger.ast_cues:
        return rule.trigger.ast_cues, False
    derived = _derived_cues(rule)
    return derived, not derived


def route_rules(rules: list[RuleRecord], code_text: str) -> list[RuleRecord]:
    """返回对该代码文本适用的规则子集。"""
    applicable: list[RuleRecord] = []
    for rule in rules:
        cues, is_global = _effective_cues(rule)
        if is_global or any(_cue_hit(cue, code_text) for cue in cues):
            applicable.append(rule)
    return applicable


def _cue_hit(cue: str, code_text: str) -> bool:
    if cue == "use":
        return re.search(r"\buse\(", code_text) is not None
    if cue == "useHook":
        # 任意 Hook 调用（useState/useEffect/useRef/...）——R-004 类规则的 API 面
        return re.search(r"\buse[A-Z]\w*\s*\(", code_text) is not None
    return re.search(rf"\b{re.escape(cue)}\b", code_text, re.I) is not None
