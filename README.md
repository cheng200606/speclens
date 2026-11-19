# SpecLens

**SpecLens** 研究：LLM 能否对照「从未见过」的规范，对代码做出可靠、可验证的审查？

三个组成部分：

1. **`bench/` — SpecLens-Bench**：规范遵循（spec-adherence）代码审查基准。
   4 份真实开放许可规范（React 19、OpenAI Agents SDK/LangGraph、OWASP ASVS 5.0、
   Airbnb JS Style Guide）已存快照（来源 + 许可 + commit pin + 「新鲜度探测」题库）；
   **240 条主套件案例**（react19 130 / asvs 40 / airbnb 38 / agents-sdk 32，含 20 条
   从真实 GitHub 修复提交挖掘的案例）+ 18 条仓库梯度案例（RQ4 成本实验辅助口径）。
   4 份规范共 40 条冻结规则（逐字原文溯源），是标注与引擎共享的 ID 命名空间。
2. **`baselines/` — 基线与变体**：B0 zero-shot、B1 规范全文 in-context、
   B2 BM25 检索 + 局部上下文、B3 纯静态检查（零 LLM）、M-lite、M-verified。
   B4（消融）由 M-lite/M-verified 配对承担（plan §2.4 消融定义），见 `docs/STATUS-I1.md`。
3. **`engine/` — 审查引擎**：规则提取（extract）→ ID 对齐（rule_bank）→ 规则验证
   （verify：grounding / 正反例可执行性 / 冲突）→ 规则路由（route）→ 分层审查（review）
   → 证据链与聚合（trace）。

## 当前状态（2026-11-20，I9 进行中）

> **全基准双模型重跑完成**（2 模型 × 4 规范 × B0/B1/M-lite/M-verified，240 案例）；
> M 管线跨规范转移鸿沟已关闭（routing v3：asvs 检出 0.90 = B1 的 3 倍、airbnb 1.0
> 持平 B1 而误报减半、agents 双超基线）；fail-open 验证关 8 次复现「不损检出」。
> 论文全文见 `paper/main.pdf`（数字全部由 run 产物自动生成）。**已知限制如实清单：
> `docs/LIMITATIONS.md`。**

- ✅ I2–I4：扩样 40 + 生死实验 Go（RQ4 规模/成本）、fail-open 修复、B2/B3 基线、
  预算阶梯（B1 检出 0.870→0.217 @236K→30K chars）、仓库梯度 62× 成本差。
- ✅ I5–I6：4 规范扩样至 240 + GitHub 挖掘管线 + 全基准双模型重跑 + 论文表格自动化
  （`paper/tools/gen_tables.py`：论文数字零手抄，重跑脚本即刷新）。
- ✅ I7：M 管线跨规范重构（确定性提取器 v2、CSV 逐字章节化、mverified fail-open 跨格复现）。
- ✅ I8：routing v3 关闭转移鸿沟（需求 ID 词元过滤 / 复数折叠 / snake_case 词元集 /
  不对称全局配对）；M2 LLM 规则合成原型（引句逐字率 95.7%）；分类学人工抽检。
- ✅ I9（2026-11-20）：论文完整性收口（引用逐条 arXiv API 核验 / origin 分档
  `ai-reviewed` / 数字口径统一 / `docs/LIMITATIONS.md`）；matched 全局 FP 的
  路由层削减被量化否定（三政策×4 规范，缺控制型违规词法不可分），审查层
  scoped-v2 提示把 agents-mx FP 0.875→0.375（McNemar p=0.008）检出不变；
  M2 LLM 合成入管线落败于确定性提取器（对齐覆盖是瓶颈）；分类学全量判读
  84 例（32/84 真实，强烈规范依赖）；PY-004/PY-020 基准缺陷修复。
- 测试：`uv run pytest` 全绿（99 passed）。

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

真实 LLM 运行：`cp .env.example .env` 填 `DEEPSEEK_API_KEY`（及 MiniMax 对照时
`MINIMAX_API_KEY`）。32 份 `i6-*.yaml` 覆盖 4 规范 × 2 模型 × 4 基线：

```bash
uv run python -m bench.harness.runner --config experiments/configs/i6-react19-ds-b0.yaml
uv run python -m experiments.make_report --runs experiments/runs \
    --prefix litmus --model deepseek/deepseek-flash
```

密钥**只放 `.env`**（已被 git 忽略），不要写进 `configs/*.yaml`。
切换模型时全部配置必须同步修改（控制变量）；详见 `docs/reproduce.md` §1 / §3。

论文复现（数字不手抄）：

```bash
uv run python -m paper.tools.gen_tables     # 从 experiments/runs/ 重新生成全部表格与宏
uv run python -m paper.tools.verify_refs    # 参考文献对 arXiv API 逐条核验
cd paper && latexmk -pdf main.tex
```

每个 run 的产物在 `experiments/runs/<name>-<hash>/`：

```
summary.json             # detection_rate / false_positive_rate / rule_match_rate + 记账字段
results.jsonl            # 逐 case 预测与判定
raw/<CASE-ID>.json       # 原始模型输出留档（审计用）
config.resolved.yaml     # 实际配置（含 temperature / run_index / code_digest）
usage.json               # n_calls / tokens / latency / by_phase（支撑成本指标与 RQ4）
spec_selection.json      # B1 纳入/省略的快照文件（对照公平性审计）
rules_diagnostic.json    # 规则来源 / 引句逐字校验 / 对齐覆盖率（仅引擎类基线）
verify_report.json       # M-verified 验证关逐规则 gate 结果与排除理由（可审计归档）
```

归档哈希包含配置**与代码摘要 `code_digest`**：改代码后同配置会得到新目录，不覆盖历史结果。
`experiments/runs/` 不入 git；论文引用的 run 打包：`uv run python -m bench.tools.pack_runs --output dist`。

## 标注来源口径（重要）

`bench/cases/*/*/meta.yaml` 的 `origin` 字段按「谁验证过」分四档（I9 起）：

| origin | 含义 | 数量 |
|---|---|---|
| `handcrafted` | 人工撰写**且**人工复核（唯一论文级可信档） | 17 |
| `ai-reviewed` | AI 起草、AI 代人工复核——**尚缺真人签核** | 23 |
| `synthetic` | AI 起草、无复核 | 198（主套件 180） |
| `mined` | 真实仓库修复提交挖掘、无复核 | 20 |

真人签核流程：`docs/review-I6-origins.md`（自动生成的复核清单，223 条待签核）；
通过后把 `origin` 改 `handcrafted` 并写 `reviewed_by` 字段。**历史教训**：I9 前
23 条「AI 代人工复核」案例曾被标为 `handcrafted`，使论文的人工标注计数虚高——
`tests/test_i6_tools.py` 现已锁死该迁移不回退。完整讨论见 `docs/LIMITATIONS.md` §2。

## 目录结构

```
speclens/
├── bench/
│   ├── specs/<spec>/spec.yaml, rules.yaml, freshness_probe.yaml, snapshot/
│   ├── cases/<spec>/<CASE-ID>/{meta.yaml, code/*}
│   ├── harness/           # schema、loader、adapter、metrics、stats、runner、spec_text、probe、agreement
│   └── tools/             # 案例生成、GitHub 挖掘、复核清单、产物打包
├── baselines/             # b0_zero_shot / b1_full_spec / b2_rag / b3_static / m_lite / m_verified
├── engine/                # ingest / extract / rule_bank / verify / route / review / trace / synth
├── experiments/           # configs/、reports/、runs/（runs 内容 git 忽略）
├── docs/                  # annotation-guide.md、STATUS-I*.md、reproduce.md、LIMITATIONS.md
├── tests/
└── paper/                 # main.tex + tables/（自动生成）+ tools/（gen_tables / verify_refs）
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
  温度 0。多轮方差（`run_index` ≥ 2）尚未全量执行——见 `docs/LIMITATIONS.md` §7。
- 规范全文默认**不截断**；如需模拟长上下文受限，显式设置 `spec_max_chars` 并核查 `spec_selection.json`。

## 许可

代码 MIT。规范文档版权归原权利人所有，入基准的规范均为开放许可，
见各 `spec.yaml` 的 `license` 字段与 `snapshot/manifest.yaml` 的来源与 commit pin。
