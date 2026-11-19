# SpecLens 已知限制（I9，2026-11-20）

> 本文是**诚实清单**：列出当前产出的全部已知弱点、证据指针、修复状态与计划。
> 给导师 / 审稿人看之前，先读这一页——每一条都可核验，没有粉饰。
> 完成状态标记：✅ 已修复 · 🔄 进行中 · ⏳ 待办（依赖人工/导师决策）。

## 1. 参考文献曾有 TODO 作者与改写标题 ✅ 已修复

- **问题（I9 前）**：`paper/refs.bib` 的 5 条学术文献全部 `author={TODO}`，且标题是
  **改写过的**（如真实论文《Still Manual? Automated Linter Configuration via DSL-Based
  LLM Compilation of Coding Standards》被写成《LintCFG: From Natural-Language Coding
  Standards to Linter Configurations》）。arXiv ID 真实、指向真实工作，但按引用找不到原文。
- **修复（I9）**：34 条条目全部按 arXiv API 记录重写（题名 / 作者 / venue / DOI 逐字核对）；
  新增核验工具 `paper/tools/verify_refs.py`（联网逐条比对 arXiv 记录，缓存快照
  `paper/refs-verified.json` 支持离线核验），写作期间可随时重跑防回退。
- **残留**：引文数量仍偏少（工作相关 26 条）；正式投稿前需按目标 venue 再扩 + 复核
  非 arXiv 渠道（ACM DL / IEEE Xplore）的 venue 字段。

## 2. 标注来源：真人签核仅 17/258；κ 无法计算 🔄 进行中（人工步骤）

- **问题**：
  - 258 条案例中，**只有 17 条（TS-001…017）是人手写并人工确认的**；
  - I9 前另有 23 条（TS-018…040）标注 `origin: handcrafted`，但复核方式是
    **「AI 代人工复核」**（`docs/review-I2-synthetic.md` §65 白纸黑字记录）——
    「人工撰写」的口径被虚高；
  - 双标样本为 0 → Cohen's κ 无法计算（plan.md §1.3 目标 κ≥0.6，**未达标**）；
  - hard 占比 8.5%（22/258），低于 plan.md 的 20% 设计线（`bench-health.json`
    逐规范列出）；
  - `reviewed_by` 字段此前不在 schema 中（`extra="forbid"`），复核流程按文档写回
    会直接校验失败——流程实际不可执行。
- **I9 已做**：
  - `Origin` 枚举新增 `ai-reviewed` 档，23 条迁出 `handcrafted`（迁移被测试锁死，
    `tests/test_i6_tools.py::test_origin_four_tiers_no_ai_reviewed_claim_as_handcrafted`）；
  - `CaseMeta` 增加 `reviewed_by` 字段，复核签核流程可执行；
  - 基准体检（`bench/harness/agreement.py`）新增「真人签核 x/y」统计与待签核明细；
  - 复核清单 `docs/review-I6-origins.md` 重生成（**223 条待真人签核**），
    `ai-reviewed` 案例标注「重点核对 AI 复核结论本身」。
- **待办（用户/导师步骤）**：按清单逐条人工签核；之后才能谈 κ（需要第二标注人）。
  论文正文（§Benchmark / §Threats）已按真实口径披露，不再使用虚高数字。

## 3. react19 B0/B1 run 覆盖 120/130（10 条 mined 后补） ✅ 已披露

- **问题**：TS-121…130（10 条 mined）在 B0/B1 全量重跑之后入库，因此
  `i6-react19-*-b0/b1` 只覆盖 120 条——表格 `n` 列此前未披露这一缺口。
- **修复（I9）**：`gen_tables.py` 在 rq1 表自动比对 run 覆盖数与当前基准规模，
  生成脚注「Coverage: ... React 19: 120/130 cases covered ...」；正文 Threats 亦披露。
- **残留**：这 10 条的 B0/B1 数字缺失（mlite/mverified v3 已覆盖 130）。

## 4. 论文内部数字口径曾不一致 ✅ 已修复

- **问题（I9 前）**：
  - 摘要引用 40 案例 pilot 的数字（FP 0.539 / p=0.031），而正文 RQ1 是 240 案例跨规范；
  - RQ3 表由 v0 分类学（pilot、5 列）生成，正文却按 v1 结构化分类学叙述，caption
    写「six-class / five configurations」与表体对不上；
  - 「验证关不损检出」的跨规范复现没有表格支撑。
- **修复（I9）**：
  - 摘要改用 run 产物派生的跨规范宏（`\xsFpDown/\xsFpCells/\xsFpUp`：
    8 格中 5 格误报下降、3 格上升——如实写「not uniformly beneficial」）；
  - RQ3 拆三表：语义分类学（pilot，7 类全列，`rq3-pilot-classes.tex`）、
    结构化分类学 v1（16 run 全量，`rq3-taxonomy.tex`）、保守空审查按规范分布
    （`rq3-taxonomy-per-spec.tex`），caption 与表体逐格对齐；
  - 新增 `rq2-failopen.tex`（全量 mlite vs mverified 成对对照，3 格 p=1.000）。
- **残留**：正文仍有 pilot/全量两套口径并存（v0 语义分类学只在 pilot 上做过）——
  已在文中明确标注 pilot 范围；投稿前可考虑把 v0 分类学扩展到全量。

## 5. 「raw model outputs are released」曾不成立 ✅ 工具已落地，发布动作待办

- **问题**：论文摘要声明释放全部原始模型输出，但 `experiments/runs/*` 被
  `.gitignore` 排除，仓库里只有 `.gitkeep`——声明在打包流程落地前不成立。
- **修复（I9）**：`bench/tools/pack_runs.py`——把论文引用的 28 个 run（或 `--all`
  全量 103 个）打包为 tar.gz，附 MANIFEST.json（逐 run 的 code_digest / n_cases /
  检出误报 / token 计数），输出 sha256 供 release 页面核验。摘要措辞已改为
  「released, together with the archived per-run products」。
- **待办（用户动作）**：`uv run python -m bench.tools.pack_runs --output dist` 后把
  产物上传 GitHub Release（或 Zenodo，投稿时挂 DOI）。

## 6. M 管线存在「在评测规范上迭代」的成分 ⏳ 待方法论决策

- **问题**：routing v3 的修复（I7–I8）是看着 4 份规范冻结规则库的路由覆盖率做的；
  `aligned` 模式还会把冻结规则的人工 `ast_cues` 合并进路由键
  （`engine/rule_bank.py`，论文已披露）。规则内容本身无泄漏（引擎只见规范快照），
  但「优化回路见过这些规范的检出结果」这一质疑成立。
- **缓解（已做）**：规则文本全部派生自规范快照（`aligned` 返回的只是从快照合成的
  规则重标注 ID）；论文 Threats 如实披露。
- **待办（导师决策）**：leave-one-specification-out 验证（在 3 份规范上修，第 4 份
  只测不改）是否值得做一轮；成本约一轮全量 M-lite 重跑（~$10 级）。

## 7. 两模型、单次运行、部分检验不显著 ⏳ 已知，暂不扩

- **问题**：仅 2 个模型（deepseek/deepseek-flash、minimax/MiniMax-M3.1-Flash），
  无西方前沿模型；52 份真实配置全部 `run_index: 0`（无方差报告，plan.md 曾计划
  3 次均值±标准差）；8 个 B0↔B1 误报 McNemar 格中 3 格不显著
  （p=0.125/0.219/1.000，表格如实列出）。
- **判断**：温度 0 + 结论方向在 8 格中 5:3 分明，单轮可支撑「测量研究」档位；
  冲 CCF-B 前建议补第三模型 + 关键格 3 轮方差（预算 ~$50-100 级）。
- **关联**：asvs-mx / agents-mx 的 mverified 未跑完（D7-5/D7-7/D8-4 停止，
  351 规则验证关在该模型延迟下投影数小时）——fail-open 结论由其余 8 格承担，
  论文表格如实留空并注明。

## 8. 分类学「真实性」判读只有 14 例抽检 ⏳ I9 队列

- **问题**：`fp-flagged-non-annotated` 类 167 例的「真实发现 vs 幻觉」判读目前
  只有 seed-42 的 14 例抽检（8 真 / 6 幻觉，`experiments/reports/taxonomy-v1-adjudication.json`），
  「约半数是真发现」的论文表述建立在抽检上。
- **I9 计划**：全量结构化判读（逐案例源码核读）——工作量 ~167 例，完成后论文
  口径可从「roughly half」升级为精确计数。

## 9. 提取/对齐的已知覆盖缺口 ⏳ 长期

- 5 条 react19 canonical 规则（R-001/002/004/005/009）无对齐孪生（alignment 7/12
  → v2 后 9/12），其案例在 M 路径依赖不对称全局配对兜底——这是 M 检出上限的
  直接原因之一；M2 LLM 合成（原型 95.7% 逐字）是既定方向，I9② 入管线对比。

## 给导师的三个决策点

1. **标注签核协议**：223 条待签核按什么口径走（逐条 vs 分层抽样）、是否需要
   第二标注人算 κ；
2. **方法学**：第 6 条的 leave-one-spec-out 是否执行（成本一轮重跑）；
3. **目标档位**：按 §7 补第三模型 + 方差冲 CCF-B，还是先以 workshop /
   数据篇（MSR 2028 Data）口径收口。
