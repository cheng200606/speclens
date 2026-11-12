# SpecLens

**SpecLens** 研究：LLM 能否对照「从未见过」的规范，对代码做出可靠、可验证的审查？

三个组成部分：

1. **`bench/` — SpecLens-Bench**：规范遵循（spec-adherence）代码审查基准。4 份真实开放许可规范
   （React 19、OpenAI Agents SDK/LangGraph、OWASP ASVS 5.0、Airbnb JS Style Guide）
   × 人工标注的「违规/合规/边界」代码样本。规范快照附带来源、许可与「新鲜度探测」记录。
2. **`baselines/` — 基线**：B0 zero-shot、B1 规范全文 in-context、B2 naive RAG、B3 纯静态检查、B4 消融。
3. **`engine/` — 审查引擎**：规则合成（extract）→ 规则验证（verify：grounding / 正反例可执行性 / 冲突）
   → 规则路由（route：规则主动扫描适用代码，而非代码检索规则）→ 分层审查（review）→ 证据链（trace）。

状态：**M0 骨架**（计划见仓库外 `plan.md`）。schema 与评测 harness 已可用，引擎模块为接口桩。

## 快速开始

```bash
# 依赖：Python >= 3.11 与 uv
uv sync --extra dev          # 安装 pydantic/pyyaml/pytest，生成 .venv 与 uv.lock

uv run pytest                # 单元测试（loader / metrics / runner 端到端）
uv run python -m bench.harness.runner --config experiments/configs/smoke-b0.yaml
```

smoke run 使用 `mock-perfect` 适配器（不调用任何 LLM API），端到端验证
「加载 case → 基线预测 → 指标计算 → 归档」全流程，产物在 `experiments/runs/<run>-<hash>/`：

```
summary.json          # detection_rate / false_positive_rate / rule_match_rate 等
results.jsonl         # 逐 case 的预测与判定
raw/<CASE-ID>.json    # 原始模型输出留档（审计用）
config.resolved.yaml  # 本次运行的实际配置
```

真实 LLM 运行：`uv sync --extra llm` 后把配置中的 `model` 换成 litellm 模型串（如 `openai/gpt-…`）。

## 目录结构

```
speclens/
├── bench/
│   ├── specs/{react19,agents-sdk,asvs,airbnb}/spec.yaml   # 规范快照元数据
│   ├── cases/<spec>/<CASE-ID>/{meta.yaml, code/*}         # 标注样本
│   └── harness/                                            # schema、loader、adapter、metrics、runner
├── baselines/            # B0–B4，与引擎同接口
├── engine/               # ingest / extract / verify / route / review / trace
├── experiments/          # configs/ 实验配置；runs/ 结果归档（git 忽略内容）
├── docs/                 # 标注指南（draft）、复现指南
├── tests/
└── paper/                # 论文（后置）
```

## 数据约定

- **repo 即数据库**：基准全部是 YAML/JSON + 源码文件，clone 即用，无后端服务。
- 所有 LLM 输出经 pydantic schema 强校验（`bench/harness/schemas.py`），失败重试 ≤3，原始响应留档。
- 每个实验一个 `experiments/configs/*.yaml`，结果按配置哈希归档，禁止覆盖。
- `case_id` 形如 `TS-014`；`verdict ∈ {violation, compliant, borderline}`；规则等级沿用 RFC2119（MUST/SHOULD/MAY），
  规则类型分类学 T1 样式 / T2 API 用法 / T3 架构分层 / T4 安全 / T5 并发与资源。

## 许可

代码 MIT。规范文档版权归原权利人所有，`bench/specs/` 只保存元数据与来源链接（入基准的规范均为开放许可，
见各 `spec.yaml` 的 `license` 字段）。
