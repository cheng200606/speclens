# 生死实验报告（Litmus Experiment）

- 生成时间：2026-11-14T06:03:18.470047+00:00
- runs 目录：`experiments\runs`（前缀 `litmus`，模型过滤 `deepseek/deepseek-flash`）

**STATUS: SCIENTIFIC（真实模型运行）**

> 说明：`model` 为 mock-* 时报告仅验证机械流程，指标不可写入论文；
> 判读标准（§3）只在全部配置为真实模型时适用。

## 1. 配置与总体指标

| 配置 | baseline | 模型 | n_cases | 检出率 | 误报率 | 规则命中率 |
|---|---|---|---|---|---|---|
| B0 | b0_zero_shot | deepseek/deepseek-flash | 40 | 0.913 | 0.5385 | 0.0476 |
| B1 | b1_full_spec | deepseek/deepseek-flash | 40 | 0.8696 | 0.0769 | 0.0 |
| M-lite | m_lite | deepseek/deepseek-flash | 40 | 0.913 | 0.1538 | 0.7143 |
| M-verified | m_verified | deepseek/deepseek-flash | 40 | 0.7826 | 0.0769 | 0.4444 |

## 2. 两两配对 McNemar（精确二项，borderline 不计）

| 对比 | 配对 n | A对B错 | A错B对 | p |
|---|---|---|---|---|
| B0 vs B1 | 36 | 1 | 6 | 0.125 |
| B0 vs M-lite | 36 | 1 | 6 | 0.125 |
| B0 vs M-verified | 36 | 4 | 7 | 0.548828125 |
| B1 vs M-lite | 36 | 2 | 2 | 1.0 |
| B1 vs M-verified | 36 | 4 | 2 | 0.6875 |
| M-lite vs M-verified | 36 | 3 | 1 | 0.625 |

## 2b. 分组配对检验（§2.4 的检出与误报是两条独立判据）

| 对比 | 子集 | 配对 n | A对B错 | A错B对 | p |
|---|---|---|---|---|---|
| B0 vs B1 | 仅违规(检出) | 23 | 1 | 0 | 1.0 |
| B0 vs B1 | 仅合规(误报) | 13 | 0 | 6 | 0.03125 |
| B0 vs M-lite | 仅违规(检出) | 23 | 1 | 1 | 1.0 |
| B0 vs M-lite | 仅合规(误报) | 13 | 0 | 5 | 0.0625 |
| B0 vs M-verified | 仅违规(检出) | 23 | 4 | 1 | 0.375 |
| B0 vs M-verified | 仅合规(误报) | 13 | 0 | 6 | 0.03125 |
| B1 vs M-lite | 仅违规(检出) | 23 | 1 | 2 | 1.0 |
| B1 vs M-lite | 仅合规(误报) | 13 | 1 | 0 | 1.0 |
| B1 vs M-verified | 仅违规(检出) | 23 | 3 | 1 | 0.625 |
| B1 vs M-verified | 仅合规(误报) | 13 | 1 | 1 | 1.0 |
| M-lite vs M-verified | 仅违规(检出) | 23 | 3 | 0 | 0.25 |
| M-lite vs M-verified | 仅合规(误报) | 13 | 0 | 1 | 1.0 |

## 3. 判读标准（plan.md §2.4；仅适用于真实模型运行）

- **Go（方法）**：M-lite 显著优于 B1（检出 +10pp 或误报 −20%，McNemar p<0.1）→ 扩全量
- **Go（规模/成本）**：B1 ≈ M-lite 但 B1 成本/上下文爆表 → 主打 RQ4
- **No-Go（方法）**：B1 全面占优且无成本劣势 → 转 RQ1+RQ3 measurement study

## 4. 复现信息（run 产物）

- B0: `experiments\runs\litmus-b0-5f5dfcc1e01e` · code_digest=`d4b7a0578be9` · temperature=0.0 · run_index=0 · n_llm_calls=40 · total_tokens=24181
- B1: `experiments\runs\litmus-b1-9bf71b835496` · code_digest=`d4b7a0578be9` · temperature=0.0 · run_index=0 · n_llm_calls=40 · total_tokens=2376388
- M-lite: `experiments\runs\litmus-mlite-e86ebe663681` · code_digest=`d4b7a0578be9` · temperature=0.0 · run_index=0 · n_llm_calls=1065 · total_tokens=371786
- M-verified: `experiments\runs\litmus-mverified-e93130e48352` · code_digest=`d4b7a0578be9` · temperature=0.0 · run_index=0 · n_llm_calls=1203 · total_tokens=399326
