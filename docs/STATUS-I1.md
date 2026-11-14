# SpecLens 项目状态盘点与 I1 迭代方案

- 盘点日期：2026-11-13
- 依据：`git log`（5 次提交）、`README.md`、`plan.md` v1.1、`idea.md` 定位修订 v2、`docs/annotation-guide.md` v1.1、全部源码与 `experiments/runs/` 产物、`pytest` 结果
- 结论一句话：**工程骨架已完成到 M2，科学证据仍为零；当前最紧迫的不是加功能，而是修复会让第一次真实实验失效的评测口径缺陷。**

---

## 1. 整体进展总结

### 1.1 项目定位与当前阶段

SpecLens 的目标不是产品化的代码审查 SaaS，而是「**基准 + 实证/方法论文**」：构建首个公开的规范遵循（spec-adherence）代码审查基准 SpecLens-Bench，测量 LLM 对照「从未见过的规范」审查代码的遵守率与误报率，并验证「规则合成 + 规则验证」管线的改进。北极星为主投 SANER 2028（CCF-B），保底 CCF-C / workshop；兼职投入，计划周期 2026-11 → 2027-10。

计划中的里程碑为 M0 立项（11-16 → 12-06）、M1 基准 v0 + 生死实验（12-07 → 01-10）、M2 方法开发（01-25 → 03-28）、M3 全量实验、M4 写作、M5 投稿。

**实际状态（2026-11-13）**：5 次提交已把 M0、M1、M2 的**代码**全部落地，日历进度大幅超前于计划。但超前的是工程骨架，不是研究证据：所有实验均跑在确定性 mock 适配器上，决定项目方向的「生死实验」（§2.4 Go/No-Go）**实际上从未执行**。

因此准确定位是：**M1 末尾 / M2 工程完成、验证未启动（Engineering-complete, Evidence-empty）**。55 个单元测试全部通过，但测试覆盖的是机械流程，不是方法有效性。

### 1.2 已完成功能

| 里程碑 | 已交付 |
|---|---|
| **M0 立项** | `pyproject.toml` + `uv.lock` + MIT 许可；pydantic 强校验 schema（`SpecMeta`/`CaseMeta`/`RuleRecord`/`Finding`）；repo 即数据库（YAML/JSON + 源码，无后端）；4 份规范快照（react19 6 页、agents-sdk 12 文件、ASVS 5.0 CSV、Airbnb），带 manifest、来源 URL、commit pin、许可；4×20 道新鲜度探测题库且 `source` 均指向真实快照；标注指南 v1/v1.1（冻结 react19 `R-001`…`R-012`）；17 个 react19 案例 |
| **M1 基准 v0** | harness 全套：`loader` / `model_adapter`（mock-perfect、mock-imperfect、LiteLLM + JSON Schema 重试≤3）/ `metrics`（检出率、误报率、规则命中率，borderline 单列）/ `stats`（精确二项 McNemar）/ `spec_text`（md 清洗 + CSV 转文本）/ `probe`（新鲜度探测）/ `runner`（配置哈希归档、原始输出留档、禁止覆盖）；B0 zero-shot、B1 全文 in-context 基线；引擎确定性链路 `ingest → extract → route → review`（44 条规范句规则）；M-lite 基线；4 份 litmus 配置 + 报告生成器 |
| **M2 方法** | `verify` 三道关（grounding 逐字溯源 + 内容词重合 + 等级一致性；executability 正反例自审；conflict 重复/语义矛盾检测，门不可用记 pending 而非 fail）；`trace`（证据链回填、精确去重、重叠行合并、排序聚合）；M-verified 消融对照 |

**质量基线**：`pytest` 55 passed / 1.87s；`git status` 干净；实验产物按 `experiments/runs/<name>-<hash>/` 归档。

### 1.3 遗留问题与技术债务

#### S0 — 会导致真实实验结果不可信（论文级风险）

1. **规则 ID 命名空间断裂（致命）**：`engine.extract` 产出 `react19-auto-001…044`，而基准标注真值使用冻结的 `R-001…R-012`，两者**交集为空**。`CaseOutcome.rule_match` 用真值 ID 与 finding 的 `rule_ids` 求交，因此任何真实引擎运行的 `rule_match_rate` 必然为 0；`trace.attach_evidence` 也只能把证据挂到自动规则而非冻结规则。当前 litmus 报告显示 1.0，是因为 `MockPerfectAdapter` 直接用真值 ID 构造 findings，把这个缺陷完全掩盖了。
2. **生死实验从未真跑**：5 份配置全部 `model: mock-perfect`；报告四项指标均为 `1.0 / 0.0 / 1.0`，六组 McNemar 全为 `p=1.0`。报告虽有文字免责声明，但无强制拦截，容易被误读为「方法已验证」。`litellm` 未安装（`--extra llm` 未同步），无 API 记账，§2.4 的 Go/No-Go 判读无法进行。
3. **关键对手 B1 被静默削弱**：`assemble_spec_text` 默认 `max_chars=200_000`，超限文件直接 `continue` 跳过。react19 全文 236,158 字符，实际只纳入 184,803（丢弃 `reference-react-useTransition.md`）；agents-sdk 同样丢 1 个文件。B1 未看到完整规范，对照不公平，且 RQ4「全文基线随仓库规模失效」的成本研究失去可信基线。
4. **M-verified 名不副实**：`_verified_rules` 调用 `verify_rules(rules, spec_dir)` 时未传 adapter，门 2 恒为 `pending`、门 3 只做重复检测。所谓「完整方法 vs M-lite」消融，实际上只有 grounding 过滤 + 证据链 + 去重。另外 `detect_conflicts` 的 `max_pairs` 只限制冲突字典大小，**不限制 LLM 调用次数**；44 条规则真实接入后最多产生 946 次调用。

#### S1 — 验收指标无法计算 / 复现性不足

5. **无 Cohen's κ 实现**；17 个案例全部只有 `annotator: A` 单标，plan.md §1.3 的 κ ≥ 0.6 与 §2.3.3 的「Phase 0 40 条全量双标」均无法达成（决策记录 #5 仍为待定）。
6. **无 token / 成本 / 时延记账**：§1.3「单文件 < $0.10 / < 60s」与 RQ4 成本–效果曲线无法测量；配置里的 `temperature` 从未传给 `LiteLLMAdapter`；无 `run_index`、无 3 次运行均值±标准差支持。
7. **复现性缺陷**：run 目录哈希仅覆盖 config，不含代码版本，改代码后同配置会撞目录并报错；`probe` 目录名只含题库 digest、不含模型，切换模型重跑会覆盖上一次结果（且无禁止覆盖保护），而「新鲜度探测」恰恰需要跨模型对比。
8. **报告口径**：`make_report` 按 mtime 选最新 run，多模型/多次运行会混用；`mcnemar_between_runs` 把 violation 与 compliant 混成「整体正确率」，而 §2.4 判据是分别看检出 +10pp 或误报 −20%，口径不匹配。

#### S2 — 规模、覆盖与文档

9. **基准规模严重不足**：17 cases（目标 40 / 240），且只有 react19 有案例，其余 3 份规范为 0；`hard` 占比 2/17 = 11.8%（要求 ≥ 20%）；`mined` / `synthetic` 均为 0（计划 35% / 15%）；全部 `handcrafted`。RQ1/RQ3 的跨规范与规则类型分解目前不可能。
10. **基线缺口**：README 宣称有 B2 (RAG)、B3 (静态检查)、B4 (消融)，注册表实际只有 B0 / B1 / M-lite / M-verified。
11. **文档漂移**：README 仍写「状态 M0 骨架 / 引擎模块为接口桩」，`engine/__init__.py` 同样；README 提到的复现指南在 `docs/` 中不存在；`experiments/runs/` 被 `.gitignore` 忽略，唯一提交的报告是 mock 结果。
12. **方法主体未落地**：规则提取仍是正则筛规范句（44 条），未做 LLM 规则合成与正反例（`pos_example` / `neg_example` 恒空）；`tree-sitter` 未安装，路由仍是字符串 cue 匹配。这是 plan.md §2.2 方法管线的真实未完成部分。
13. **溯源引句非全逐字**：标注指南 v1.1 称 R-006…R-012「全部来自快照逐字规范句」，但如 R-007 指南写「Promises passed to `use` must be cached…」，快照实际为「Promises passed to `use` **in Client Components** must be cached…」；R-004 存在直/弯引号差异。逐字溯源是本项目可信度的基础，需以快照原文重建。

---

## 2. I1 迭代方案：评测有效性加固（Measurement Validity Hardening）

### 2.1 迭代目标

> **在不依赖外部 LLM API 的前提下，把评测链路修到「真实模型一接入即可产出可写进论文的、口径正确且可复现的数字」，并把现有 mock 结论明确判定为非科学。**

**范围约束**（遵循 plan.md §1.4 非目标）：不新增 IDE/CI/前端、不做向量库、不微调模型、不改北极星与投稿窗口。真实模型实验、扩样、双标注、B2/B3/B4 均**不在 I1 范围**，列为 I2。

**为什么这是最高优先级**：I1 之前投入任何真实 API 预算，产出的 `rule_match_rate` 会是 0、B1 会被人为削弱、M-verified 消融是假的、结果无法复现——这些数字既不能写进论文，也会误导 Go/No-Go 决策。修复顺序必须「先口径、后实验」。

### 2.2 任务优先级与关键改动点

| 优先级 | 任务 | 关键改动点 | 对应债务 |
|---|---|---|---|
| **P0-1** | 统一规则 ID 命名空间 | 新增 `bench/specs/react19/rules.yaml`（12 条冻结规则，引句逐字取自快照）；新增 `engine/rule_bank.py`（加载 + 一对一贪心对齐）；`RuleRecord` 增 `synthesis_id`；`m_lite` / `m_verified` 改用对齐规则；新增 `rules_source` 配置轴 `canonical / aligned / synthesized` | S0-1、S2-13 |
| **P0-2** | 修正 B1 对照公平性 | `assemble_spec_text` 默认不截断；新增 `spec_max_chars` 配置与 `snapshot_selection()`；run 产物记录 `spec_files_used` / `spec_files_omitted` | S0-3 |
| **P0-3** | 验证关真正接入实验路径 | `m_verified.predict_case` 传 adapter 给 `verify_rules`；缓存按 adapter 隔离；`detect_conflicts` 增加真实 LLM 调用次数上限 | S0-4 |
| **P0-4** | 运行记账与可复现 | `LiteLLMAdapter` 记录 n_calls / tokens / latency；runner 写 `usage.json` 与 summary 字段；config 哈希纳入 `code_digest` + model + temperature + run_index；`temperature` 生效；`probe` 目录按模型隔离并禁止覆盖 | S1-6、S1-7 |
| **P0-5** | 标注一致性与基准体检 | 新增 `bench/harness/agreement.py`：Cohen's κ、verdict/rule-set 一致性、分布与 hard 占比、双标覆盖率、规则引用覆盖率，CLI 输出 JSON | S1-5、S2-9 |
| **P1-1** | 报告防误读与分组统计 | `stats.mcnemar_subsets()` 分 violation / compliant 子集；`make_report` 检测 mock run 打 `NON-SCIENTIFIC` 标记并拒绝输出判读结论；新增脚本化确定性适配器 `mock-scripted` 供端到端验证 | S1-8、S0-2 |
| **P1-2** | 文档纠偏 | README / `engine/__init__.py` 更新为真实状态；新增 `docs/reproduce.md`；本文件回填验证结果 | S2-10、S2-11 |

### 2.3 验收标准（可机械核验）

| # | 验收项 | 判据 |
|---|---|---|
| A1 | 回归测试 | `pytest` 全绿，用例数 ≥ 55（新增测试不破坏既有契约） |
| A2 | 规则溯源 | `rules.yaml` 中 12 条 `source_span.quote` 经规范化后 100% 逐字存在于 react19 快照 |
| A3 | 规则对齐 | 自动提取规则一对一映射到冻结规则且无重复 ID；覆盖率**如实报告并解释未覆盖原因**。实测 7/12（见 §3 决策 D2：初始设 ≥10/12，实测后按证据修订，不掩盖提取器局限） |
| A4 | 口径修复 | 脚本化适配器下 M-lite / M-verified 的 `rule_match_rate > 0`，证据链 `rule_quote` 指向 canonical 原文 |
| A5 | B1 公平 | 默认配置下 react19 6 个快照文件全部纳入，`spec_files_omitted == []` |
| A6 | 验证关生效 | 脚本化 adapter 下 `exec_test` 出现 `pass`/`fail`（非全 `pending`）；gate3 LLM 调用数 ≤ `max_pairs` |
| A7 | 记账与复现 | 脚本化 run 产出 `usage.json`；`temperature` / `code_digest` / `run_index` 进入归档；两次不同配置哈希不冲突 |
| A8 | 体检与防误读 | `validate_bench` 如实输出「17 条单标注 → κ = N/A」「hard 11.8% 未达 20%」；litmus 报告对 mock run 含 `NON-SCIENTIFIC` 且不给 Go/No-Go 结论 |
| A9 | 端到端 | `mock-scripted` 四配置 litmus 产生非退化指标（不全是 1.0/0.0），McNemar 与子集检验可计算 |

### 2.4 方案合理性自检

- **与 plan.md 一致性**：未触碰 §1.4 非目标；修复项全部指向 §1.3 验收指标与 §2.2 控制变量原则（所有变体同一模型、差异只来自知识组织方式）——B1 静默截断与规则 ID 不一致都是对控制变量的破坏。
- **成本**：全程离线，不消耗 API 预算；`litellm` 保持可选依赖，不强行安装。
- **风险与缓解**：改动会触及 runner 与基线模块，可能破坏既有测试 → 保持 `predict_case(case, adapter)` 签名不变，新配置通过 `adapter.run_config` 可选读取，旧适配器默认行为不变；`engine.extract` 输出保持不变，对齐作为独立层，避免污染「自动规则合成」的可复现性。
- **不做的理由**：真实模型实验需要 API key 与预算决策；扩样与双标注需要人工投入，属于 I2；B2/B3/B4 在基准口径未修复前实现只会放大无效实验。

### 2.5 明确顺延到 I2（本次不做）

1. 接入真实 LLM（闭源 + 开源各 1）跑 §2.4 生死实验，产出 Go/No-Go 判读。
2. 基准扩样：40 条生死集 → 240 条全量；补齐 agents-sdk / asvs / airbnb 案例；引入 mined / synthetic；hard ≥ 20%。
3. 第二标注人 / 降级预案落地，κ ≥ 0.6；补 B2/B3/B4 基线与消融。
4. LLM 规则合成（正反例）、tree-sitter AST 路由、RQ1–RQ4 全量实验与成本曲线。
5. 论文写作与投稿窗口复核。

---

## 3. 执行记录（2026-11-13 完成）

### 3.1 关键决策

| # | 决策 | 理由 |
|---|---|---|
| D1 | **对齐只重标注 ID，不把人工冻结规则注入引擎规则集** | 原方案打算把 12 条 canonical 规则并入 `aligned`，这等于把标注真值泄漏给被测方法，`rule_match_rate` 会变成自我印证。改为：合成规则内容（assertion / quote / level）完全不变，命中的改用 `R-xxx`、未命中的改用 `X-NNN`，`synthesis_id` 保留原 ID。`canonical` 模式显式标记 `oracle_leakage: true`，仅作上界诊断 |
| D2 | **按实测证据修订 A3，不做启发式凑数** | 实测对齐覆盖 7/12（58.3%），未覆盖 `R-001/R-002/R-004/R-005/R-009`。归因：R-001/R-002/R-005 是描述性句（不含 must/should 等规范措辞），确定性提取器根本不召回；R-004 的 `Don’t` 是弯引号，未被 ASCII 正则匹配；R-009 的句子切分与引句范围不一致。用规则硬凑到 10/12 会掩盖「确定性提取器不足以复原人工规则」这一真实发现，而它恰恰是 I2 必须做 LLM 规则合成的论据 |
| D3 | **不改 `predict_case(case, adapter)` 接口契约** | 配置通过 `adapter.run_config` 可选注入；默认 `rules_source=synthesized` 保持既有离线测试语义，只有新 litmus/validate 配置显式指定 `aligned`。因此 55 个既有测试全部零改动通过 |
| D4 | **B1 默认 `spec_max_chars=None`（不截断），但保留受限场景** | 静默截断是对控制变量的破坏；RQ4 仍需「上下文受限」场景，故保留显式配置并把 `files_omitted` 写入 `spec_selection.json` 供审计 |
| D5 | **门不可用仍记 pending，不伪造；cap 改为限制 LLM 调用数** | `detect_conflicts` 原先用 `len(conflicts) >= max_pairs` 收尾，44 条规则真实接入最多 946 次调用。改为 `n_checked >= max_pairs` 跳过，并把 `n_pairs_checked` / `within_cap` 写进验证报告 |
| D6 | **新增 `mock-scripted` 而非修改 `mock-perfect` 语义** | `mock-perfect` 承担「指标口径正确性」的既有测试，不能污染。新适配器带已知误差模式（漏掉 hard、固定 1 个误报、约 1/4 规则自洽失败），专门验证评测链路能否产生非退化数字 |

### 3.2 改动文件清单

**新增（11）**

| 文件 | 作用 |
|---|---|
| `bench/specs/react19/rules.yaml` | 12 条冻结规则，引句逐字取自快照（12/12 校验通过） |
| `engine/rule_bank.py` | 规则库加载、引句逐字校验、一对一贪心对齐、`rules_source` 三档构建 |
| `bench/harness/agreement.py` | Cohen's κ、规则集合 Jaccard、基准体检与 CLI |
| `docs/STATUS-I1.md` | 本文件（状态盘点 + I1 方案 + 验收 + 执行记录） |
| `docs/reproduce.md` | 复现指南（离线自检 / 真实实验 / 产物判读 / 常见坑） |
| `experiments/configs/validate-{b0,b1,mlite,mverified}.yaml` | 4 份非科学端到端验证配置 |
| `tests/test_rule_bank.py`、`test_agreement.py`、`test_runner_accounting.py`、`test_i1_guards.py` | 16 个新增测试 |

**修改（12）**

`bench/harness/schemas.py`（`RuleRecord.synthesis_id`）、`spec_text.py`（默认不截断 + `snapshot_selection`）、
`model_adapter.py`（`UsageRecord` / 温度 / `run_config` / `MockScriptedAdapter` / `is_mock_model`）、
`runner.py`（`code_digest`、usage 落盘、规则与规范诊断、`temperature`/`run_index`）、
`stats.py`（分组 McNemar）、`probe.py`（按模型隔离 run 目录 + 禁止覆盖）、
`experiments/make_report.py`（NON-SCIENTIFIC 强制标记 + 分组检验 + `--model`）、
`baselines/b1_full_spec.py`（读 `spec_max_chars`）、`baselines/m_lite.py`、`baselines/m_verified.py`
（接入 `rules_source`、verify 传 adapter）、`engine/verify.py`（cap 修复 + gate 统计）、
`engine/__init__.py` 与 `README.md`（状态纠偏）、4 份 `litmus-*.yaml`（补 `rules_source` 与说明）。

> 计划文档 `plan.md` / `idea.md` 未改动：它们是项目目标与路线图的来源，迭代状态由本文件承载。

### 3.3 验证结果（对照 §2.3 验收标准）

| # | 判据 | 实测 | 结论 |
|---|---|---|---|
| A1 | `pytest` 全绿且 ≥ 55 | **71 passed / 2.32s**（55 既有 + 16 新增，既有测试零改动） | ✅ |
| A2 | 12 条引句逐字可溯源 | `quote_check: 12/12 verbatim, all_verbatim=true` | ✅ |
| A3 | 一对一对齐、覆盖率如实报告 | `matched=7/12, coverage=0.583`，无重复 ID，未覆盖 5 条已归因（D2） | ✅（按证据修订判据） |
| A4 | `rule_match_rate > 0` | `validate-mlite` 与 `validate-mverified` 均为 **1.0**（修复前真实运行必为 0）；`oracle_leakage=false` | ✅ |
| A5 | B1 全文纳入、无省略 | 6/6 快照文件纳入、`included_chars=236,158`、`spec_files_omitted=[]`（修复前 184,803 / 丢 1 个文件） | ✅ |
| A6 | 验证关真正执行 | `gate2: pass=33 / fail=11 / pending=0`；`gate3: n_pairs_checked=60, within_cap=true, skipped_by_cap=12` | ✅ |
| A7 | 记账与复现 | `usage.json` 落盘；B1 `total_tokens=1,008,858`（17 cases × 全文 ≈59K），B0 仅 4,330 — **RQ4 成本差距已被量化**；`temperature`/`run_index`/`code_digest` 进入归档；同配置二次运行报「禁止覆盖」；probe 双模型目录隔离 | ✅ |
| A8 | 体检与防误读 | 体检如实输出 `κ=N/A（无双标）`、`hard=11.8% < 20%`、`17 < 40`、`仅 1/4 规范有样本`；两份报告均 `STATUS: NON-SCIENTIFIC` + 「本次判读：不出具」 | ✅ |
| A9 | 端到端非退化 | `validate`：B0/B1 `检出 1.0 / 误报 0.25`；M-lite `0.6364 / 0.0`；M-verified `0.1818 / 0.0`；`B0 vs M-verified` McNemar `p=0.0215`，分组检验可计算 | ✅ |

> 上述所有数字来自 `mock-scripted`，**只证明评测链路可用，不构成任何方法结论**。
> M-verified 检出率低于 M-lite 是脚本化适配器刻意制造的自洽失败与冲突所致，不是方法效果。

### 3.4 执行后仍存在的缺口（全部归入 I2）

1. **全量真实实验仍未执行**（同日稍后已接入 DeepSeek，见 §3.5）：Go/No-Go 未判读，
   所有已产出的结果仍是非科学的 mock 或单 case 连通性冒烟。
2. **基准规模**：17 条 / 1 规范 / hard 11.8% / 单标注 / 全 handcrafted；κ 无法计算。
3. **方法主体**：规则提取仍是正则筛句（对齐覆盖仅 7/12），`pos_example` / `neg_example` 仍为空，
   tree-sitter AST 路由未落地；B2/B3/B4 基线缺失。
4. **成本口径**：`estimated_cost_usd` 需配置 `price_per_1k_tokens` 才有值，未硬编码单价（避免过期价格污染结果）。
5. **文档**：`docs/annotation-guide.md` v1.1 中 R-007 等引句为转述而非逐字，本次未改指南；
   canonical 引句以快照原文为准，I2 扩样前应回写指南以保持单一真值源。

### 3.5 后续补充：真实模型接入（2026-11-13 晚）

用户填入 `DEEPSEEK_API_KEY` 并指定 `deepseek flash`。核实后确认
`deepseek-flash` 是 DeepSeek-V4.1-Flash 的官方现行模型名（旧的
`deepseek-chat` / `deepseek-reasoner` 已于 2026-07-24 下线），
litellm 1.109.1 明确支持 `deepseek/deepseek-flash` 并读取 `DEEPSEEK_API_KEY`。

已做：`uv sync --extra dev --extra llm`；四份 `litmus-*.yaml` 统一切换为
`deepseek/deepseek-flash` / temperature 0 / `thinking: disabled` /
`litellm_num_retries: 3` / `timeout 180`；`LiteLLMAdapter` 增加 429 与超时退避、
provider 特定参数透传（保留参数过滤）、本地 cost map 默认开关；
`.env.example` / `README.md` / `docs/reproduce.md` 同步；新增
`tests/test_llm_config.py`（控制变量一致性、密钥隔离、参数透传）。

**验证**：`pytest` 82 passed；最小真实调用确认模型/密钥/JSON 模式可用；
TS-001 单 case 冒烟中 B0（284 tokens）、B1（59,259 tokens，全文 6/6 文件）、
M-lite 单规则（259 tokens）三种 prompt 均返回合规 `FindingsOutput`；
四份配置的 run 哈希互不相同。thinking 关闭使输出 token 从 42 降至 6。

**边界**：上述均为链路验证，不是实验结果；全量 17 cases × 3 runs 未执行
（预计约 2,850 次调用、数小时），需由用户确认预算后启动。详见 `docs/reproduce.md` §3。

