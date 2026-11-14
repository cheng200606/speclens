"""M-verified：完整方法 M（plan.md §2.2）。

extract / rule_bank → verify（三道关，真正带 adapter 执行）→ 过滤不合格规则
→ route → review → trace（证据链回填）→ deduplicate/aggregate（聚合去重）。

与 M-lite 的差异即消融对象：verify 三道关 + 证据链 + 聚合。

排除策略（I3 起 fail-open，对齐 plan.md §2.2「低分规则进入人工复核队列」）：
- **excluded（移出规则库）**：仅 grounding < 0.6（确定性门 1，可离线复现）。
- **review_flags（保留但标记待复核）**：exec_test == "fail"（LLM 自审，
  实测 8/44 误杀率——R-011 被 fail 后 TS-031/040 漏检，docs/STATUS-I2.md §3-1）
  与 conflicts（语义矛盾判定同为 LLM 产物）。二者是诊断信号，不是删除依据；
  逐规则结果归档于 run 目录 verify_report.json。

I1 修订（docs/STATUS-I1.md P0-1 / P0-3）：
- 规则来源由 `rules_source` 显式配置（默认 synthesized 以兼容既有离线测试；
  litmus 配置用 aligned，保证 finding 的 rule_id 与标注真值同命名空间）。
- `verify_rules` **传入 adapter**：此前门 2 恒 pending、门 3 只做重复检测，
  所谓「完整方法」名不副实。现在门不可用仍记 pending（不伪造结果），
  可用时门 2 走正反例自审、门 3 走语义矛盾判定（调用数受 max_pairs 限制）。
- 验证前深拷贝规则，避免 lru_cache 中的规则对象被跨 run 修改。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from engine.rule_bank import build_rules, rules_source_from
from engine.verify import GROUNDING_REVIEW_THRESHOLD, verify_rules

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding, RuleRecord

BASELINE_ID = "m_verified"

# 验证关快照（I3 可诊断性）：key = (spec_dir_str, rules_source)。
# lru_cache 保证验证每 run 只跑一次；快照供 runner 归档 verify_report.json，
# 否则门 2/3 过滤了哪些规则无从归因（docs/STATUS-I2.md §3-1）。
_LAST_VERIFY: dict[tuple[str, str], dict] = {}


@lru_cache(maxsize=8)
def _verified_rules(
    spec_dir_str: str, rules_source: str = "synthesized", adapter=None
) -> tuple:
    rules, _diag = build_rules(Path(spec_dir_str), rules_source)
    rules = [r.model_copy(deep=True) for r in rules]
    verified, report = verify_rules(rules, Path(spec_dir_str), adapter=adapter)
    _LAST_VERIFY[(str(Path(spec_dir_str).resolve()), rules_source)] = _verify_snapshot(
        verified, report
    )
    return tuple(verified)


def verify_report(spec_dir_str: str, rules_source: str = "synthesized") -> dict | None:
    """最近一次验证关的逐规则快照；run 结束后由 runner 归档为 verify_report.json。"""
    return _LAST_VERIFY.get((str(Path(spec_dir_str).resolve()), rules_source))


def _verify_snapshot(verified: list[RuleRecord], report: dict) -> dict:
    per_rule = []
    for r in verified:
        v = r.verification
        per_rule.append(
            {
                "id": r.id,
                "synthesis_id": r.synthesis_id,
                "level": r.level,
                "grounding": v.grounding,
                "exec_test": v.exec_test,
                "conflicts": list(v.conflicts or []),
                "excluded": _excluded(r),
                "exclusion_reasons": _exclusion_reasons(r),
                "review_flags": _review_flags(r),
            }
        )
    reason_counts: dict[str, int] = {}
    flag_counts: dict[str, int] = {}
    for x in per_rule:
        for reason in x["exclusion_reasons"]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        for flag in x["review_flags"]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    return {
        "policy": "fail-open",
        "n_rules": len(per_rule),
        "n_kept": sum(1 for x in per_rule if not x["excluded"]),
        "n_excluded": len(per_rule) - sum(1 for x in per_rule if not x["excluded"]),
        "exclusion_reason_counts": reason_counts,
        "review_flag_counts": flag_counts,
        "rules": per_rule,
        "verify_summary": report,
    }


def _exclusion_reasons(rule: RuleRecord) -> list[str]:
    """确定性排除：仅门 1（grounding）。门 2/3 是 LLM 产物，误杀不排除，只标记。"""
    v = rule.verification
    reasons: list[str] = []
    if v.grounding is not None and v.grounding < GROUNDING_REVIEW_THRESHOLD:
        reasons.append(f"grounding<{GROUNDING_REVIEW_THRESHOLD}")
    return reasons


def _review_flags(rule: RuleRecord) -> list[str]:
    """保留但标记待人工复核的信号（plan.md §2.2 人工复核队列）。"""
    v = rule.verification
    flags: list[str] = []
    if v.exec_test == "fail":
        flags.append("exec-fail")
    if v.conflicts:
        flags.append("conflicts")
    return flags


def _excluded(rule: RuleRecord) -> bool:
    return bool(_exclusion_reasons(rule))


def _spec_dir_for_case(case: Case) -> Path:
    return case.root.parents[2] / "specs" / case.root.parent.name


def predict_case(case: Case, adapter: ModelAdapter) -> list[Finding]:
    from engine.review import review_code
    from engine.trace import aggregate

    spec_dir = _spec_dir_for_case(case)
    source = rules_source_from(adapter)
    verified = _verified_rules(str(spec_dir.resolve()), source, adapter)
    rules = [r.model_copy(deep=True) for r in verified if not _excluded(r)]
    findings = review_code(case, rules, adapter)
    return aggregate(findings, rules)
