# SpecLens I7 执行记录：跨规范对齐改造 + mverified 新规范 + 分类学 v1（2026-11-15）

## 0. 范围

I7 = STATUS-I6 遗留队列：① 跨规范 M 管线改造（I6 D6-4 首项）；② mverified 新规范重跑；
③ 错误分类学扩展到新规范。人工复核（200 案例）仍待用户执行。

## 1. I7① 根因诊断（对齐坍塌的第一因在提取层）

离线复现（确定性提取，零 API）逐层定位：

1. **asvs CSV 从未进入提取**：`assemble_spec_text` 把 CSV 转写为
   「ReqID (Lx): desc」行，但 `parse_document` 只按 markdown heading 切节——
   CSV 无 heading → 整文件丢弃，asvs 仅剩 README 5.7K 字符可达 → 2 条垃圾规则。
2. **airbnb/agents 段落噪声**：HTML 锚点（`<a name>`）、表格行、跨代码块合并句
   混入断言；airbnb 清单行无句末标点 → 整节粘连成 >400 字符长句被长度过滤。
3. **cues 只认 React 白名单**（`_CUE_WORDS`）→ 非规范无路由键。
4. **编号前缀剥离顺序错误**：`[5.1](#x)` 先转 `5.1` 才能剥编号，原顺序恒不命中。
5. **短祈使句被长度/规范性过滤**：airbnb 式「Use array destructuring」无情态动词。

## 2. 提取器 v2（全部确定性，保持离线可复现）

- `ingest`：CSV 需求行 → 需求级章节（asvs 6 → 351 节，90.6K 字符可达）。
- `extract`：围栏代码块以**哨兵**替换（跨块合并句含 `@@CODE@@` 直接剔除——
  恢复「引句逐字」性质，修复 8 条离线 grounding 失败）；锚点/表格行过滤；
  「Verify that …」计 MUST；祈使句（Use/Prefer/Avoid…）计 SHOULD；
  编号前缀剥离（先链接后编号）；行候选优先 + 跨节轮转采选（覆盖全部章节）；
  **预算自适应**（cap ≥ 节数，asvs 351）；cues 泛化为任意反引号标识符。
- `rule_bank._similarity`：max(引句 Jaccard, assertion+quote 联合 Jaccard)。
- `verify._norm`：两侧同步剥编号前缀——**I4 门 1 零排除不变量在 v2 下保持**
  （87 条 react19 合成规则离线 0 失败）。

## 3. 终态：对齐覆盖与 M-lite 恢复

| 规范 | v1 覆盖 | v2 覆盖 | M-lite 检出 v1 → v2（DS） | v2 MX | FP |
|---|---|---|---|---|---|
| react19 | 7/12 | **9/12** | 0.642 → **0.688**（130 案例，2111 调用） | — | 0.225→0.367 |
| airbnb | 2/8 | **7/8** | 0.000 → **0.263**（172 调用） | **0.263**（178 调用） | 0.0/0.053 |
| agents-sdk | 4/8 | **5/8** | 0.125 → **0.438**（137 调用） | **0.562**（164 调用） | 0.0/0.25 |
| asvs | 0/12 | **12/12** | 0.000（0 调用）→ **0.05**（79 调用） | 0.25（FP 0.35） | 0.1/0.35 |

- 总覆盖 **14/40 → 33/40（0.825）**。路由 benign 零命中性质保持，调用有界。
- agents-sdk M-lite 0.438（DS）/0.562（MX）**超过其 B1 全文基线（0.312）**——
  结构化方法在新规范首次反超；react19 检出 0.642→0.688 但 FP 0.225→0.367
  （规则集 44→87 条的覆盖/误报权衡，如实记录）。
- **asvs 是当前边界**：对齐 12/12、门 1 全过（v2b：351/351 kept、13 flagged），
  检出仍 0-0.05——瓶颈在路由/审查层（prose 规则派生 cue 与代码标识符
  单复数/形态不匹配），列 I8。
- asvs-mx FP 0.35：339 条未对齐 X-规则的过标（MiniMax），如实记录。

## 4. I7② mverified 新规范（fail-open 不损检出，跨三规范复现）

| run | 检出 | FP | 调用 | 对照 mlite |
|---|---|---|---|---|
| airbnb-ds | 0.263 | 0.0 | 474 | 0.263（=） |
| agents-sdk-ds | 0.438 | 0.0 | 588 | 0.4375（=） |
| asvs-ds | 0.0 | 0.05 | 1588 | 0.05（≈；门 0 排除/13 flag） |
| airbnb-mx | 0.210 | 0.0 | 476 | 0.263（≈，-1 例） |
| agents-sdk-mx | D7-7 停止（verify 2.5h + review ≈13 min/调用，投影 4h+） | | | |
| asvs-mx | D7-5 停止（351 规则 verify ≈6-12h） | | | |

- 验证关开销：调用 ×1.5-3.5，检出无损——fail-open 政策在 v2 规则集上复现 I4 结论
  （5/6 格实证；两个停止格的补跑列 I8）。
- asvs 门 1 修复实证：v2a（引句失真）排除 343/351 → v2b 0 排除（D7-6）。

## 5. I7③ 错误分类学 v1（结构化程序归类，16 个 B0/B1 run 全量）

- `bench/tools/gen_taxonomy.py` → `experiments/reports/error-taxonomy-v1.json`。
- **fn-conservative-empty 100 例**（violation 上零 findings 的保守空审查，I6 新类）：
  DS-B1 主导（react19 20 / asvs 14 / agents 11），MX-B1 稀少（11/3/1）——
  过抑制（DS）与过标注（MX）是同一问题的两种模型答案。
- fp-flagged-non-annotated 167（B0/B1 用文档原生标签，ID 交集为近似口径；
  「真实违规」确认仍需 v0 式人工判读——airbnb B1 的范围外真违规已人工实证）。

## 6. 论文与测试

- RQ2 重写为两版本叙事（v1 坍塌 → v2 恢复），数字全部宏化
  （\mlAlign*Vone 固定 manifest、\mlAlign* 取最新 run）；RQ3 接入 v1 类。
- 测试 93 passed（计数绑定同步 87/25 长度界）。

## 7. 决策记录

- D7-1：提取保持确定性（不引入 LLM 合成）——免费、可复现、可审计；LLM 合成仍是 M2 方向。
- D7-2：v1 run 以 manifest 固定（mlite-v1 节），v2 走 find_i6 最新——论文可同时引用两版本。
- D7-3：预算自适应（cap ≥ 节数）取代全局 60 上限；路由 benign 零命中保证成本有界
  （asvs 实测 95 调用/40 案例）。
- D7-4：跨代码块合并句直接剔除（哨兵法）而非放宽 grounding——逐字性优先。
- D7-5：asvs-mx-mverified 中途停止（351 规则 × MiniMax verify ≈ 6-12h，
  基建成本伪影非科学问题）；「验证关不损检出」由 asds/airbnb/agents 三对
  mlite↔mverified 同检出对照承担（DS 三规范 + MX airbnb/agents）。
- D7-7：agents-sdk-mx-mverified 停止（verify 95 规则 2.5h 后 review 相位
  ≈13 min/调用，投影 4h+ 只为补一格冗余确认；fail-open 不损检出已在
  5/6 格成立）。agents-mx-mverified 补跑列 I8。
- D7-6：CSV 章节文本必须逐字保留原始行（含 "(Lx)"）——首次实现重组行文本
  导致引句失真、门 1 全灭 343/351（det 0.0）；修正后 asvs grounding
  340/351=1.0（min 0.8），全规范 0 条低于门。教训：**溯源行是唯一真源，
  任何重组都是引句失真**。
