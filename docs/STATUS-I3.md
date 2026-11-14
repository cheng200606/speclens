# SpecLens I3 执行记录：复核入库 + M-verified 退化归因与修复（2026-11-14）

- 依据：`docs/STATUS-I2.md` §3 缺口与 §5 优先级（I3-① 验证关可诊断性、I3-② 用户复核）
- 结论一句话：**复核已完成（40/40 人工确认，TS-028 降为 medium）；M-verified 退化根因坐实为
  门 2 自审假阴性（R-011 被误杀）且门 2 跨运行不稳定；按 plan §2.2 改 fail-open 后
  检出 0.783 → 0.870，与 M-lite 差距缩至 1 个 case；门 2/3 降级为复核信号而非过滤器。**

---

## 1. I3-② 用户复核（已完成）

- 23 条 synthetic 案例全部人工复核：**23/23 通过**，`origin` 全部翻转 `handcrafted`
  → **基准 40 条 100% 人工确认**，解除「synthetic 不进核心判断集」限制。
- 唯一修正：TS-028 难度 hard → medium（泄漏 interval 场景），hard 占比 0.25 → 0.225（9/40），
  测试同步（用户自改）。verdict / rule_ids 零改动。
- 清单存档：`docs/review-I2-synthetic.md`（勾选 + 结论汇总）。pytest 85 passed。

## 2. I3-① M-verified 退化归因（verify_report.json 证据）

I2 观察到的退化（检出 0.913 → 0.783，4 个预测翻转）在本轮重跑中**可复现**（检出 0.7826，
完全一致）。归因（run `litmus-mverified-af708d3d4ed2`，首个带 `verify_report.json` 的 run）：

| 排除原因 | 规则数 | 其中被杀的冻结规则 |
|---|---|---|
| exec-fail（门 2 LLM 自审） | 8 | **R-011**（MUST） |
| conflicts（门 3 LLM 判定） | 3 | **R-007**（MUST） |
| grounding < 0.6（门 1 确定性） | 4 | **R-003**（MUST，引句含 `<CodeStep>` JSX 标记，归一化后得分系统性偏低） |
| 合计 | 13/44 | 31 条存活规则覆盖面骤减 |

**根因坐实**：R-011（"`dispatchAction` must be called from an Action."，快照逐字句，grounding=1.0）
被门 2 判 exec-fail → 静默移出规则库 → 其违规案例 TS-031/TS-040 直接漏检。
门 2 的判据是"模型自合成的反例须被检出且引用本规则 ID、正例须零 finding"——双重自评判据脆弱。

## 3. 修复：fail-open 验证策略（对齐 plan.md §2.2）

plan §2.2 原文是「低分规则进入**人工复核队列**」，此前实现偏离为「直接删除」。修复（commit `I3 fail-open`）：

1. **excluded 仅剩确定性门 1**（grounding < 0.6，可离线复现）；
2. 门 2 exec-fail / 门 3 conflicts → **保留规则 + `review_flags` 标记**（人工复核队列）；
3. 门 2 增加明细捕获（`executability_test_detail`：neg_ok/pos_ok 分腿 + 自合成例的命中 findings），
   随 `verify_report.json` 归档——补上"哪条腿失败"的最后一块可审计性。

### 重跑结果（run `litmus-mverified-4ec0c8febcb8`，40 kept / 4 excluded）

| 配置 | 检出率 | 误报率 | 规则命中 | tokens |
|---|---|---|---|---|
| M-verified（I2，filter 策略） | 0.783 | 0.077 | 0.444 | 399K |
| **M-verified（I3，fail-open）** | **0.870** | 0.154 | **0.600** | 437K |
| M-lite（参照） | 0.913 | 0.154 | 0.714 | 372K |

- **R-011 三案例（TS-014/031/040）全部恢复检出**。
- 与 M-lite 的差异仅剩 TS-029（R-005 手写乐观模式，M-verified 本轮漏检、M-lite 检出；
  单 case 差异，LLM 方差量级）+ TS-035（borderline，不计分）。
- 本轮 R-011 门 2 结果为 **pass**（neg_ok/pos_ok 均 True）——同一规则、同一模型、temperature 0，
  上一轮 fail、本轮 pass。**门 2 自审跨运行不稳定**实锤，进一步支持"只作信号、不作过滤器"。

## 4. 对方法结论（RQ2）的影响

- 验证关以当前实现**不产生检出增益**：M-verified(fail-open) ≈ M-lite（差异 1 case），
  其剩余价值在证据链（trace）、聚合去重与**诊断信号**（grounding 分、门 2 分腿明细、冲突标记）。
- I2 的判读不变：**Go（RQ4 场景）**，RQ2 主线不升级。论文可写的方法学发现：
  「LLM 自审式规则验证作为过滤器会静默移除关键 MUST 规则（本研究实测 3/12），
  应作为人工复核信号而非自动化删除依据」——这本身就是 RQ3 错误分类学的素材。
- 遗留：门 1 对含 JSX 标记引句（R-003）的归一化偏差，会误杀真规则——I4 可改归一化
  （剥离 `<CodeStep …>` 标记后重评分）或调阈值。

## 5. 决策记录

| # | 决策 | 理由 |
|---|---|---|
| D1 | 排除策略改 fail-open（仅门 1 排除） | plan §2.2 原设计即"人工复核队列"；门 2 实测误杀 R-011 且跨 run 不稳定（8→6 个 fail，集合不同） |
| D2 | 门 2/3 结果保留为 review_flags 并全量归档 | 信号有论文价值（RQ3），删除则丢失可审计性 |
| D3 | 门 1 的 `<CodeStep>` 归一化偏差记录但不本轮修 | 修复涉及 tokenizer 细节，影响面需单独评估；已如实标注 |
| D4 | I2 filter 策略的 run 产物不删 | 实验不可变原则；两轮 run 目录并存即对照证据 |

## 6. I3 剩余 → I4

1. RQ4 成本–规模实验（1k/10k/50k 行仓库梯度 + 多规范并发）——主线；
2. 门 1 归一化修复（`<CodeStep>` 剥离）后重测 grounding 分布；
3. B2 (RAG) / B3 (静态检查) 基线；错误分类学（RQ3）；第二模型；240 条扩样。
