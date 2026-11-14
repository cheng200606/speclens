"""规则验证三道关（plan.md §2.2，本项目方法核心）：

1. **grounding**：规则断言 ↔ 规范原文的双向忠实性校验（确定性打分：
   引句必须在快照中逐字存在 + 断言-引句内容词重合 + 等级一致性）。
2. **executability**：正反例自洽测试——为规则合成正/反例代码，用与审查
   完全相同的入口（engine.review.check_code_against_rule）自审，反例须被
   检出且引用本规则、正例须零 finding，两条件同时成立才 pass。需要 LLM；
   无 adapter 时保持 pending（不伪造结果）。
3. **conflict**：规则间冲突检测（同线索 + 极性相反；断言重复）。

低分/冲突规则进入人工复核队列。usage:

    uv run python -m engine.verify --spec react19
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from pydantic import BaseModel

from bench.harness.schemas import RuleRecord
from bench.harness.spec_text import assemble_spec_text

# ---------- 门 1：grounding ----------

_MUST_KW = re.compile(r"\b(must|never|do not|don't|cannot|required)\b", re.I)
_SHOULD_KW = re.compile(r"\bshould\b", re.I)
_SOFT_KW = re.compile(r"\b(avoid|discouraged|prefer|recommended)\b", re.I)
_CJK = re.compile(r"[\u4e00-\u9fff]")
_STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "that", "this", "it", "is", "are", "be", "as", "by", "not", "you", "your",
    "from", "will", "can", "if", "when", "then", "than", "so", "its", "their",
}


_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_BULLET = re.compile(r"^\s*[*\-+]\s+", re.M)
# 提取器把跨列表项的多句引句用 "- " 拼接（"system. - It should..."）；
# 规范文本侧列表符在行首已被 _BULLET 剥离，引句侧的句中列表符必须同样剥离，
# 否则 quote_in_spec 恒 False（I4：此前 X-018/R-003/X-028/X-033 四条被误杀的直接原因）。
_MID_BULLET = re.compile(r"([.!?;:])\s+[-*+]\s+")


def _norm(text: str) -> str:
    """规范化：拆 markdown 链接外壳、去列表符/加粗符、压空白、小写。

    断言经过提取清洗（链接已拆），快照原文没有——两侧必须同构才能逐字比对。
    """
    text = _MD_LINK.sub(r"\1", text)
    text = _BULLET.sub("", text)
    text = _MID_BULLET.sub(r"\1 ", text)
    return re.sub(r"\s+", " ", text.replace("*", "")).strip().lower()


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_.]{2,}", text.lower())
    return {w for w in words if w not in _STOP}


def _level_consistent(level: str, quote: str) -> tuple[bool, str | None]:
    """引句的规范性措辞与声明等级是否一致；引句两者兼备或皆无时视为中性。

    I4 修订（docs/STATUS-I4.md D1）：
    - "should" 是 React 文档的教程式指令语气（"It should return a cleanup function"），
      冻结规则据此判 MUST 属标注人裁量 —— 容忍并记 note，不再扣分
      （此前 R-003 因该项 + 跨语言零重叠被门 1 误杀）。
    - 软建议词（prefer/avoid/discouraged/recommended）上声明 MUST 仍判不一致
      （过度声明，真会放大误报）；硬强制句上声明 SHOULD 判不一致（弱化声明，漏检方向）。
    """
    has_must = bool(_MUST_KW.search(quote))
    has_should = bool(_SHOULD_KW.search(quote))
    has_soft = bool(_SOFT_KW.search(quote))
    if has_must and not (has_should or has_soft):
        return level == "MUST", None if level == "MUST" else "under-claim: hard-normative quote"
    if has_soft and not (has_must or has_should):
        if level == "MUST":
            return False, "over-claim: soft-recommendation quote declared MUST"
        return True, None
    if has_should and not (has_must or has_soft):
        if level == "MUST":
            return True, "tutorial-should: quote uses should-wording, MUST declared by annotation"
        return True, None
    return True, None


def grounding_score(rule: RuleRecord, spec_text_norm: str) -> tuple[float, dict]:
    """返回 (score∈[0,1], 分项明细)。引句必须在快照中逐字存在（权重 0.5）。

    I4 修订：断言为中文而引句为英文时（canonical 冻结规则皆如此），
    词面重叠无定义——原实现按 0 计入并叠加等级扣分，把 R-003 压到 0.5 误杀。
    跨语言时权重重归一为 quote_in_spec 0.5 + level 0.5；等级张力降级为 note
    （仅软建议词 + MUST 声明的过度声明仍判 False，会在明细中暴露）。
    """
    quote_norm = _norm(rule.source_span.quote)
    assert_norm = _norm(rule.assertion)
    quote_in_spec = quote_norm in spec_text_norm
    assert_words = _content_words(assert_norm)
    quote_words = _content_words(quote_norm)
    level_ok, level_note = _level_consistent(rule.level, rule.source_span.quote)
    cross_language = bool(_CJK.search(assert_norm)) and bool(quote_words)
    if cross_language:
        overlap = None
        score = (1.0 if quote_in_spec else 0.0) * 0.5 + (1.0 if level_ok else 0.0) * 0.5
    else:
        overlap = (
            len(assert_words & quote_words) / max(1, len(assert_words | quote_words))
            if assert_words or quote_words
            else 0.0
        )
        score = (
            (1.0 if quote_in_spec else 0.0) * 0.5
            + overlap * 0.3
            + (1.0 if level_ok else 0.0) * 0.2
        )
    detail = {
        "quote_in_spec": quote_in_spec,
        "content_overlap": round(overlap, 3) if overlap is not None else None,
        "level_consistent": level_ok,
        "cross_language": cross_language,
    }
    if level_note:
        detail["level_note"] = level_note
    return round(score, 3), detail


# ---------- 门 2：executability ----------

class RuleExamples(BaseModel):
    """LLM 为规则合成的正/反例代码。"""

    pos_example: str
    neg_example: str


_SYNTH_SYSTEM = (
    "You are creating test snippets for a code-review rule. "
    'Respond ONLY with JSON: {"pos_example": "<compliant code>", '
    '"neg_example": "<code that clearly violates the rule>"}. '
    "Keep each snippet under 15 lines, TypeScript/TSX."
)


def _synth_prompt(rule: RuleRecord) -> str:
    return (
        f"Rule (level {rule.level}): {rule.assertion}\n"
        f"Specification text: \"{rule.source_span.quote}\"\n"
        "Provide a compliant snippet (pos_example) and a clearly violating "
        "snippet (neg_example)."
    )


class GateUnavailable(Exception):
    """门 2 无法执行（如 adapter 不支持正反例合成）——门结果记 pending，非 fail。"""


def _synthesize_examples(rule: RuleRecord, adapter) -> tuple[str, str]:
    from pydantic import ValidationError

    try:
        out = adapter.complete_json(
            system=_SYNTH_SYSTEM,
            user=_synth_prompt(rule),
            schema=RuleExamples,
            meta={"rule_id": rule.id, "phase": "synthesize"},
        )
    except ValidationError as exc:
        # adapter 不产出 RuleExamples 形状 => 门不可用，而非规则自洽失败
        raise GateUnavailable(f"synthesis schema mismatch: {exc}") from exc
    return out.pos_example, out.neg_example


def executability_test_detail(rule: RuleRecord, adapter) -> tuple[str, dict]:
    """门 2 带明细：哪条腿失败（neg_ok / pos_ok）与自合成例的命中情况。

    I3 可诊断性（docs/STATUS-I2.md §3-1）：此前 R-011 被门 2 误杀却无从归因。
    """
    from engine.review import check_code_against_rule  # 局部导入避免环

    pos, neg = _synthesize_examples(rule, adapter)
    neg_findings = check_code_against_rule(rule, neg, adapter)
    pos_findings = check_code_against_rule(rule, pos, adapter)
    neg_ok = any(rule.id in f.rule_ids for f in neg_findings)
    pos_ok = len(pos_findings) == 0
    state = "pass" if (neg_ok and pos_ok) else "fail"
    detail = {
        "neg_ok": neg_ok,
        "pos_ok": pos_ok,
        "neg_findings": [f.model_dump() for f in neg_findings],
        "pos_findings": [f.model_dump() for f in pos_findings],
    }
    return state, detail


def executability_test(rule: RuleRecord, adapter) -> str:
    """自洽测试：反例须被检出且引用本规则，正例须零 finding。

    无 adapter（离线）时返回 "pending"，不伪造结果。
    """
    state, _detail = executability_test_detail(rule, adapter)
    return state


# ---------- 门 3：conflict ----------


class ContradictionVerdict(BaseModel):
    contradict: bool


_CONTRA_SYSTEM = (
    "You are checking whether two specification-derived rules contradict each "
    "other (i.e., cannot both be satisfied at the same time for the same code). "
    'Respond ONLY with JSON: {"contradict": true|false}.'
)


def _contra_prompt(a: RuleRecord, b: RuleRecord) -> str:
    return (
        f"Rule A (level {a.level}): {a.assertion}\n"
        f"Rule B (level {b.level}): {b.assertion}\n"
        "Do A and B contradict each other?"
    )


def detect_conflicts(
    rules: list[RuleRecord],
    adapter=None,
    max_pairs: int = 60,
    stats: dict | None = None,
) -> dict[str, list[str]]:
    """规则间冲突检测（双向记录）。

    - 离线（无 adapter）：只报**断言重复**（确定性、零误报）。
    - 有 adapter：对共享线索的规则对追加 LLM 语义矛盾判定，**LLM 调用对数严格
      受 max_pairs 限制**。原实现用 `len(conflicts) >= max_pairs` 收尾，只在已经
      发现冲突时才生效，44 条规则真实接入会退化成最多 946 次调用（S0-4）。
      「use 必须在组件内调用」vs「use 不能在 try-catch 内调用」这类极性相反
      但语义相容的规则对，只有语义判定才能排除——故极性启发式不作为离线依据。
    - stats 可选传入一个 dict，回填 `n_pairs_checked` / `n_pairs_skipped_by_cap`。
    """
    conflicts: dict[str, list[str]] = {}
    n_checked = 0
    n_skipped = 0
    for i, a in enumerate(rules):
        for b in rules[i + 1 :]:
            duplicate = _norm(a.assertion) == _norm(b.assertion)
            if duplicate:
                conflicts.setdefault(a.id, []).append(f"{b.id}:duplicate")
                conflicts.setdefault(b.id, []).append(f"{a.id}:duplicate")
                continue
            if adapter is None:
                continue
            if not (set(a.trigger.ast_cues) & set(b.trigger.ast_cues)):
                continue
            if n_checked >= max_pairs:
                n_skipped += 1
                continue
            n_checked += 1
            from pydantic import ValidationError

            try:
                verdict: ContradictionVerdict = adapter.complete_json(
                    system=_CONTRA_SYSTEM,
                    user=_contra_prompt(a, b),
                    schema=ContradictionVerdict,
                    meta={"rule_id": a.id, "other": b.id, "phase": "contradiction"},
                )
            except ValidationError:
                continue  # adapter 不支持该判定形态 => 此对跳过，不伪造冲突
            if verdict.contradict:
                conflicts.setdefault(a.id, []).append(f"{b.id}:llm-contradict")
                conflicts.setdefault(b.id, []).append(f"{a.id}:llm-contradict")
    if stats is not None:
        stats.update(
            {
                "n_pairs_checked": n_checked,
                "n_pairs_skipped_by_cap": n_skipped,
                "max_pairs": max_pairs,
                "within_cap": n_checked <= max_pairs,
            }
        )
    return conflicts


# ---------- 汇总 ----------

GROUNDING_REVIEW_THRESHOLD = 0.6


def verify_rules(
    rules: list[RuleRecord],
    spec_dir: Path,
    adapter=None,
    spec_text: str | None = None,
) -> tuple[list[RuleRecord], dict]:
    """跑三道关，回填每条规则的 verification 字段，返回 (规则, 汇总报告)。

    adapter=None 时门 2 保持 pending（离线可复现）；adapter 存在时走
    LLM 合成 + 自审。
    """
    if spec_text is None:
        spec_text, _used = assemble_spec_text(spec_dir)
    spec_text_norm = _norm(spec_text)

    conflict_stats: dict = {}
    conflicts = detect_conflicts(rules, adapter=adapter, stats=conflict_stats)
    exec_details: dict[str, dict] = {}
    flagged: list[dict] = []
    for rule in rules:
        score, detail = grounding_score(rule, spec_text_norm)
        rule.verification.grounding = score
        if adapter is not None:
            try:
                state, exec_detail = executability_test_detail(rule, adapter)
                rule.verification.exec_test = state
                exec_details[rule.id] = exec_detail
            except GateUnavailable as exc:
                # 门不可用（如 mock adapter 不支持合成）：保持 pending，不判死
                detail["exec_unavailable"] = str(exc)[:200]
            except Exception as exc:  # 自审判定失败等真实错误
                rule.verification.exec_test = "fail"
                detail["exec_error"] = str(exc)[:200]
        rule.verification.conflicts = conflicts.get(rule.id, [])

        reasons: list[str] = []
        if score < GROUNDING_REVIEW_THRESHOLD:
            reasons.append(f"grounding<{GROUNDING_REVIEW_THRESHOLD}")
        if "exec_error" in detail:
            reasons.append("exec-error")
        elif rule.verification.exec_test == "fail":
            reasons.append("exec-fail")
        if rule.verification.conflicts:
            reasons.append("conflicts")
        if reasons:
            flagged.append({"id": rule.id, "reasons": reasons, "detail": detail})

    report = {
        "n_rules": len(rules),
        "n_conflict_rules": sum(1 for r in rules if r.verification.conflicts),
        "n_flagged": len(flagged),
        "flagged_for_review": flagged,
        "gate2_llm": adapter is not None,
        "gate2_exec_counts": {
            state: sum(1 for r in rules if r.verification.exec_test == state)
            for state in ("pass", "fail", "pending")
        },
        "gate3_stats": conflict_stats,
        "exec_details": exec_details,
        "grounding_mean": round(
            sum(r.verification.grounding or 0.0 for r in rules) / max(1, len(rules)), 3
        ),
    }
    return rules, report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SpecLens 规则验证三道关")
    parser.add_argument("--spec", required=True, help="spec_id，如 react19")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default=None, help="报告 JSON 输出路径")
    args = parser.parse_args(argv)

    repo = Path(args.repo_root)
    spec_dir = repo / "bench" / "specs" / args.spec
    from engine.extract import extract_rules

    rules = extract_rules(spec_dir, spec_id=args.spec)
    rules, report = verify_rules(rules, spec_dir)

    payload = {"report": report, "rules": [r.model_dump() for r in rules]}
    text = __import__("json").dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"[speclens] verification report -> {args.output}")
    print(__import__("json").dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
