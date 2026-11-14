# SpecLens

**SpecLens** 研究：LLM 能否对照「从未见过」的规范，对代码做出可靠、可验证的审查？

三个组成部分：

1. **`bench/` — SpecLens-Bench**：规范遵循（spec-adherence）代码审查基准。4 份真实开放许可规范
   （React 19、OpenAI Agents SDK/LangGraph、OWASP ASVS 5.0、Airbnb JS Style Guide）
   已存快照；**目前仅 react19 有 40 条标注样本**。规范快照附带来源、许可与「新鲜度探测」题库。
   `bench/specs/react19/rules.yaml` 是 12 条冻结规则（逐字原文溯源），也是标注与引擎共享的 ID 命名空间。
2. **`baselines/` — 基线与变体**：B0 zero-shot、B1 规范全文 in-context、
   B2 BM25 检索 + 局部上下文、B3 纯静态检查（零 LLM）、M-lite、M-verified。
   B4（消融）由 M-lite/M-verified 配对承担（plan §2.4 消融定义），见 `docs/STATUS-I1.md`。
3. **`engine/` — 审查引擎**：规则提取（extract）→ ID 对齐（rule_bank）→ 规则验证
   （verify：grounding / 正反例可执行性 / 冲突）→ 规则路由（route）→ 分层审查（review）
   → 证据链与聚合（trace）。

## 当前状态（2026-11-15，I4 迭代后）

> **B0–B3 基线全部实现并完成真实/确定性运行；RQ4 预算阶梯实证全文基线失效模式
> （120K 预算检出即跌 30pp）；B3 静态基线零成本追平 B1（0.870/0.077）。**
> I2 判读维持 **Go（RQ4 规模/成本场景）**。详见 `docs/STATUS-I4.md`。

- ✅ M0 / M1 / M2 代码落地；I1 评测有效性加固；I2 扩样 40 + 真实生死实验（SCIENTIFIC）；
  I3 复核入库 + M-verified 退化归因修复（fail-open）。
- ✅ I4：门 1 归一化修复（句中列表符拼接致 4 规则 quote_in_spec 恒 False，44/44 grounding=1.0）；
  B3 静态基线（检出 0.870 / 误报 0.077 / 零 token）；B2 BM25 检索基线（0.478 / 1.3% 成本）；
  RQ4 预算阶梯（B1: 0.870 → 0.565 → 0.435 → 0.217）；错误分类学 v0
  （`experiments/reports/error-taxonomy-v0.json`，含 TS-011 基准标注粒度问题）。
- ⏳ I5：第二模型（待用户提供 API key）、240 条扩样（先修 TS-011 标注）、真实多仓库 RQ4、
  arXiv 报告骨架、论文。
- 测试：`uv run pytest` 全绿（89 passed）。

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
