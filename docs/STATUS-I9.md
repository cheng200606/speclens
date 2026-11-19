# SpecLens I9 执行记录：论文完整性收口 + 路由层 FP 定界 + M2 入管线 + 分类学全量判读（2026-11-19/20）

## 0. 范围与起点

I9 起点：论文级收尾批次（用户指定优先：「引用修 + 口径统一 + README 刷新 +
LIMITATIONS 页」）+ STATUS-I8 遗留队列。执行顺序按用户指示推进到 I9 完成。

## 1. 论文完整性批次（先于队列执行，commit a7a8fe7）

### 1.1 参考文献从「看起来像编造」到逐条可核验

- **问题**：refs.bib 5 条学术文献全部 `author={TODO}` 且标题是改写过的
  （arXiv ID 真实、指向真实工作，但按引用找不到原文）——给导师/审稿人的第一观感风险。
- **修复**：34 条条目全部按 arXiv API 记录重写（题名/作者/venue/DOI 逐字）；
  新增 `paper/tools/verify_refs.py`（arXiv API 逐条比对，NFKD 归一使 LaTeX 重音宏
  与 UTF-8 记录可匹配；缓存 refs-verified.json 支持离线核验）。
- **Windows 教训（D9-0）**：bib 里写 UTF-8 原字符（İçöz/Šmite）会被 Windows bibtex
  经系统代码页写成乱码（.bbl 编译即 fatal）——**作者名必须用 LaTeX 重音宏（ASCII）**。
- 新增条目含最邻近工作 SGCR（ASE 2025，specification-grounded review——正文加
  对比段：SGCR 单工业场景+接受率口径 vs 本工作未见规范+violation/compliant 平衡）。

### 1.2 origin 分档：AI 代复核不再冒充人工

- **问题**：23 条（TS-018…040）「AI 起草 + AI 代人工复核」的案例标着
  `origin: handcrafted`——人工标注计数虚高；`reviewed_by` 字段不在 schema
  （extra=forbid），复核流程按文档写回会校验失败——**流程实际不可执行**。
- **修复**：Origin 枚举新增 `ai-reviewed` 档并迁移 23 条（测试锁死不回退）；
  CaseMeta 增加 `reviewed_by`；体检新增「真人签核 17/258」统计；复核清单重生成
  （223 条待签核，ai-reviewed 案例标注「重点核对 AI 复核结论本身」）。
- 口径：handcrafted=人工撰写**且**人工复核（17）；ai-reviewed=AI 起草+AI 代复核（23）；
  synthetic（198）；mined（20）。论文 Cases 段与 Threats 同步真实口径。

### 1.3 数字口径统一

- 摘要：pilot 数字（FP 0.539 / p=0.031）→ 跨规范全量宏（8 格中 5 降 3 升——
  如实写 not uniformly beneficial）；「all raw model outputs are released」→
  可核实表述 + `bench/tools/pack_runs.py`（MANIFEST + sha256 打包）。
- RQ3：表/文对齐——v0 语义分类学（pilot 7 类全列，含 B3 列与第二模型脚注）、
  v1 结构化分类学（16 run）、保守空审查按规范分布三表齐备。
- RQ2：新增 `rq2-failopen.tex`（全量 mlite↔mverified 成对，3 格 p=1.000）。
- rq1 表自动披露覆盖率（react19 B0/B1 120/130，10 条 mined 后补）。
- canonical-runs.json：mlite-v3/mverified-v3 按 ID 固定（不再依赖 mtime 取最新）。

### 1.4 README + LIMITATIONS

- README 从 I4 口径（40 案例/89 tests）刷新到 I8/I9（258 案例/98 tests/origin 表/复现命令）。
- 新增 `docs/LIMITATIONS.md`：9 项已知限制（证据指针 + 状态 + 计划）+
  给导师的三个决策点。

## 2. I9① matched 全局 FP 削减（相关度预算化）→ 路由层定界（负结果）+ 审查层实验

### 2.1 诊断（全离线，bench/tools/route_v4_diag.py）

FP 标记三层分解（按 v3 run 产物回映射路由决策）：
- **cue 命中层**（tier-1）：asvs-mx 72 条；
- **matched 兜底层**（cue 未命中全局配对）：asvs-mx 112 条（其中 overlap=0 纯噪声 90）、
  agents-mx 17 条——**主要 FP 源**；
- **编造 ID 层**：模型引用路由集之外的需求编号（引句里的 "V7.3.1 (L2)" 被
  当 rule_id 回引，或整句/“MUST”）——asvs-mx 66 条、agents-mx 21 条。

### 2.2 三政策离线定界（覆盖不可回退为硬约束）

| 政策 | asvs 覆盖 | airbnb 覆盖 | 备注 |
|---|---|---|---|
| P1 内容词重叠 ≥1 | 1.0→**0.45** | 0.95→0.58 | 盲区在内容词层同样存在 |
| P2 重叠 ≥2 | **0.20** | 0.53 | 更差 |
| 文件级门（matched 零命中才兜底） | 16/20 | **10/18** | airbnb 丢 44% |
| 预算 K（保 100% 覆盖） | K=12（不砍） | K=6（仅砍 ~1-2 条/文件） | 前沿支配 |

**结论（D9-1）**：缺控制型违规（「必须有 X」被「没有 X」违反）与无关文件在
词法空间**不可分**——I8 的不对称路由买检出（asvs 0.90=3×B1）的同时买 FP
（asvs-mx 0.90）；**matched 全局的 FP 代价在路由层不可削减**，这是三政策 ×
4 规范的量化定界，入稿 RQ2 层归因。

### 2.3 审查层实验（scoped-v2 提示，唯一变量=审查提示）

`review_prompt: scoped-v2`（engine/review.py 新轴）：只审当前规则、不报引句里的
需求 ID、rule_ids 用给定 ID、投机关联不报。**刻意不做「主题缺席即不报」**——
那会直接砍掉缺控制型检出。三格重跑：asvs-mx、agents-mx（两个最差 FP 格）+
asvs-ds（DS 回归）。结果见 §5 终表。

## 3. I9② M2 合成入管线

- `bench/tools/synth_bank.py`：LLM 逐节合成 → 逐字预校验 → 落盘
  `bench/specs/<spec>/rules-llm-synth.yaml`（**run 时零 LLM 调用**，确定性复现）。
- rule_bank 新增 `rules_source: llm-aligned`（合成库 → 同一对齐器）；digest glob 覆盖。
- 合成库质量：airbnb 48 条（逐字率 94.1%，对齐 4/8）、agents 48 条（逐字率 100%，
  对齐 3/8）——**LLM 合成对齐低于确定性提取器**（7/8、5/8）。
- 对比 run：airbnb-ds、agents-sdk-ds × mlite × llm-aligned（结果见 §5 终表）。

## 4. I9④ 分类学全量判读（167 实例 → 84 去重案例，逐例核读）

- `experiments/reports/taxonomy-v1-adjudication-full.json`：**32/84（38%）含至少
  一条真实且有规范背书的范围外发现**，规范依赖性极强：
  airbnb **14/14** 真、asvs **13/16** 真、agents-sdk **2/16**、react19 **3/38**。
- 关键快照证据：asvs 的 V6.2.1（密码≥8）/V8.2.1（功能级授权）/V2.4.1（反自动化）/
  V14.3.2（anti-caching）/V16.3.1（认证日志）等真实条文背书大多数 asvs 标记；
  react19 的幻误区=「startTransition 不支持 async」（文档示例全在用 async）、
  「useOptimistic 必须带 reducer」（文档明示 `reducer?` 可选）、「缓存须失效/驱逐」
  （文档自己的缓存实现不做）。
- **I8 抽检修正**：PY-134 曾判「真」；全量核读显示 verify_signature 确实被调用——
  过度推断，已在报告 notes 记录。
- **基准缺陷（顺带发现）**：agents-sdk PY-004（compliant 案例）回调参数
  (agent, context) 与文档 (context, agent) 相反——案例修复（PY-020 同型），
  待 run 完成后落盘避免扰动在跑产物。
- 论文口径升级：「roughly half」→ 精确计数 + 规范依赖性洞察（宏 taxFull*）。

## 5. 实验终表

### 5.1 scoped-v2 审查层实验（三格，唯一变量=审查提示；对照=mlite-v3 固定 run）

| 格 | v3 (v1 提示) | p2 (scoped-v2) | McNemar compliant | McNemar violation |
|---|---|---|---|---|
| asvs-mx | det 0.850 / FP 0.900（err 5，1117 调用） | **det 0.950 / FP 0.700**（err 2，975 调用） | FP b=5/c=1 p=0.219 | det b=3/c=1 p=0.625 |
| agents-mx | det 1.000 / FP 0.875（335 调用） | **det 0.938 / FP 0.375**（296 调用，-19% tokens） | **FP b=8/c=0 p=0.008 显著** | det b=0/c=1 p=1.000 |
| asvs-ds | det 0.900 / FP 0.400（826 调用） | det 0.800 / FP 0.350（780 调用） | FP b=1/c=0 p=1.000 | det b=0/c=2 p=0.500 |

- **结论（D9-2 终态）**：范围纪律 + 软校准提示把两个过标注格的 FP 显著压下
  （agents-mx 0.875→0.375 显著；asvs-mx -20pp 不显著且检出反升 1 例），代价是
  DS 校准趋保守（asvs-ds 检出 -2 例，不显著）——FP 杠杆在审查层成立，
  检出风险格如实入稿（\pTwo* 宏族）。
- p2 的 junk ID（"(L2)" 后缀需求编号回显）仍在——聚合层已前置真 ID 不影响指标，
  留作 review prompt 的后续精化。

### 5.2 llm-aligned（M2 合成入管线，两格）

| 格 | 确定性 v2 (aligned) | llm-aligned（24 节合成库） |
|---|---|---|
| airbnb-ds | det **1.000** / FP 0.105（7/8 对齐） | det 0.579 / FP 0.105（4/8 对齐，逐字率 94%） |
| agents-sdk-ds | det **0.625** / FP 0.0625（5/8 对齐） | det 0.500 / FP 0.250（3/8 对齐，逐字率 100%） |

- **结论（D9-3 终态）**：等预算下 LLM 合成全面落败于确定性提取器——瓶颈是
  对齐覆盖而非逐字性（逐字率 94-100% 由构造保证）。M2 方向的下一步是提升
  合成覆盖（更多节 / 更好的提示），不是改进逐字校验。

### 5.3 路由定界（离线，零 API；route-v4-diagnosis.json）

| 政策 | asvs 覆盖 | agents 覆盖 | airbnb 覆盖 | react19 覆盖 |
|---|---|---|---|---|
| P0（v3 现状） | 1.00 | 0.625 | 0.947 | 0.810 |
| P1 重叠≥1 | 0.45 | 0.5625 | 0.579 | 0.810 |
| P2 重叠≥2 | 0.20 | 0.50 | 0.526 | 0.684 |
| P3 重叠≥1 且 K=3 | 0.40 | 0.5625 | 0.579 | 0.544 |
| P5 文件级门 | 0.80 | 0.5625 | 0.526 | 0.392 |

- 覆盖保不住（P1/P5）或 FP 削不动（保 100% 覆盖需 K=12=全池）——D9-1 定界成立。

## 6. 决策记录

- D9-0：bib 作者名一律 LaTeX 重音宏（Windows bibtex 代码页损坏 UTF-8）。
- D9-1：matched 全局 FP 的路由层削减被否定（三政策量化定界）；FP 杠杆移审查层。
- D9-2：审查层以 `review_prompt: scoped-v2` 配置轴落地（范围纪律 + 软校准），
  不做「缺席判定」以保护缺控制型检出。
- D9-3：M2 合成以「落盘 synth bank + llm-aligned 规则源」入管线——run 确定性优先，
  合成是归档的独立实验步骤。
- D9-4：asvs-mx/agents-mx mverified 维持停止（D7-5/D7-7/D8-4 顺延）：fail-open
  已 8 格复现；asvs 351 规则 × MX 延迟投影 6-12h 的基建伪影结论不变。
- D9-5：PY-134 判读修正入档；PY-004/PY-020 案例修复排队（不扰动在跑 run）。

## 7. 测试与提交

- 98 passed（+2 origin 档锁死/签核字段、+1 review_prompt 轴）。
- 提交：a7a8fe7（论文完整性批次）→ I9 终态提交（见 git log）。
