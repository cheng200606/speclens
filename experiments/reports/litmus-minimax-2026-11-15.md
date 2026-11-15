# 生死实验报告（Litmus Experiment）

- 生成时间：2026-11-15T01:18:57.628754+00:00
- runs 目录：`experiments\runs`（前缀 `litmus-minimax`，模型过滤 `minimax/MiniMax-M3.1-Flash`）

**STATUS: SCIENTIFIC（真实模型运行）**

> 说明：`model` 为 mock-* 时报告仅验证机械流程，指标不可写入论文；
> 判读标准（§3）只在全部配置为真实模型时适用。

## 1. 配置与总体指标

| 配置 | baseline | 模型 | n_cases | 检出率 | 误报率 | 规则命中率 |
|---|---|---|---|---|---|---|
| B0 | b0_zero_shot | minimax/MiniMax-M3.1-Flash | 40 | 1.0 | 0.6154 | 0.0435 |
| B1 | b1_full_spec | minimax/MiniMax-M3.1-Flash | 40 | 0.913 | 0.2308 | 0.0476 |
| M-lite | m_lite | minimax/MiniMax-M3.1-Flash | 40 | 0.8696 | 0.9231 | 0.65 |
| M-verified | m_verified | minimax/MiniMax-M3.1-Flash | 40 | 1.0 | 0.9231 | 0.6522 |

## 2. 两两配对 McNemar（精确二项，borderline 不计）

| 对比 | 配对 n | A对B错 | A错B对 | p |
|---|---|---|---|---|
| B0 vs B1 | 36 | 2 | 5 | 0.453125 |
| B0 vs M-lite | 36 | 7 | 0 | 0.015625 |
| B0 vs M-verified | 36 | 4 | 0 | 0.125 |
| B1 vs M-lite | 36 | 12 | 2 | 0.012939453125 |
| B1 vs M-verified | 36 | 9 | 2 | 0.0654296875 |
| M-lite vs M-verified | 36 | 0 | 3 | 0.25 |

## 2b. 分组配对检验（§2.4 的检出与误报是两条独立判据）

| 对比 | 子集 | 配对 n | A对B错 | A错B对 | p |
|---|---|---|---|---|---|
| B0 vs B1 | 仅违规(检出) | 23 | 2 | 0 | 0.5 |
| B0 vs B1 | 仅合规(误报) | 13 | 0 | 5 | 0.0625 |
| B0 vs M-lite | 仅违规(检出) | 23 | 3 | 0 | 0.25 |
| B0 vs M-lite | 仅合规(误报) | 13 | 4 | 0 | 0.125 |
| B0 vs M-verified | 仅违规(检出) | 23 | 0 | 0 | 1.0 |
| B0 vs M-verified | 仅合规(误报) | 13 | 4 | 0 | 0.125 |
| B1 vs M-lite | 仅违规(检出) | 23 | 3 | 2 | 1.0 |
| B1 vs M-lite | 仅合规(误报) | 13 | 9 | 0 | 0.00390625 |
| B1 vs M-verified | 仅违规(检出) | 23 | 0 | 2 | 0.5 |
| B1 vs M-verified | 仅合规(误报) | 13 | 9 | 0 | 0.00390625 |
| M-lite vs M-verified | 仅违规(检出) | 23 | 0 | 3 | 0.25 |
| M-lite vs M-verified | 仅合规(误报) | 13 | 0 | 0 | 1.0 |

## 3. 判读标准（plan.md §2.4；仅适用于真实模型运行）

- **Go（方法）**：M-lite 显著优于 B1（检出 +10pp 或误报 −20%，McNemar p<0.1）→ 扩全量
- **Go（规模/成本）**：B1 ≈ M-lite 但 B1 成本/上下文爆表 → 主打 RQ4
- **No-Go（方法）**：B1 全面占优且无成本劣势 → 转 RQ1+RQ3 measurement study

## 4. 复现信息（run 产物）

- B0: `experiments\runs\litmus-minimax-b0-ed4c7cdb4d51` · code_digest=`68a6e05435d4` · temperature=0.0 · run_index=0 · n_llm_calls=41 · total_tokens=285104
- B1: `experiments\runs\litmus-minimax-b1-2b3fafe1154a` · code_digest=`68a6e05435d4` · temperature=0.0 · run_index=0 · n_llm_calls=40 · total_tokens=2414936
- M-lite: `experiments\runs\litmus-minimax-mlite-e122e867d6f7` · code_digest=`e095117f6aa5` · temperature=0.0 · run_index=0 · n_llm_calls=1154 · total_tokens=1651439
- M-verified: `experiments\runs\litmus-minimax-mverified-5c084c57a98a` · code_digest=`e095117f6aa5` · temperature=0.0 · run_index=0 · n_llm_calls=1437 · total_tokens=2065628
