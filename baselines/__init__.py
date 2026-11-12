"""基线注册表（plan.md §2.4：B0/B1/B2/B3/B4）。

每个基线模块实现统一接口：
    BASELINE_ID: str
    predict_case(case, adapter) -> list[Finding]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding


class Baseline(Protocol):
    BASELINE_ID: str

    def predict_case(self, case: Case, adapter: ModelAdapter) -> list[Finding]: ...


_REGISTRY: dict[str, Baseline] = {}


def get_baseline(baseline_id: str) -> Baseline:
    from baselines import b0_zero_shot, b1_full_spec, m_lite

    registry = {
        b0_zero_shot.BASELINE_ID: b0_zero_shot,
        b1_full_spec.BASELINE_ID: b1_full_spec,
        m_lite.BASELINE_ID: m_lite,
    }
    try:
        return registry[baseline_id]
    except KeyError as exc:
        raise KeyError(
            f"未知基线 {baseline_id!r}；可用：{sorted(registry)}"
        ) from exc
