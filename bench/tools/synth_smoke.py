"""I8④ LLM 规则合成冒烟：单规范 × 单模型，产出落盘 experiments/reports/。

用法：
  uv run python -m bench.tools.synth_smoke --spec airbnb --model deepseek/deepseek-flash
  uv run python -m bench.tools.synth_smoke --spec airbnb --model minimax/MiniMax-M3.1-Flash
密钥来自 .env。产出：experiments/reports/synth-{spec}-{tag}.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bench.harness.model_adapter import LiteLLMAdapter

ROOT = Path(__file__).resolve().parents[2]

_MX_KWARGS = {"api_base": "https://api.minimaxi.com/v1"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-sections", type=int, default=12)
    args = parser.parse_args()

    run_config = {"litellm_kwargs": _MX_KWARGS} if "minimax" in args.model else {"litellm_kwargs": {"thinking": {"type": "disabled"}}}
    adapter = LiteLLMAdapter(args.model, run_config=run_config)

    from engine.rule_bank import build_rules  # 对齐对照：确定性提取器 v2
    from engine.synth import llm_coverage_diagnostic, synthesize_rules_llm

    spec_dir = ROOT / "bench" / "specs" / args.spec
    rules, report = synthesize_rules_llm(spec_dir, args.spec, adapter, max_sections=args.max_sections)
    diag = llm_coverage_diagnostic(spec_dir, rules)
    det_rules, det_diag = build_rules(spec_dir, "aligned")
    out = {
        "synth": report,
        "llm_alignment": diag,
        "deterministic_alignment": {
            "n_matched": det_diag["alignment"]["n_matched"],
            "n_canonical": det_diag["alignment"]["n_canonical"],
            "coverage": det_diag["alignment"]["coverage"],
        },
        "n_llm_rules": len(rules),
        "sample_assertions": [r.assertion[:110] for r in rules[:8]],
    }
    tag = args.model.split("/")[-1].lower()
    out_path = ROOT / "experiments" / "reports" / f"synth-{args.spec}-{tag}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in out.items() if k != "sample_assertions"}, ensure_ascii=False, indent=1))
    print("wrote", out_path)


if __name__ == "__main__":
    main()
