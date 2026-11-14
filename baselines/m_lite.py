"""M-lite：生死实验的简版方法 = 规则提取（无验证）+ 规则路由 + 逐规则审查。

与 B1 的对比回答生死问题：「结构化规则组织」相对「全文塞上下文」是否更优。
M-verified 在提取与审查之间插入 verify（三道关）与 trace（证据链）。

I1 修订：规则来源由 `rules_source` 配置轴决定（canonical / aligned / synthesized），
默认 synthesized 保持既有离线测试行为；litmus 配置用 aligned，使 finding 的
rule_id 与标注真值同命名空间（docs/STATUS-I1.md P0-1）。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from engine.rule_bank import rules_source_from

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding, RuleRecord

BASELINE_ID = "m_lite"


@lru_cache(maxsize=8)
def _rules_for_spec(
    spec_dir_str: str, rules_source: str = "synthesized"
) -> tuple:  # tuple[RuleRecord, ...]
    from engine.rule_bank import build_rules

    rules, _diag = build_rules(Path(spec_dir_str), rules_source)
    return tuple(rules)


def _spec_dir_for_case(case: Case) -> Path:
    return case.root.parents[2] / "specs" / case.root.parent.name


def predict_case(case: Case, adapter: ModelAdapter) -> list[Finding]:
    from engine.review import review_code

    spec_dir = _spec_dir_for_case(case)
    source = rules_source_from(adapter)
    rules = list(_rules_for_spec(str(spec_dir.resolve()), source))
    return review_code(case, rules, adapter)
