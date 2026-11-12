"""M-lite：生死实验的简版方法 = 确定性规则提取（无验证）+ 规则路由 + 逐规则审查。

与 B1 的对比回答生死问题：「结构化规则组织」相对「全文塞上下文」是否更优。
M2 将在提取与审查之间插入 verify（三道关）与 trace（证据链回填）。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding, RuleRecord

BASELINE_ID = "m_lite"


@lru_cache(maxsize=4)
def _rules_for_spec(spec_dir_str: str) -> tuple:  # tuple[RuleRecord, ...]
    from engine.extract import extract_rules

    return tuple(extract_rules(Path(spec_dir_str)))


def _spec_dir_for_case(case: Case) -> Path:
    return case.root.parents[2] / "specs" / case.root.parent.name


def predict_case(case: Case, adapter: ModelAdapter) -> list[Finding]:
    from engine.review import review_code

    spec_dir = _spec_dir_for_case(case)
    rules = list(_rules_for_spec(str(spec_dir.resolve())))
    return review_code(case, rules, adapter)
