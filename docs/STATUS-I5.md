# SpecLens I5 执行记录：真实仓库 RQ4 + 跨规范扩样启动（2026-11-15，进行中）

- 范围：I5 = 240 扩样、真实多仓库 RQ4、论文。本记录覆盖已落地部分；扩样与论文为持续工作。

## 1. I5-② 真实仓库 RQ4（RP 集，已落地）

- **生成器** `bench/tools/gen_repo_cases.py`（确定性，seed 可复现）：6 种子模式
  （R-003/R-007/R-011 × 违规/合规）嵌入 benign React 仓库，3 规模档 ≈1k/10k/50k 行，
  共 18 案例（RP-001…018，目录 `bench/cases/react19-repo/`，共享 react19 规则库，
  loader.spec_name_for_case 剥离 -repo 后缀）。
- **路由 v2**（`engine/route.py`）：无 cues 规则不再全局适用，从 assertion+quote 派生
  路由键（驼峰/点分优先，通用词黑名单）；对齐时联合注入冻结规则的人工 cues
  （rules.yaml v1.3）。**实测：benign 文件路由命中 0.0（30 样本 max 0），目标文件 3–15 条。**
- 诚实注记：5 条 canonical 规则（R-001/002/004/005/009）无对齐孪生（对齐覆盖 7/12 的
  既有局限），其案例在 M 路径下无期望规则可路由——路由 v2 使该缺口显性化（此前靠
  全局规则的偶然覆盖）。LLM 规则合成（提高对齐覆盖）的优先级因此上调。
- B3 于仓库梯度：检出 0.667 / 误报 0.333（静态检查在 repo 尺度的真实水平，对照注记）。

## 2. I5-① 跨规范扩样（已启动）

- **airbnb 规则库 v1 草案**：airbnb-001…008（引用/解构/默认参数/箭头函数/单引号/
  严格相等/多行大括号），引句逐字 8/8；**首批 10 案例**（JS-001…010，5v/5c，
  origin=synthetic 待人工复核）。基准总量：68 案例 / 3/4 规范有样本。
- **agents-sdk 规则库 v1**：agents-001…008（output_type/动态 instructions/guardrails
  并行与阻塞/工具 docstring/FunctionTool 错误处理/每目的地一 handoff/ModelInputData），
  引句逐字 8/8；**首批 8 案例**（PY-001…008，4v/4c）。
- **asvs 规则库 v1**：asvs-V6.2.9/V6.2.12/V1.1.2/V3.3.3/V7.3.1/V7.4.5/V6.5.1/V5.2.1
  （密码长度/泄露检查/输出编码/cookie 前缀/会话超时/管理员吊销/OTP 一次性/上传限长），
  引句逐字 8/8（来源 CSV req_description）；**首批 16 案例**（PY-101…116，8v/8c）。
- **基准终态：248 案例 ≥ 240 目标**（react19 120 = 62 原有 + 30 第二批 + 28 mined；
  asvs 40；airbnb 38；agents-sdk 32；仓库集 18 为 RQ4 辅助口径）。4/4 规范有样本，
  12 条 asvs 规则全库逐字校验通过。全部 AI 起草/挖掘案例 origin 如实标注
  （synthetic/mined），待人工复核后升 handcrafted。

## 3. RQ4 深跑（进行中）

- **已完成**（deepseek-flash × 18 RP 案例，temperature 0）：
  B1 检出 1.0 / 误报 0.0 / **4,214,818 tokens**（18 次调用，每次=规范全文+整个仓库）；
  M-lite 检出 1.0 / 误报 0.333 / **68,382 tokens**（182 次调用，文件级路由 benign 零命中）。
  **同效下 62× 成本差**，且 B1 成本随仓库规模线性放大（1k→50k 档单例 ≈62K→434K tokens）、
  M 有界（路由 benign 零命中）——RQ4 主张的定量实证。
  M-lite 的 3 个误报集中在 R-011-clean 案例（fetch 型 action 被个别规则覆盖时误判），
  与 I4 fp-rule-overgeneralization 同族，扩样时按该类增补合规例。

## 3b. mined 扩量（终态）

扩展 miner 至 12 查询轮换 + 放宽 vetting（before 仅要求 Effect 内建 interval/timeout、
after 出现清理且 before 无清理）：再产出 **8 对**（TS-063…070），mined 总计 **10 对**。
产出率仍低（8/~300 提交）——扩 mined 需更多查询迭代或放宽至 addEventListener 族，
已列为 I6 项。

## 4. 论文（已成稿）

- **paper/main.tex 全文**：Abstract/Intro/Related/Benchmark/Design/Results(RQ1–RQ4)/
  Threats/Conclusion，全部接入实测数字；LaTeX 转义问题已修复（ightarrow、	imes）。
- 双模型对照（deepseek vs MiniMax-M3.1-Flash）与 62× 成本差均已写入。

- `paper/main.tex` 骨架 + `refs.bib`（近邻 7 篇 + 规范来源 4 项）；Results 各节已挂
  I2–I4 实测数字；双模型对照（deepseek vs MiniMax-M3.1-Flash）数据齐备待写入。
