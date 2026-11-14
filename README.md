# SpecLens

**SpecLens** 研究：LLM 能否对照「从未见过」的规范，对代码做出可靠、可验证的审查？

三个组成部分：

1. **`bench/` — SpecLens-Bench**：规范遵循（spec-adherence）代码审查基准。4 份真实开放许可规范
   （React 19、OpenAI Agents SDK/LangGraph、OWASP ASVS 5.0、Airbnb JS Style Guide）
   已存快照；**目前仅 react19 有 40 条标注样本**。规范快照附带来源、许可与「新鲜度探测」题库。
   `bench/specs/react19/rules.yaml` 是 12 条冻结规则（逐字原文溯源），也是标注与引擎共享的 ID 命名空间。
2. **`baselines/` — 基线与变体**：已实现 B0 zero-shot、B1 规范全文 in-context、M-lite、M-verified。
   B2 (RAG) / B3 (静态检查) / B4 (消融) **尚未实现**，见 `docs/STATUS-I1.md`。
3. **`engine/` — 审查引擎**：规则提取（extract）→ ID 对齐（rule_bank）→ 规则验证
   （verify：grounding / 正反例可执行性 / 冲突）→ 规则路由（route）→ 分层审查（review）
   → 证据链与聚合（trace）。

## 当前状态（2026-11-14，I3 迭代后）

> **基准 40 条（react19）已 100% 人工复核；M-verified 退化已归因并修复（门 2 自审假阴性
> 误杀 R-011，fail-open 后检出 0.783 → 0.870）。** I2 判读维持：**Go（RQ4 规模/成本场景）**；
> 最干净的测量发现仍是规范上下文显著压制误报（B0 0.539 → B1 0.077，p=0.031）。
> 详见 `docs/STATUS-I2.md` 与 `docs/STATUS-I3.md`。

- ✅ M0 / M1 / M2 代码落地：schema、harness、4 份规范快照与探测题库、标注指南 v1.2、
  B0/B1 基线、verify 三关、trace 证据链、M-lite / M-verified 消融。
- ✅ I1「评测有效性加固」：规则 ID 命名空间、B1 截断、验证关接线、记账、κ 体检、防误读。
- ✅ I2：基准扩样 17→40、新鲜度探测（4 规范均「已熟悉」）、真实生死实验四配置（SCIENTIFIC）。
- ✅ I3：synthetic 案例 23/23 人工复核通过（origin 全部 handcrafted）；验证关逐规则归档
  （verify_report.json）；门 2 假阴性归因（R-011 跨 run fail/pass 实锤不稳定）；
  排除策略改 fail-open（对齐 plan §2.2 人工复核队列）。
- ⏳ I4：RQ4 成本–规模实验（主线）、门 1 归一化修复（`<CodeStep>`）、B2/B3、错误分类学、
  第二模型、240 条扩样、论文。
- 测试：`uv run pytest` 全绿（85 passed）。

## 快速开始

```bash
# 依赖：Python >= 3.11 与 uv
uv sync --extra dev --extra llm   # pydantic / pyyaml / pytest / litellm；勿只写单个 extra

uv run pytest                                          # 单元 + 端到端测试
uv run python -m bench.harness.agreement --root .       # 基准体检（κ / 分布 / 缺口）
uv run python -m bench.harness.runner --config experiments/configs/smoke-b0.yaml
```

离线验证评测链路（**非科学**，产生非退化指标以验证 metrics / McNemar / 证据链 / 记账）：

```bash
for c in validate-b0 validate-b1 validate-mlite validate-mverified; do
  uv run python -m bench.harness.runner --config experiments/configs/$c.yaml
done
uv run python -m experiments.make_report --runs experiments/runs --prefix validate \
    --output experiments/reports/validate-<date>.md
```

真实 LLM 运行：**已完成配置**——`cp .env.example .env` 填 `DEEPSEEK_API_KEY`，
四份 `litmus-*.yaml` 已统一设为 `deepseek/deepseek-flash`（temperature 0、
thinking disabled、`litellm_num_retries: 3`）。直接跑：

```bash
uv run python -m bench.harness.runner --config experiments/configs/litmus-b0.yaml
uv run python -m experiments.make_report --runs experiments/runs \
    --prefix litmus --model deepseek/deepseek-flash
```

密钥**只放 `.env`**（已被 git 忽略），不要写进 `configs/*.yaml`。
切换模型时四份配置必须同步修改（控制变量）；详见 `docs/reproduce.md` §1 / §3。

每个 run 的产物在 `experiments/runs/<name>-<hash>/`：

```
summary.json             # detection_rate / false_positive_rate / rule_match_rate + 记账字段
results.jsonl            # 逐 case 预测与判定
raw/<CASE-ID>.json       # 原始模型输出留档（审计用）
config.resolved.yaml     # 实际配置（含 temperature / run_index / code_digest）
usage.json               # n_calls / tokens / latency / by_phase（支撑成本指标与 RQ4）
spec_selection.json      # B1 纳入/省略的快照文件（对照公平性审计）
rules_diagnostic.json    # 规则来源 / 引句逐字校验 / 对齐覆盖率（仅引擎类基线）
verify_report.json       # M-verified 验证关逐规则 gate 结果与排除理由（可审计归因）
```

归档哈希包含配置**与代码摘要 `code_digest`**：改代码后同配置会得到新目录，不覆盖历史结果。

## 目录结构

```
speclens/
├── bench/
│   ├── specs/<spec>/spec.yaml, rules.yaml, freshness_probe.yaml, snapshot/
│   ├── cases/<spec>/<CASE-ID>/{meta.yaml, code/*}
│   └── harness/           # schema、loader、adapter、metrics、stats、runner、spec_text、probe、agreement
├── baselines/             # b0_zero_shot / b1_full_spec / m_lite / m_verified
├── engine/                # ingest / extract / rule_bank / verify / route / review / trace
├── experiments/           # configs/、reports/、runs/（内容 git 忽略）
├── docs/                  # annotation-guide.md、STATUS-I1.md、reproduce.md
├── tests/
└── paper/                 # 论文（后置）
```

## 数据约定

- **repo 即数据库**：基准全部是 YAML/JSON + 源码文件，clone 即用，无后端服务。
- 所有 LLM 输出经 pydantic schema 强校验（`bench/harness/schemas.py`），失败重试 ≤3，原始响应留档。
- `case_id` 形如 `TS-014`；`verdict ∈ {violation, compliant, borderline}`；规则等级沿用
  RFC2119（MUST/SHOULD/MAY），类型分类学 T1 样式 / T2 API 用法 / T3 架构分层 / T4 安全 / T5 并发与资源。
- **`rules_source` 必须显式一致**：`aligned`（默认推荐，合成规则 ID 重标注到 `R-xxx`，
  不注入人工规则）/ `canonical`（oracle 上界诊断，**有标注泄漏，不进主对比**）/
  `synthesized`（原始自动规则，ID 与标注不同命名空间，`rule_match_rate` 不可解释）。
- 控制变量：同一模型、同一温度、同一 `rules_source` 下比较 B0/B1/M-lite/M-verified；
  温度 0，报告多次运行均值±标准差（配置 `run_index`）。
- 规范全文默认**不截断**；如需模拟长上下文受限，显式设置 `spec_max_chars` 并核查 `spec_selection.json`。

## 许可

代码 MIT。规范文档版权归原权利人所有，入基准的规范均为开放许可，
见各 `spec.yaml` 的 `license` 字段与 `snapshot/manifest.yaml` 的来源与 commit pin。
