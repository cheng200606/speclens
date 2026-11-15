# SpecLens I6 执行记录：全量重跑 + 表格自动化 + arXiv 排版 + mined 扩量（2026-11-15）

## 0. 范围与判据

I6 = STATUS-I5 遗留队列：① 双模型 248 案例全量重跑（含新规范首跑）；
② 论文表格自动化（数字全部由 run 产物再生成）；③ arXiv 编译排版（本地 + CI）；
④ mined 扩量（addEventListener 族）；⑤ 全库 synthetic/mined 人工复核清单。

## 1. 全量重跑（wave-1 b0/b1 + wave-2 mlite）

- 配置：`experiments/configs/i6-{spec}-{ds|mx}-{b0|b1|mlite}.yaml`（24 份，
  `bench/tools/gen_i6_configs.py` 生成）。deepseek=deepseek/deepseek-flash（thinking 关），
  mx=MiniMax-M3.1-Flash（中国区端点，thinking 常开）。temperature 0，run_index 0。
- 覆盖：airbnb 38 / agents-sdk 32 / asvs 40 / react19 120（含 mined），共 230 案例 ×
  双模型 × 3 配置；react19-repo 18 例沿用 I5 rq4 产物（成本口径独立）。
- **deepseek 全部完成**（b0/b1/mlite × 4 规范，0 case error）。**minimax 在飞**
  （b0/b1 完成后接 mlite）。

## 2. 主要发现（deepseek 侧，最终数字以 gen_tables 产物为准）

### 2.1 全量 react19（120 案例）：B0↔B1 双向显著

| 对比（B0 vs B1，McNemar 精确二项） | 配对 n | B0对B1错 | B0错B1对 | p |
|---|---|---|---|---|
| 仅违规（检出） | 67 | 14 | 0 | **0.000122** |
| 仅合规（误报） | 49 | 0 | 25 | **<1e-5** |
| 全部 | 116 | 14 | 25 | 0.108 |

- B1 全文规范在场：误报 0.592→0.082（显著改善）**同时**检出 0.910→0.702
  （显著恶化）。40 案例试点（I2-I4）中「检出统计不变」在扩样后不再成立——
  扩样暴露了 in-context 规范的检出-误报权衡（trade-off），是 I5 扩样科学回报的直接证据。

### 2.2 跨规范 RQ1（deepseek）

| 规范 | B0 det/FP | B1 det/FP | 解读 |
|---|---|---|---|
| react19 (120) | 91.0 / 59.2 | 70.2 / 8.2 | FP 压制 + 检出让渡 |
| airbnb (38) | 63.2 / 0.0 | 100.0 / 21.1 | 「已见」对照：B0 无误报，加规范反升误报、检出补满 |
| agents-sdk (32) | 56.2 / 31.2 | 31.2 / 6.2 | **过抑制**：FN 复核=空 findings（如 PY-009 B0 报、B1 []） |
| asvs (40) | 45.0 / 40.0 | 30.0 / 5.0 | 过抑制 + FP 压制 |

- agents-sdk B1 已核实非截断伪影：spec_selection.json `truncated:false`（11/11 文件、
  207,709 字符全文在场）。过抑制为真实行为：规范在场使模型对陌生 SDK 的违规判定
  保守化（空 findings）。
- 跨规范模式：规范「越不熟悉/越抽象」（agents-sdk、asvs），B1 的 FP 压制越强、
  检出过抑制也越强；规范「越 ingrained」（airbnb 对照组），B0 本就无误报，
  加规范反而增加合规误报。adherence 是「模型既有信念 × 规范要求」的交互函数。

## 3. 表格自动化（论文数字不再手抄）

- `paper/tools/gen_tables.py`：从 run 产物生成 `paper/tables/{rq1-crossspec,
  rq2-verification,rq4-ladder,rq4-repo,rq3-taxonomy,macros}.tex` + `DIGEST.md`（run 溯源）。
- canonical run 固定清单 `paper/canonical-runs.json`（litmus40 / budget-ladder /
  rq4-repo / b2 以 ID 固定；i6-* 按 `i6-{spec}-{ds|mx}-{b0|b1|mlite}` 自动发现最新）。
- `paper/main.tex`：Results 全部改引 `\input{tables/*}` 与 macros
  （\benchN、\dsBzeroFP、\repoGap 等），手抄数字清零。

## 4. arXiv 编译排版

- 本地 TeXLive 2025：`latexmk -pdf paper/main.tex` 通过（5 页，含 4 表 + 宏）。
- CI：`.github/workflows/paper-build.yml`（setup-uv → 有 run 产物则重生成表格，
  否则用仓内 tables 副本 → latex-action 编译 → 上传 PDF artifact）。
  experiments/runs 按约定不入库（plan §3.4），故 CI 走仓内 tables 副本路径。
- `paper/.gitignore`：LaTeX 中间产物不入库，`tables/*.tex` 入库（自包含可编译）。

## 5. mined 扩量（终态）

- `bench/tools/mine_github.py`：查询 12→20（+事件订阅族 8 条）、vetting 放宽为
  双族（interval/timeout 族 ∪ addEventListener 订阅族）、cap 8→20、
  按 repo@sha8 去重已 emit 案例；`_get/_get_text` 退避加重（6 级至 60s，
  抗本网络对 github.com 的间歇 SSL 阻断）。
- 终态：**新产出 10 对（TS-121…130，全 violation，全 origin=mined）**，
  mined 总计 20；react19 130 案例；主套件 240（=40 handcrafted + 180 synthetic
  + 20 mined），另有仓库辅助 18。待人工复核 200（review-I6-origins.md）。

## 7. 终态数字（全 run 落盘；表格/宏由 gen_tables 产物为准）

- **run 完成度**：23 个 i6 run 完成（deepseek 12/12 + minimax 11/12；
  react19-mx-mlite 按 D6-5 停止，9/120 无 summary 不入表）。
  react19-mx-b0 含 4 个 provider 失败（1 timeout + 3 conn-refused），
  按 I4 口径计失败并在表格 n 列标注（n=120^e）。
- **跨规范 RQ1（论文 Table 1 终稿）**：

| 规范 | 模型 | B0 det/FP | B1 det/FP | p(合规) |
|---|---|---|---|---|
| react19 | DS | 91.0/59.2 | 70.2/8.2 | <0.001 |
| react19 | MX | 94.0/73.5 | 83.6/22.4 | <0.001 |
| airbnb | DS | 63.2/0.0 | 100.0/21.1 | 0.125 |
| airbnb | MX | 94.7/10.5 | 100.0/73.7 | <0.001 |
| agents | DS | 56.2/31.2 | 31.2/6.2 | 0.219 |
| agents | MX | 93.8/93.8 | 81.2/50.0 | 0.039 |
| asvs | DS | 45.0/40.0 | 30.0/5.0 | 0.016 |
| asvs | MX | 85.0/70.0 | 95.0/75.0 | 1.000 |

- **react19 全量 120 McNemar（B0 vs B1）**：DS 违规 p=0.000122（B1 −14/+0）、
  合规 p<1e-5（+25/−0）；MX 违规 p=0.092（−10/+3）、合规 p<1e-5（+26/−1）。
  FP 压制双模型复现；检出过抑制为 DS 特有。
- **M 跨规范迁移**：对齐覆盖 react19 7/12（DS/MX 同）、agents 4/8、airbnb 2/8、
  asvs 0/12（DS 提取器仅 2 规则、0 调用）；M-lite 检出（DS）
  0.913(40)/0.642(120) → 0.125 → 0.0 → 0.0；MX 新规范复现坍塌
  （airbnb 0.0/5 调用、asvs 0.0/0 调用、agents 0.3125/101 调用）。
- 论文：6 页 PDF（含 4 表 + 参考文献引文 + 全部宏化数字），latexmk 零错误。

## 6. 人工复核清单（论文级门槛前置）

- `bench/tools/gen_review_checklist.py` → `docs/review-I6-origins.md`：
  **200 案例**待人工复核（I6 miner emit 后更新；react19 90 / airbnb 34 /
  agents-sdk 24 / asvs 52），逐案例给出 claim、文件与复核口径；
  复核通过改 `origin: handcrafted` + `reviewed_by`，重跑脚本应清零。
- 每次表格生成在 `paper/tables/DIGEST.md` 记录所用 run ID（溯源）。

## 8. 决策记录

- D6-1：B0/B1 双向显著后，论文 RQ1 叙事从「B1 压 FP 而检出不变」改为
  「检出-误报权衡，方向由规范熟悉度调节」；40 案例试点数字保留为 pilot 对照。
- D6-2：M 全量刷新限定 mlite（mverified 的 fail-open 语义已在 I4 固化，
  新规范上重跑留给 I7）；M-lite 含 react19 120 案例刷新。
- D6-3：CI 编译在无 run 产物时使用仓内 tables 副本（有 DIGEST 溯源），
  不把「缺数据编译成 TODO」的产物当正式 PDF。
- D6-4：M 管线跨规范失配如实入稿（不掩盖、不当 bug 修）：aligned 模式防泄漏设计
  下，返回集合=LLM 合成规则（canonical 永不入集合）。对齐覆盖 react19 7/12 →
  agents-sdk 4/8 → airbnb 2/8 → **asvs 0/12（提取器仅产出 2 条规则、0 次审查调用）**，
  M-lite 检出 0.913（react19-40）→ 0.125 → 0.0 → 0.0。结论：知识组织的优势
  是「对齐+路由基建」绑定的，不随规范免费迁移；跨规范对齐改造（嵌入匹配 +
  人工 cues 移植）列为 I7 首项。
- D6-5：react19-mx-mlite（120 案例 × MiniMax thinking 速率 ≈ 11h）超出本迭代
  时限，中途停止（9/120，无 summary 不入表）；react19 的 M 对照由
  deepseek 全量 120 + minimax 规范 40（litmus-minimax-mlite canonical）承担。
- D6-6：react19-mx-b0 的 4 个 provider 失败（timeout×1 + conn-refused×3）
  **不重跑洗白**——按 I4 既定「错误率如实入稿」口径计入失败，表格 n 列加
  ^e 标注并附脚注；选择性重跑至零错误构成轻度选择偏差。
