"""I6 全量重跑配置生成器：{airbnb,agents-sdk,asvs} × {ds,mx} × {b0,b1} + react19 刷新。

确定性一次性脚本（用后保留作为复现依据）。密钥不入配置（.env 提供）。
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "configs"

DS = {
    "model": "deepseek/deepseek-flash",
    "kwargs": "litellm_kwargs:\n  thinking: {type: disabled}\n",
    "note": "DeepSeek 默认开启 thinking；统一关闭（与 I2-I4 litmus 控制变量一致）。",
}
MX = {
    "model": "minimax/MiniMax-M3.1-Flash",
    "kwargs": 'litellm_kwargs:\n  api_base: "https://api.minimaxi.com/v1"\n',
    "note": "MiniMax 中国区端点；M 系列 thinking 常开（无开关），与 minimax 组一致。",
}
SPECS = ["airbnb", "agents-sdk", "asvs", "react19"]
BASELINES = {
    "b0": "b0_zero_shot",
    "b1": "b1_full_spec",
    "mlite": "m_lite",
}
# mlite 需要 aligned 规则库（引擎从快照提取+对齐冻结库）
EXTRA_LINES = {
    "mlite": "rules_source: aligned\n",
}

TPL = """# I6 全量重跑（gen_i6_configs.py 生成）：{spec} × {model_key} × {bkey}
# {note}
# 密钥：.env（不入配置）。控制变量：同模型组共用 model/temperature/endpoint。
run_name: i6-{spec}-{model_key}-{bkey}
baseline: {baseline}
cases_dir: bench/cases/{spec}
model: {model}
temperature: 0.0
run_index: 0
litellm_num_retries: 3
litellm_timeout_s: 180
{extra}{kwargs}"""


def main() -> None:
    n = 0
    for spec in SPECS:
        for model_key, m in (("ds", DS), ("mx", MX)):
            for bkey, baseline in BASELINES.items():
                text = TPL.format(
                    spec=spec,
                    model_key=model_key,
                    bkey=bkey,
                    note=m["note"],
                    baseline=baseline,
                    model=m["model"],
                    extra=EXTRA_LINES.get(bkey, ""),
                    kwargs=m["kwargs"],
                )
                (OUT / f"i6-{spec}-{model_key}-{bkey}.yaml").write_text(
                    text, encoding="utf-8", newline="\n"
                )
                n += 1
    print(f"wrote {n} configs -> {OUT}")


if __name__ == "__main__":
    main()
