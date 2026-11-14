"""B3 纯静态检查基线（plan.md §2.4）：零 LLM、零 API、完全确定性。

定位：RQ2 的「静态检查」对照臂。用正则 / 行结构启发式实现 12 条冻结规则中
可静态近似的部分，产出与其它基线同构的 Finding（rule_ids 与冻结规则库同
命名空间，rule_match_rate 可解释）。

诚实边界（RQ3 素材）：
- R-005（手写乐观更新）无可靠静态特征，不实现 → 该规则恒漏检；
- R-007 只能识别 `use(fetch(...))` / `.then()` 内联创建 Promise 的强特征，
  `use(fetchUser(id))`（未缓存具名函数）静态不可区分 → 漏检；
- R-008 只能识别「用了 use(调用) 但全文无 <Suspense>」，边界归属（组件是否
  在边界内）静态不可判 → 部分漏检。
规则引句取自 bench/specs/react19/rules.yaml（人工冻结真值词汇表）——
静态检查器由规范编译而来是其定义使然，与 LLM 基线的「未见规范」前提不同，
论文表述时须注明。
"""

from __future__ import annotations

import re
from pathlib import Path

from bench.harness.schemas import Finding, FindingEvidence

BASELINE_ID = "b3_static"

_HOOK_CALL = re.compile(r"\b(use[A-Z]\w*|use)\s*\(")
_RETURN = re.compile(r"^\s*return\b|^\s*return\s*[\(\"\'`\w]")
_CONTROL = re.compile(
    r"^\s*(if\s*\(|else|for\s*\(|while\s*\(|switch\s*\(|try\s*\{|catch\s*\(|finally\s*\{)"
)
_EFFECT_SETUP = re.compile(
    r"setInterval|setTimeout|addEventListener|new\s+WebSocket|\.subscribe\(|requestAnimationFrame"
)
_INLINE_PROMISE = re.compile(r"\buse\s*\(\s*(fetch\s*\(|[\w.]+\s*\([^)]*\)\s*\.then\b)")
_PROMISE_STATUS = re.compile(r"\b\w+\.status\b|\bpromise\.value\b")
_DISPATCH_CALL = re.compile(r"\b(dispatch\w*|setOptimistic\w*|addOptimistic\w*)\s*\(")
_IMPURITY = re.compile(r"\bDate\.now\s*\(|\bMath\.random\s*\(")
_FORM_ONSUBMIT = re.compile(r"<form[^>]*onSubmit\s*=")
_USE_BROWSER = re.compile(r"\buse\s*\(\s*browser\b")
_INLINE_COMMENT = re.compile(r"(?<!:)//.*$")


def _strip_comments(lines: list[str]) -> list[str]:
    """去掉 // 注释（保留 https:// 等协议头）；块注释按行前缀近似处理。

    启发式匹配必须基于无注释文本：TS-024 的合规注释「不读取 promise.status」
    曾被 R-009 命中（I4 修）。
    """
    out = []
    in_block = False
    for line in lines:
        if in_block:
            line = re.sub(r"^.*?\*/", "", line)
            if "*/" not in line:
                out.append("")
                continue
            in_block = False
        if "/*" in line and "*/" not in line.split("/*", 1)[1]:
            line = line.split("/*", 1)[0]
            in_block = True
        line = _INLINE_COMMENT.sub("", line)
        out.append(line)
    return out

_SPEC_DIR = Path(__file__).resolve().parent.parent / "bench" / "specs" / "react19"
_QUOTES: dict[str, str] | None = None


def _quotes() -> dict[str, str]:
    global _QUOTES
    if _QUOTES is None:
        from engine.rule_bank import build_rules

        rules, _ = build_rules(_SPEC_DIR, "canonical")
        _QUOTES = {r.id: (r.source_span.quote if r.source_span else "") for r in rules}
    return _QUOTES


def _finding(
    file: str, line: int, rule_id: str, message: str, case_id: str
) -> Finding:
    return Finding(
        case_id=case_id,
        file=file,
        line_start=line,
        line_end=line,
        rule_ids=[rule_id],
        severity="warning",
        message=message,
        evidence=FindingEvidence(
            rule_quote=_quotes().get(rule_id, ""),
            explanation=f"B3 static heuristic: {message}",
        ),
    )


def _match_span(code: str, start_idx: int) -> int:
    """返回从 start_idx 处的 '(' 起到配对 ')' 的下标；不配对则返回 -1。"""
    depth = 0
    for i in range(start_idx, len(code)):
        if code[i] == "(":
            depth += 1
        elif code[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _effect_bodies(lines: list[str]) -> list[tuple[int, int]]:
    """定位 useEffect(...) 回调体的 (起始行, 结束行)（1-based，闭区间）。"""
    spans: list[tuple[int, int]] = []
    joined = "\n".join(lines)
    for m in re.finditer(r"useEffect\s*\(", joined):
        open_idx = m.end() - 1
        close = _match_span(joined, open_idx)
        if close == -1:
            continue
        start_line = joined.count("\n", 0, m.start()) + 1
        end_line = joined.count("\n", 0, close) + 1
        spans.append((start_line, end_line))
    return spans


def _check_r004(lines: list[str], file: str, case_id: str) -> list[Finding]:
    out: list[Finding] = []
    for i, line in enumerate(lines, 1):
        if not _HOOK_CALL.search(line):
            continue
        indent = len(line) - len(line.lstrip())
        # Hook 所在函数的起点（更浅缩进的 function 头），return 只统计同函数内的
        func_start = 1
        for j in range(i - 1, 0, -1):
            prev = lines[j - 1]
            prev_indent = len(prev) - len(prev.lstrip())
            if prev.strip() and prev_indent < indent and re.search(
                r"(?:export\s+)?(?:default\s+)?function\s+\w+|const\s+\w+\s*=\s*[\w(\"\']", prev
            ):
                func_start = j
                break
        same_func_returns = [
            no for no in range(func_start, i) if _RETURN.match(lines[no - 1])
        ]
        # 语义：Hook 必须在所有 early return 之前——同函数内 Hook 之前存在任何
        # return（无论缩进，包括 if 块内）即意味着该 Hook 可能被跳过（R-004）。
        # 此前只比同缩进 return，漏掉 TS-037（return 在 if 块内、Hook 在外层）。
        if same_func_returns:
            out.append(
                _finding(file, i, "R-004", "Hook called after an early return", case_id)
            )
            continue
        # 位于控制流块内（函数起点之后、Hook 之前存在更浅缩进的控制流头）
        for j in range(i - 1, func_start - 1, -1):
            prev = lines[j - 1]
            prev_indent = len(prev) - len(prev.lstrip())
            if prev.strip() and prev_indent < indent and _CONTROL.match(prev):
                out.append(
                    _finding(
                        file, i, "R-004", "Hook call inside a control-flow block", case_id
                    )
                )
                break
    return out


def _check_effects(
    lines: list[str], file: str, case_id: str
) -> list[Finding]:
    out: list[Finding] = []
    for start, end in _effect_bodies(lines):
        body = "\n".join(lines[start - 1 : end])
        if re.search(r"fetch\s*\(", body):
            out.append(
                _finding(
                    file, start, "R-001", "data fetching inside useEffect", case_id
                )
            )
        if _EFFECT_SETUP.search(body) and not re.search(
            r"return\s*(\(|function|\w+\s*=>)", body
        ):
            out.append(
                _finding(
                    file,
                    start,
                    "R-003",
                    "Effect establishes subscription/timer without cleanup",
                    case_id,
                )
            )
    return out


def _check_use_call(
    lines: list[str], file: str, case_id: str
) -> list[Finding]:
    out: list[Finding] = []
    for i, line in enumerate(lines, 1):
        if _PROMISE_STATUS.search(line):
            out.append(
                _finding(
                    file, i, "R-009", "reads promise.status/value to bypass use()", case_id
                )
            )
    return out


def _check_inline_promise(
    lines: list[str], file: str, case_id: str
) -> list[Finding]:
    out: list[Finding] = []
    for i, line in enumerate(lines, 1):
        if _INLINE_PROMISE.search(line):
            out.append(
                _finding(
                    file,
                    i,
                    "R-007",
                    "Promise created inline in render and passed to use()",
                    case_id,
                )
            )
    return out


def _check_action_context(
    lines: list[str], file: str, case_id: str
) -> list[Finding]:
    out: list[Finding] = []
    for i, line in enumerate(lines, 1):
        m = _DISPATCH_CALL.search(line)
        if not m:
            continue
        window = "\n".join(lines[max(0, i - 6) : min(len(lines), i + 5)])
        if "startTransition" in window or "useTransition" in window:
            continue
        # Action prop 约定：函数名以 Action 结尾时视为已处于 Action 作用域
        for j in range(i - 1, max(0, i - 15), -1):
            fm = re.search(r"(?:async\s+)?function\s+(\w+)", lines[j - 1])
            if fm:
                if fm.group(1).endswith(("Action", "action")):
                    break
                rule_id = "R-010" if m.group(1).startswith("set") else "R-011"
                out.append(
                    _finding(
                        file,
                        i,
                        rule_id,
                        f"{m.group(1)} called outside an Action/startTransition",
                        case_id,
                    )
                )
                break
    return out


def _check_use_context(
    lines: list[str], file: str, case_id: str
) -> list[Finding]:
    """R-006：裸 use( 必须位于组件（大写开头）或 Hook（use 前缀）内。"""
    out: list[Finding] = []
    for i, line in enumerate(lines, 1):
        if not re.search(r"(?<![\w.])use\s*\(", line):
            continue
        for j in range(i - 1, 0, -1):
            prev = lines[j - 1]
            fm = re.search(r"(?:export\s+)?(?:default\s+)?function\s+(\w+)", prev)
            if not fm:
                fm = re.search(r"const\s+(\w+)\s*=", prev)
            if fm:
                name = fm.group(1)
                if not (name.startswith("use") or name[:1].isupper()):
                    out.append(
                        _finding(
                            file,
                            i,
                            "R-006",
                            f"use() inside plain function {name} (not a Component/Hook)",
                            case_id,
                        )
                    )
                break
    return out


def _check_purity(
    lines: list[str], file: str, case_id: str
) -> list[Finding]:
    out: list[Finding] = []
    joined = "\n".join(lines)
    for m in re.finditer(r"useOptimistic\s*\(", joined):
        close = _match_span(joined, m.end() - 1)
        if close == -1:
            continue
        span = joined[m.end() : close]
        if _IMPURITY.search(span) or re.search(r"\w+\.push\s*\(", span):
            line_no = joined.count("\n", 0, m.end()) + 1
            out.append(
                _finding(
                    file,
                    line_no,
                    "R-012",
                    "useOptimistic updater/reducer is impure",
                    case_id,
                )
            )
    return out


def _check_forms_and_suspense(
    lines: list[str], file: str, case_id: str
) -> list[Finding]:
    out: list[Finding] = []
    joined = "\n".join(lines)
    if _FORM_ONSUBMIT.search(joined):
        line_no = next(
            (
                i
                for i, line in enumerate(lines, 1)
                if _FORM_ONSUBMIT.search(line)
            ),
            1,
        )
        out.append(
            _finding(
                file, line_no, "R-002", "form handled via onSubmit instead of Actions", case_id
            )
        )
    if _USE_BROWSER.search(joined) and "<Suspense" not in joined:
        line_no = next(
            (i for i, line in enumerate(lines, 1) if _USE_BROWSER.search(line)), 1
        )
        out.append(
            _finding(
                file,
                line_no,
                "R-008",
                "use(call) outside any <Suspense> boundary (server rendering)",
                case_id,
            )
        )
    return out


def check_file(code: str, file: str, case_id: str) -> list[Finding]:
    lines = _strip_comments(code.splitlines())
    return (
        _check_r004(lines, file, case_id)
        + _check_effects(lines, file, case_id)
        + _check_use_call(lines, file, case_id)
        + _check_use_context(lines, file, case_id)
        + _check_inline_promise(lines, file, case_id)
        + _check_action_context(lines, file, case_id)
        + _check_purity(lines, file, case_id)
        + _check_forms_and_suspense(lines, file, case_id)
    )


def predict_case(case, adapter=None) -> list[Finding]:
    findings: list[Finding] = []
    for name in case.meta.files:
        findings.extend(check_file(case.read_file(name), name, case.meta.case_id))
    return findings
