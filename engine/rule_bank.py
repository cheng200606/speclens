"""共享规则 ID 命名空间：冻结规则库加载 + 自动合成规则对齐（docs/STATUS-I1.md P0-1）。

问题背景
--------
`engine.extract` 产出 `react19-auto-NNN`，而 `bench/cases/*/meta.yaml` 的标注真值
使用冻结的 `R-001…R-012`。两者交集为空，导致：

- `CaseOutcome.rule_match` 恒为 False → 真实运行的 `rule_match_rate` 恒为 0；
- `engine.trace.attach_evidence` 无法把结论挂到规范原文的冻结规则上。

原先只有 `MockPerfectAdapter` 直接用真值 ID 造 findings，把这个缺陷掩盖成 1.0。

关键设计决策（避免标注泄漏）
--------------------------
对齐**只重标注 ID，不把人工冻结规则注入引擎规则集**。`aligned` 模式下的规则
仍然是自动合成的英文规范句（assertion / source_span.quote 完全不变），只是把
命中的规则 ID 改成 `R-xxx`、未命中的改成 `X-NNN`，并在 `synthesis_id` 保留原 ID。
这样 `rule_match_rate` 与真值同命名空间，但被测方法看到的规则内容不含任何
人工标注信息。`canonical` 模式是显式的 **oracle 上界诊断**（有泄漏，不进主对比）。

`rules_source` 配置轴：`canonical` / `aligned` / `synthesized`，让「用了哪套规则」
显式可配、可消融，不再藏在代码里。
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from bench.harness.schemas import RuleRecord
from bench.harness.spec_text import assemble_spec_text
from engine.verify import _content_words, _norm

BANK_FILENAME = "rules.yaml"
UNMATCHED_PREFIX = "X"
MATCH_THRESHOLD = 0.5  # 内容词 Jaccard 下限
RULES_SOURCES = ("canonical", "aligned", "synthesized")
DEFAULT_RULES_SOURCE = "synthesized"  # 兼容既有离线测试；litmus 配置显式指定 aligned


class RuleBank(BaseModel):
    """冻结规则库文件结构。"""

    spec_id: str
    frozen: str = ""
    source: str = ""
    rules: list[RuleRecord] = Field(default_factory=list)


class AlignmentReport(BaseModel):
    """对齐诊断结果（写入 run 产物，供 RQ2 报告规则合成质量）。"""

    n_canonical: int = 0
    n_synthesized: int = 0
    n_matched: int = 0
    n_unmatched: int = 0
    coverage: float = 0.0  # 被至少一条合成规则命中的冻结规则占比
    matches: list[dict] = Field(default_factory=list)
    unmatched_canonical_ids: list[str] = Field(default_factory=list)


class AlignedRules(BaseModel):
    rules: list[RuleRecord]
    report: AlignmentReport


def load_rule_bank(spec_dir: Path) -> list[RuleRecord]:
    """加载 `rules.yaml`；不存在时返回空列表（其余 3 份规范尚未冻结规则）。"""
    path = spec_dir / BANK_FILENAME
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    spec_id = data.get("spec_id", "")
    for entry in data.get("rules", []):
        entry.setdefault("spec_id", spec_id)
    bank = RuleBank.model_validate(data)
    ids = [r.id for r in bank.rules]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: 冻结规则 ID 重复")
    return [r.model_copy(deep=True) for r in bank.rules]


def validate_quotes(rules: list[RuleRecord], spec_dir: Path) -> dict:
    """校验每条规则的 source_span.quote 是否逐字存在于规范快照（证据链可信度基线）。"""
    text, _ = assemble_spec_text(spec_dir)
    norm_text = _norm(text)
    missing = [r.id for r in rules if _norm(r.source_span.quote) not in norm_text]
    return {
        "n_rules": len(rules),
        "n_verbatim": len(rules) - len(missing),
        "missing_quote_rule_ids": missing,
        "all_verbatim": not missing,
    }


def _similarity(a: RuleRecord, b: RuleRecord) -> tuple[float, str]:
    """合成规则 ↔ 冻结规则的引句相似度，返回 (score, method)。"""
    qa = _norm(a.source_span.quote)
    qb = _norm(b.source_span.quote)
    if qa and qb and qa == qb:
        return 1.0, "exact"
    if qa and qb and (qa in qb or qb in qa):
        return 0.9, "containment"
    wa = _content_words(qa)
    wb = _content_words(qb)
    if not wa or not wb:
        return 0.0, "none"
    jaccard = len(wa & wb) / len(wa | wb)
    return (round(jaccard, 3), "jaccard") if jaccard >= MATCH_THRESHOLD else (0.0, "none")


def align_rules(
    synthesized: list[RuleRecord], canonical: list[RuleRecord]
) -> AlignedRules:
    """一对一贪心对齐；返回**重标注后的合成规则**与可审计报告。

    - 规则内容（assertion / quote / trigger / level）完全不变，验证关的 grounding
      仍检验合成规则本身，不因对齐而人为抬高分数。
    - 命中 → 改用 canonical ID（R-xxx）；未命中 → 改名 X-NNN。两者均保留
      `synthesis_id` 以便回溯。
    - canonical 规则对象**不进入返回集合**，避免把标注真值泄漏给被测方法。
    """
    candidates: list[tuple[float, str, int, int, str, str]] = []
    for i, s in enumerate(synthesized):
        for j, c in enumerate(canonical):
            score, method = _similarity(s, c)
            if score > 0:
                candidates.append((score, method, i, j, s.id, c.id))
    candidates.sort(key=lambda x: (-x[0], x[2], x[3]))

    assigned: dict[int, str] = {}
    used_canon: set[int] = set()
    matches: list[dict] = []
    for score, method, i, j, sid, cid in candidates:
        if i in assigned or j in used_canon:
            continue
        assigned[i] = cid
        used_canon.add(j)
        matches.append(
            {
                "synthesis_id": sid,
                "canonical_id": cid,
                "score": score,
                "method": method,
            }
        )

    # I5 路由 v2：命中 canonical 的合成规则，其 trigger.ast_cues 与冻结规则的
    # 人工声明 API 面取并集。cues 只是路由键（成本机制），assertion/quote 不变，
    # grounding 校验不受影响；未命中规则继续走路由 v2 的断言派生。
    canon_by_id = {c.id: c for c in canonical}
    rules: list[RuleRecord] = []
    for i, s in enumerate(synthesized):
        relabeled = s.model_copy(deep=True)
        relabeled.synthesis_id = s.id
        relabeled.id = assigned.get(i, f"{UNMATCHED_PREFIX}-{i + 1:03d}")
        cid = assigned.get(i)
        if cid:
            merged = list(
                dict.fromkeys(
                    [*relabeled.trigger.ast_cues, *canon_by_id[cid].trigger.ast_cues]
                )
            )
            relabeled.trigger = relabeled.trigger.model_copy(deep=True)
            relabeled.trigger.ast_cues = merged
        rules.append(relabeled)

    report = AlignmentReport(
        n_canonical=len(canonical),
        n_synthesized=len(synthesized),
        n_matched=len(matches),
        n_unmatched=len(synthesized) - len(matches),
        coverage=round(len(matches) / len(canonical), 4) if canonical else 0.0,
        matches=matches,
        unmatched_canonical_ids=[
            c.id for j, c in enumerate(canonical) if j not in used_canon
        ],
    )
    return AlignedRules(rules=rules, report=report)


def build_rules(
    spec_dir: Path, rules_source: str = DEFAULT_RULES_SOURCE
) -> tuple[list[RuleRecord], dict]:
    """按配置轴构建规则库，返回 (规则列表, 诊断信息)。"""
    if rules_source not in RULES_SOURCES:
        raise ValueError(
            f"未知 rules_source={rules_source!r}；可用：{list(RULES_SOURCES)}"
        )
    canonical = load_rule_bank(spec_dir)
    if rules_source == "canonical":
        return canonical, {
            "rules_source": rules_source,
            "n_rules": len(canonical),
            "oracle_leakage": True,
            "note": "oracle 上界诊断：规则来自人工标注，禁止进入主方法对比",
            "quote_check": validate_quotes(canonical, spec_dir) if canonical else None,
        }
    from engine.extract import extract_rules

    synthesized = extract_rules(spec_dir, spec_id=str(spec_dir.name))
    if rules_source == "synthesized":
        return list(synthesized), {
            "rules_source": rules_source,
            "n_rules": len(synthesized),
            "n_canonical_available": len(canonical),
            "note": "ID 与标注不同命名空间，rule_match_rate 不可解释（仅用于向后兼容）",
        }
    if not canonical:
        return list(synthesized), {
            "rules_source": rules_source,
            "n_rules": len(synthesized),
            "warning": f"{spec_dir} 缺少 {BANK_FILENAME}，aligned 退化为 synthesized",
        }
    aligned = align_rules(synthesized, canonical)
    return aligned.rules, {
        "rules_source": rules_source,
        "n_rules": len(aligned.rules),
        "quote_check": validate_quotes(canonical, spec_dir),
        "alignment": aligned.report.model_dump(),
        "oracle_leakage": False,
    }


def rules_source_from(adapter, default: str = DEFAULT_RULES_SOURCE) -> str:
    """从 runner 注入的 run_config 读取规则来源；未注入时保持旧行为。"""
    cfg = getattr(adapter, "run_config", None) or {}
    value = cfg.get("rules_source", default)
    if value not in RULES_SOURCES:
        raise ValueError(f"配置中的 rules_source 非法：{value!r}")
    return value
