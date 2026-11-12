"""B1 full-spec in-context：把规范全文直接塞进上下文（plan.md §2.4）。

生死实验最关键的对手。M1 实现规范快照注入；当前为占位桩。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding

BASELINE_ID = "b1_full_spec"


def predict_case(case: Case, adapter: ModelAdapter) -> list[Finding]:
    raise NotImplementedError(
        "B1 需要 spec 快照与全文注入 prompt，M1 实现（plan.md §4）。"
    )
