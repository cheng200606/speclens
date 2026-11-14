# SpecLens 复现指南（2026-11-13：I1 + DeepSeek 真实模型已配置）

> 完整状态盘点与迭代计划见 `STATUS-I1.md`，项目目标与验收指标见仓库外 `plan.md`。
> 本轮已把四份 litmus 配置从 mock 切换到真实模型，并完成最小连通性验证（见 §3.0）。

## 1. 环境

```bash
cd speclens
uv sync --extra dev --extra llm   # 同时装 pytest 与 litellm；只写 --extra llm 会移除 dev 依赖
uv run pytest                     # 全部通过
```

**密钥只放在仓库根目录的 `.env`**（已被 `.gitignore` 忽略）。代码在
`LiteLLMAdapter` 初始化时通过 `bench/harness/env.py` 加载它，不会覆盖 shell
已 `export` 的变量；缺失所需变量时会直接报出该填哪个变量名。
**不要**把 key 写进 `experiments/configs/*.yaml`：那些文件受版本控制，且会被
原样归档进 `config.resolved.yaml`。CI 场景推荐直接 `export DEEPSEEK_API_KEY=...`。

当前已配置：

| 项 | 值 | 依据 |
|---|---|---|
| 密钥变量 | `DEEPSEEK_API_KEY`（`.env`，已设置） | litellm deepseek provider 读取该变量 |
| 模型串 | `deepseek/deepseek-flash` | DeepSeek-V4.1-Flash 官方名；litellm 1.109.1 明确支持 |
| base URL | 默认 `https://api.deepseek.com` | 无需设置 `DEEPSEEK_API_BASE` |
| 上下文窗口 | 1M tokens | B1 全文实测 59,259 prompt tokens，可完整容纳 |
| 结构化输出 | `response_format={"type":"json_object"}` | 实测三种 prompt 均返回合法 JSON |

> ⚠️ 旧模型名 `deepseek-chat` / `deepseek-reasoner` 已于 2026-07-24 下线，勿再使用。

仓库无 GPU、无数据库、无后端服务；基准与规则库全部是 git 版本化的 YAML/JSON。

## 2. 离线自检（不消耗 API 预算）

```bash
# 基准体检：κ / 样本分布 / hard 占比 / 规则引句逐字校验 / 未达标清单
uv run python -m bench.harness.agreement --root . --json experiments/reports/bench-health.json

# 规则验证三关（离线：门 2 保持 pending，不伪造结果）
uv run python -m engine.verify --spec react19 --output experiments/reports/verify-react19.json

# 评测链路端到端验证（mock-scripted：带已知误差模式，非科学）
for c in validate-b0 validate-b1 validate-mlite validate-mverified; do
  uv run python -m bench.harness.runner --config experiments/configs/$c.yaml
done
uv run python -m experiments.make_report --runs experiments/runs --prefix validate \
    --output experiments/reports/validate-2026-11-13.md
```

`validate-*` 报告顶部必须出现 `STATUS: NON-SCIENTIFIC` 与「本次判读：不出具」。
若没有，说明防误读机制失效，不要继续解读任何数字。

## 3. 真实模型实验（I2，需先确认 API 预算）

控制变量原则：**四个配置必须共用同一模型、同一温度、同一 `rules_source`、
同一 `litellm_kwargs`**，差异只来自知识组织方式（plan.md §2.2）。

### 3.0 已完成的配置与连通性验证

四份 `experiments/configs/litmus-*.yaml` 已统一写入：

```yaml
model: deepseek/deepseek-flash
temperature: 0.0
run_index: 0
litellm_num_retries: 3
litellm_timeout_s: 180
rules_source: aligned        # 仅 mlite / mverified
litellm_kwargs:
  thinking: {type: disabled} # DeepSeek 默认开启 thinking，四份统一关闭
```

已用**不含项目数据**的最小请求验证：模型可用、密钥有效、JSON 模式正常。
随后用 TS-001 做单 case 真实冒烟，三种 prompt 均返回合规 `FindingsOutput`：

| 入口 | prompt tokens | completion tokens | 耗时 | 结果 |
|---|---|---|---|---|
| B0 zero-shot | 284 | 6 | 1.3s | 合法 JSON，0 findings |
| B1 full-spec | 59,259 | 6 | 1.4s | 合法 JSON，0 findings |
| M-lite 单规则 | 259 | 6 | 0.9s | 合法 JSON，0 findings |

> 该表**只证明链路可用，不构成任何效果结论**。TS-001 对应 R-001（SHOULD 级、
> 文档为描述性/「discouraged」措辞），本身属于边界样本；单 case 的 0 findings
> 既不说明模型差，也不说明配置错。正式结论必须来自全量 17+ cases × 3 runs。

### 3.1 thinking 开关的取舍（可自行切换）

实测同一 prompt：thinking 默认开启时 `completion_tokens=42 / 1.52s`，
关闭后 `completion_tokens=6 / ~1s`，且返回内容更干净。

| 取向 | 优点 | 代价 |
|---|---|---|
| `disabled`（**当前默认**） | 输出 token 降约 86%、更快、更便宜、更可复现，JSON 抽取更稳定 | 可能削弱复杂推理；若担心检出率偏低，应做 on/off 对照实验 |
| `enabled` | 逐规则审查可能有更强推理 | 成本与时延上升、输出含 reasoning tokens、随机性增大 |

切换方式：把**四份**配置的 `litellm_kwargs.thinking.type` 同步改为 `enabled`。
只改一份会破坏控制变量。

### 3.2 执行

```bash
# 1) 建议先单配置冒烟（B0 最快），确认账户余额与限流正常
uv run python -m bench.harness.runner --config experiments/configs/litmus-b0.yaml

# 2) 三次重复运行，逐次改四份配置的 run_index: 0 / 1 / 2
for idx in 0 1 2; do
  for c in litmus-b0 litmus-b1 litmus-mlite litmus-mverified; do
    uv run python -m bench.harness.runner --config experiments/configs/$c.yaml
  done
done
```

`run()` 的归档目录名含配置与 `code_digest` 的哈希；同一配置重复运行会报
「run 已存在，禁止覆盖」。改 `run_index` 或改代码即可得到新目录，历史结果永不覆盖。

```bash
# 3) 按模型汇总（--model 防止多次 run 被 mtime 混选）
uv run python -m experiments.make_report --runs experiments/runs \
    --prefix litmus --model deepseek/deepseek-flash \
    --output experiments/reports/litmus-real.md
```

真实模型报告顶部为 `STATUS: SCIENTIFIC`，才会列出可用的 §2.4 判读标准；
Go/No-Go 仍需人工按「检出 +10pp 或误报 −20%，McNemar p<0.1」判定。

**调用量与预算预估**（单次全量、17 cases）：B0/B1 各 17 次调用；M-lite 约 425 次；
M-verified 约 487 次（含验证关 2 的 44×3 次自审与门 3 上限 60 对判定）。
四配置合计约 950 次调用，3 次运行约 2,850 次。B1 每次约 59K 输入 tokens，
是成本主体。DeepSeek 对 `deepseek-flash` 的并发上限为 2,500，串行执行不会触发 429，
但**总耗时可能达数小时**，建议先跑单配置再决定全量规模。

## 4. 新鲜度探测（堵「模型见过规范」质疑）

```bash
uv run python -m bench.harness.probe --probe bench/specs/react19/freshness_probe.yaml \
    --model deepseek/deepseek-flash --output-dir experiments/runs
# 换第二个模型重跑：run 目录按模型名隔离，不会覆盖
```

题库 4 份 × 20 题，`source` 均指向真实快照文件。正确率接近随机（4 选项 ≈ 0.25）
才支持「未见规范」的主张；显著偏高需在论文中如实报告。

## 5. 产物判读

| 文件 | 看什么 |
|---|---|
| `summary.json` | 检出率 / 误报率 / 规则命中率；`n_llm_calls`、`total_tokens`、`latency_s`（RQ4 成本曲线）；`code_digest` |
| `spec_selection.json` | `truncated` 必须为 false，B1 全文 6 个快照文件全部纳入 |
| `rules_diagnostic.json` | `quote_check.all_verbatim`、`alignment.coverage`、`oracle_leakage` 必须为 false |
| `usage.json` | 分阶段真实 token 数与调用数；`estimated_cost_usd` 需配置 `price_per_1k_tokens` 才有值 |
| `results.jsonl` / `raw/` | 逐 case 判定与原始响应，供错误分类学（RQ3）与审计 |
| `config.resolved.yaml` | 本次实际生效的全部配置，含 temperature / run_index / litellm_kwargs |

**成本口径限制**：`estimated_cost_usd` 用「总 tokens × 单一单价」粗估，不区分输入/输出，
也不区分 DeepSeek 峰谷定价（闲时价约为峰时一半）。正式论文请直接用 `usage.json`
中的 `prompt_tokens` / `completion_tokens` 按官方费率自行换算，勿引用该粗估值。

## 6. 常见坑

1. **不要把 mock 数字写进任何结论**。`make_report` 已强制标记，但人工导出 CSV 时仍可能绕过。
2. **`rules_source: canonical` 有标注泄漏**，只能作为上界诊断，不能与方法变体同表对比。
3. **不要只改一个配置的 model / thinking**：不一致会摧毁控制变量，整个 litmus 作废。
4. **不要静默设 `spec_max_chars`**：一旦设置必须检查 `spec_files_omitted` 并在论文中说明。
5. **验证关门 2/3 依赖 adapter**：离线跑 `engine.verify` 时 `exec_test` 全为 `pending`
   是预期行为；真实模型跑 `m_verified` 时才会有 pass/fail，且会显著增加调用量。
6. `uv sync --extra llm` **会移除 dev 依赖**（pytest），必须用
   `uv sync --extra dev --extra llm` 或 `--all-extras`。
7. litellm 启动时联网拉取价格表在国内常超时；代码已默认设
   `LITELLM_LOCAL_MODEL_COST_MAP=True` 使用本地备份。本项目从 `resp.usage` 自行记账，
   不依赖其价格表；需要实时价格时设 `LITELLM_LOCAL_MODEL_COST_MAP=False`。
8. 修改 `bench/harness/*.py`、`baselines/*.py`、`engine/*.py`、`bench/specs/*/rules.yaml`
   都会改变 `code_digest`，归档目录必然变化——刻意设计，勿手动删旧 run。

## 7. 第二模型对照：MiniMax-M2.1（I4 接入，待用户填 key）

```bash
# 1) 在 .env 增加一行（勿提交、勿贴入对话）：MINIMAX_API_KEY=...
# 2) 连通性冒烟（单 case，四配置哈希互异检查内建于 runner）：
uv run python -m bench.harness.runner --config experiments/configs/litmus-minimax-b0.yaml
# 3) 全量四配置（同 model/temperature/api_base，rules_source 仅 M 路径 aligned）：
for c in litmus-minimax-b0 litmus-minimax-b1 litmus-minimax-mlite litmus-minimax-mverified; do
  uv run python -m bench.harness.runner --config experiments/configs/$c.yaml
done
uv run python -m experiments.make_report --runs experiments/runs --prefix litmus-minimax \
    --model minimax/MiniMax-M2.1 --output experiments/reports/litmus-minimax.md
# 4) 新鲜度探测（堵「模型见过」质疑，按模型名隔离不覆盖）：
uv run python -m bench.harness.probe --probe bench/specs/react19/freshness_probe.yaml \
    --model minimax/MiniMax-M2.1 --output-dir experiments/runs
```

要点与坑（来源：锁定版 litellm 1.109.1 的 minimax provider 源码）：

- 路由：`minimax/` 前缀走 OpenAI 兼容端点（中国 `https://api.minimaxi.com/v1`，
  国际 `https://api.minimax.io/v1`）；该版支持的模型为 MiniMax-M2.1 / M2.1-lightning / M2
  （M2.5 需升级 litellm 后可用，暂不采用）。
- **thinking 无法关闭**：M2 系列默认 interleaved thinking，reasoning 在独立字段
  （`reasoning_content`），不污染 JSON content，但 completion tokens 显著高于 deepseek-flash
  （成本对比时用 usage.json 实测值，勿套用 deepseek 单价）。
- **Coding Plan 订阅 key 不兼容**标准 API（litellm#24483）：需用按量付费 key。
- `response_format=json_object` 在 OpenAI 兼容路由上理论支持，首个 run 前先用
  litmus-minimax-b0 冒烟确认；若 400，在 litellm_kwargs 里去掉 response_format 的方案
  需先改 adapter（勿直接改配置绕过 schema 校验）。
- MiniMax 未知错误码若触发 429/超时，现有退避（num_retries=3 / timeout 180s）同样生效。
