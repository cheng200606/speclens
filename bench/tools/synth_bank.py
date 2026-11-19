"""I9② M2 合成规则库落盘：LLM 逐节合成 → 引句逐字预校验 → 写入 rules-llm-synth.yaml。

与 I8④ 冒烟（synth_smoke.py）的差异：冒烟只留样例断言，本工具落盘**全部通过
预校验的规则**（RuleRecord 全字段），供 `rules_source: llm-aligned` 在 runner
中作为规则库消费——run 行为保持确定性（不隐式调 LLM），合成是一次单独的、
产物归档的实验步骤。

用法：
  uv run python -m bench.tools.synth_bank --spec airbnb --model deepseek/deepseek-flash
  uv run python -m bench.tools.synth_bank --spec agents-sdk --model deepseek/deepseek-flash
产出：bench/specs/<spec>/rules-llm-synth.yaml + experiments/reports/synth-bank-{spec}-{tag}.json（报告）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from bench.harness.model_adapter import LiteLLMAdapter

ROOT = Path(__file__).resolve().parents[2]

_MX_KWARGS = {"api_base": "https://api.minimaxi.com/v1"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-sections", type=int, default=24)
    args = parser.parse_args()

    run_config = (
        {"litellm_kwargs": _MX_KWARGS}
        if "minimax" in args.model
        else {"litellm_kwargs": {"thinking": {"type": "disabled"}}}
    )
    adapter = LiteLLMAdapter(args.model, run_config=run_config)

    from engine.synth import llm_coverage_diagnostic, synthesize_rules_llm

    spec_dir = ROOT / "bench" / "specs" / args.spec
    rules, report = synthesize_rules_llm(
        spec_dir, args.spec, adapter, max_sections=args.max_sections
    )
    diag = llm_coverage_diagnostic(spec_dir, rules)

    payload = {
        "rules": [
            {
                "id": r.id,
                "spec_id": r.spec_id,
                "level": r.level,
                "category": r.category,
                "assertion": r.assertion,
                "source_span": {"section": r.source_span.section, "quote": r.source_span.quote},
                "trigger": {"scenario": r.trigger.scenario, "ast_cues": list(r.trigger.ast_cues)},
            }
            for r in rules
        ]
    }
    bank_path = spec_dir / "rules-llm-synth.yaml"
    bank_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )

    report["llm_alignment"] = diag
    report["n_rules"] = len(rules)
    tag = args.model.split("/")[-1].lower()
    report_path = ROOT / "experiments" / "reports" / f"synth-bank-{args.spec}-{tag}.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "bank": str(bank_path),
                "n_rules": len(rules),
                "n_quotes_invalid": report["n_quotes_invalid"],
                "verbatim_rate": (
                    report["n_quotes_verbatim"]
                    / max(1, report["n_quotes_verbatim"] + report["n_quotes_invalid"])
                ),
                "alignment": diag["coverage"],
                "n_matched": diag["n_matched"],
                "n_canonical": diag["n_canonical"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
