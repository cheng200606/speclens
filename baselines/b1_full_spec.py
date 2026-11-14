"""B1 full-spec in-context：把规范全文直接塞进上下文（plan.md §2.4 生死实验的关键对手）。

与 B0 的唯一差异是 prompt 中注入了规范全文——所有对比在同一模型上进行，
差异只来自知识组织方式（plan.md §2.2 控制变量）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bench.harness.schemas import FindingsOutput
from bench.harness.spec_text import spec_text_for_case

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding

BASELINE_ID = "b1_full_spec"

SYSTEM = (
    "You are a meticulous code reviewer. You are given a technical specification "
    "document. Review the code ONLY against rules that are explicitly stated in "
    "that specification; report each violation with the specification text that "
    "supports it. Respond ONLY with a JSON object of the form "
    '{"findings": [{"file": str, "line_start": int, "line_end": int, '
    '"rule_ids": [str], "severity": "info"|"warning"|"error", "message": str, '
    '"evidence": {"rule_quote": str, "explanation": str}}]}. '
    "Report nothing when the code violates nothing in the specification."
)


def build_user_prompt(case: Case, spec_text: str) -> str:
    parts = [
        f"# Specification document\n\n{spec_text}",
        f"\n# Code to review (case {case.meta.case_id})\n",
    ]
    for name in case.meta.files:
        parts.append(f"--- {name} ---\n{case.read_file(name)}")
    return "\n".join(parts)


def predict_case(case: Case, adapter: ModelAdapter) -> list[Finding]:
    # 默认 None = 规范全文不截断。此前硬编码 200_000 会静默丢弃快照文件，
    # 使「全文基线」这一最关键对手看不到完整规范（docs/STATUS-I1.md S0-3）。
    # 需要模拟长上下文受限时，在 config 中显式设置 spec_max_chars，
    # runner 会把被省略的文件写入 run 产物以供审计。
    cfg = getattr(adapter, "run_config", None) or {}
    spec_text, _used = spec_text_for_case(case, cfg.get("spec_max_chars"))
    out = adapter.complete_json(
        system=SYSTEM,
        user=build_user_prompt(case, spec_text),
        schema=FindingsOutput,
        meta={"case_id": case.meta.case_id},
    )
    for finding in out.findings:
        finding.case_id = case.meta.case_id
    return out.findings
