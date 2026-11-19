"""I9① 路由 v4 离线诊断：matched 全局配对的相关度预算化（零 API）。

背景：I8 不对称路由（matched 规则 cue 未命中仍全局配对）关闭了转移鸿沟，
但代价被 MX 的过标注放大（asvs FP 0.90 / agents FP 0.875，18 个 FP 案例每例
7-13 条标记）。本诊断在**零 API** 下量化候选政策（v4）对三件事的影响：

1. **目标规则覆盖率**（不可回退）：violation 案例的标注规则必须仍在路由集内——
   这是 I8 测的「annotated rules routed 40/40」，v4 不得低于 v3；
2. **compliant 案例路由集大小**（FP 机会 + 成本代理）：v4 应显著小于 v3；
3. **观测 FP 的可削减率**：把 v3 run 里实际发生的 FP 标记映射回路由决策，
   统计各政策能拦掉多少（不重跑模型的上界估计）。

候选政策（对 matched 且 cue 未命中的规则，即全局兜底对）：
- P0 = v3 现状：全部全局配对；
- P1：内容词重叠 ≥1 才配对（assertion+quote 内容词 ∩ 文件词元/词）；
- P2：重叠 ≥2；
- P3：重叠 ≥1 且每文件至多 K=3 条兜底（按重叠降序、bank-df 升序）；
- P4：重叠 ≥2 且 K=3；
- P5（文件级门）：文件对整个 matched 库零 cue 命中时才允许兜底对——
  假设「盲区违规文件对库沉默，无关文件至少命中自己的范围规则」。

用法：uv run python -m bench.tools.route_v4_diag
产出：experiments/reports/route-v4-diagnosis.json + 控制台摘要。
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from bench.harness.loader import load_cases
from bench.harness.schemas import Verdict
from engine.route import _effective_cues, _cue_variants, _code_tokens
from engine.rule_bank import build_rules
from engine.verify import _content_words, _norm

ROOT = Path(__file__).resolve().parents[2]
SPECS = ("asvs", "agents-sdk", "airbnb", "react19")
# v3 run（论文口径）——FP 标记映射回路由决策用
V3_MLITE = {
    "asvs": "i6-asvs-ds-mlite-f8c666a7fba9",
    "agents-sdk": "i6-agents-sdk-ds-mlite-e3f096039b37",
    "airbnb": "i6-airbnb-ds-mlite-7b321106e455",
    "react19": "i6-react19-ds-mlite-8c5fd2e77f87",
}
POLICIES = ("P0", "P1", "P2", "P3", "P4", "P5")


def _rule_words(rule) -> set[str]:
    """规则的内容词（assertion + quote，_norm 后，非停用词）。"""
    quote = rule.source_span.quote if rule.source_span else ""
    return _content_words(_norm(f"{rule.assertion} {quote}"))


def _file_words(code_text: str) -> set[str]:
    """文件内容词：标识符词元（含驼峰/下划线切分）∪ 文档式词。"""
    from engine.route import _IDENT_PARTS, _CAMEL_SPLIT

    words: set[str] = set()
    for ident in _IDENT_PARTS.findall(code_text):
        for part in _CAMEL_SPLIT.split(ident):
            part = part.lower().strip("_")
            if len(part) >= 3:
                words.add(part)
    for w in re.findall(r"[a-z][a-z0-9_]{2,}", code_text.lower()):
        words.add(w)
    return words


def _cue_hit(cue: str, code_text: str, tokens: set[str]) -> bool:
    """与 route._cue_hit 同构的轻量版（诊断只判断命中与否）。"""
    if cue == "use":
        return re.search(r"\buse\(", code_text) is not None
    if cue == "useHook":
        return re.search(r"\buse[A-Z]\w*\s*\(", code_text) is not None
    return bool(_cue_variants(cue) & tokens)


def pair_allowed(policy: str, overlap: int) -> bool:
    """政策对「cue 未命中 matched 规则」的配对判定。

    P5 的文件级判定在 diagnose_spec 中处理（依赖全库命中数），这里对 P5
    恒放行——单条规则的判定不因政策而异，门在文件层。
    """
    if policy == "P0":
        return True
    if policy in ("P5",):
        return True
    if policy == "P1":
        return overlap >= 1
    if policy == "P2":
        return overlap >= 2
    if policy == "P3":
        return overlap >= 1
    if policy == "P4":
        return overlap >= 2
    raise ValueError(policy)


def diagnose_spec(spec: str) -> dict:
    spec_dir = ROOT / "bench" / "specs" / spec
    rules, _diag = build_rules(spec_dir, "aligned")
    rule_words = {r.id: _rule_words(r) for r in rules}
    cases = load_cases(ROOT / "bench" / "cases" / spec)

    # 观测 FP：v3 run 的 compliant 误判案例 → 被标记的规则 ID 集合
    fp_flags: dict[str, set[str]] = {}
    run = V3_MLITE.get(spec)
    if run and (ROOT / "experiments" / "runs" / run / "results.jsonl").exists():
        for line in (ROOT / "experiments" / "runs" / run / "results.jsonl").read_text(
            encoding="utf-8"
        ).splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["resolved_verdict"] == "compliant" and rec["predicted"]:
                flagged = set()
                for f in rec.get("findings") or []:
                    flagged.update(f.get("rule_ids") or [])
                fp_flags[rec["case_id"]] = flagged

    per_policy = {p: {"cover_hits": 0, "cover_total": 0, "compliant_pairs": 0,
                      "fp_blockable": 0, "fp_observed": 0} for p in POLICIES}
    per_policy["P3"]["fallback_budget"] = 3
    per_policy["P4"]["fallback_budget"] = 3
    detail: list[dict] = []

    for case in cases:
        code = "\n".join(case.read_file(f) for f in case.meta.files)
        tokens = _code_tokens(code)
        fwords = _file_words(code)
        targets = set(case.meta.resolved.rule_ids)
        is_violation = case.meta.resolved.verdict == Verdict.VIOLATION
        is_compliant = case.meta.resolved.verdict == Verdict.COMPLIANT

        # 逐规则决策：cue 命中（v3/v4 都进）或 matched 兜底（按政策）
        entries = []  # (rule, cue_hit, overlap)
        for rule in rules:
            cues, is_global = _effective_cues(rule)
            is_matched = not rule.id.startswith("X-")
            if not is_global and any(_cue_hit(c, code, tokens) for c in cues):
                entries.append((rule, True, 0))
                continue
            if not is_matched:
                continue  # X 规则：cue 未命中不配对（v3 既有政策，不变）
            overlap = len(rule_words[rule.id] & fwords)
            entries.append((rule, False, overlap))

        # P5 文件级门：文件对整个 matched 库零 cue 命中时才允许兜底对
        matched_cue_hits = sum(1 for r, hit, _ in entries if hit and not r.id.startswith("X-"))
        file_silent = matched_cue_hits == 0

        flagged = fp_flags.get(case.meta.case_id, set())
        for policy in POLICIES:
            budget = per_policy[policy].get("fallback_budget")
            # 兜底对按重叠降序、bank-df 升序取预算内（确定性）
            fallback = [e for e in entries if not e[1]]
            fallback.sort(key=lambda e: (-e[2], e[0].id))
            kept_fallback = []
            for e in fallback:
                if pair_allowed(policy, e[2]) and (budget is None or len(kept_fallback) < budget):
                    kept_fallback.append(e)
            if policy == "P5" and not file_silent:
                kept_fallback = []
            routed = {e[0].id for e in entries if e[1]} | {e[0].id for e in kept_fallback}

            if is_violation:
                per_policy[policy]["cover_total"] += len(targets)
                per_policy[policy]["cover_hits"] += len(targets & routed)
            if is_compliant:
                per_policy[policy]["compliant_pairs"] += len(routed)
                if flagged:
                    per_policy[policy]["fp_observed"] += len(flagged)
                    per_policy[policy]["fp_blockable"] += len(flagged - routed)

        detail.append({
            "case_id": case.meta.case_id,
            "verdict": case.meta.resolved.verdict.value,
            "targets": sorted(targets),
            "observed_fp_flags": sorted(flagged),
        })

    out = {"spec": spec, "n_cases": len(cases), "policies": {}}
    for p, m in per_policy.items():
        cov = m["cover_hits"] / m["cover_total"] if m["cover_total"] else None
        out["policies"][p] = {
            "target_rule_coverage": round(cov, 4) if cov is not None else None,
            "coverage_misses": m["cover_total"] - m["cover_hits"],
            "compliant_case_routed_pairs": m["compliant_pairs"],
            "observed_fp_flags": m["fp_observed"],
            "fp_flags_no_longer_paired": m["fp_blockable"],
        }
    out["detail"] = detail
    return out


def main() -> None:
    report = {spec: diagnose_spec(spec) for spec in SPECS}
    out_path = ROOT / "experiments" / "reports" / "route-v4-diagnosis.json"
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    for spec, r in report.items():
        print(f"== {spec} ({r['n_cases']} cases)")
        for p, m in r["policies"].items():
            print(
                f"  {p}: coverage={m['target_rule_coverage']} "
                f"(miss {m['coverage_misses']}) compliant_pairs={m['compliant_case_routed_pairs']} "
                f"fp_paired_away={m['fp_flags_no_longer_paired']}/{m['observed_fp_flags']}"
            )
    print("wrote", out_path)


if __name__ == "__main__":
    main()
