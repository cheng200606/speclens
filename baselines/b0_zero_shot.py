"""B0 zero-shot：不给任何规范，纯模型能力（plan.md §2.4）。

作用：测量模型对目标规范的「已有知识」，是生死实验的下界参照。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bench.harness.schemas import FindingsOutput

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding

BASELINE_ID = "b0_zero_shot"

SYSTEM = (
    "You are a meticulous code reviewer. Review the given code for defects, "
    "bad practices, and rule violations. Respond ONLY with a JSON object of the "
    'form {"findings": [{"file": str, "line_start": int, "line_end": int, '
    '"rule_ids": [str], "severity": "info"|"warning"|"error", "message": str, '
    '"evidence": {"rule_quote": str, "explanation": str}}]}. '
    "Report nothing when the code is fine."
)


def build_user_prompt(case: Case) -> str:
    parts = [f"Review case {case.meta.case_id}."]
    for name in case.meta.files:
        parts.append(f"\n--- {name} ---\n{case.read_file(name)}")
    return "\n".join(parts)


def predict_case(case: Case, adapter: ModelAdapter) -> list[Finding]:
    out = adapter.complete_json(
        system=SYSTEM,
        user=build_user_prompt(case),
        schema=FindingsOutput,
        meta={"case_id": case.meta.case_id},
    )
    for finding in out.findings:
        finding.case_id = case.meta.case_id
    return out.findings
