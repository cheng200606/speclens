# SpecLens I4 执行记录：门 1 修复、B2/B3 基线、RQ4 阶梯、错误分类学（2026-11-15）

- 依据：`docs/STATUS-I3.md` §6 I4 清单
- 结论一句话：**门 1 误杀根因修正（句中列表符拼接，44/44 grounding=1.0）；B3 静态基线零成本
  追平 B1（检出 0.870 / 误报 0.077）；RQ4 阶梯证实全文基线随预算暴跌（120K 即 -30pp）；
  B2 检索用 B1 的 1.3% tokens 达 0.478——『检索覆盖由命中决定』获得实证。**

---

## 1. I4-② 门 1 修复（归因修正）

I3 曾把 R-003 被误杀归因为 `<CodeStep>` JSX 标记——**该假设错误**。真实根因有两层：

1. **句中列表符拼接**：引擎提取器把跨列表项的多句引句用 `- ` 拼接成引句
   （如 `"system. - It should return..."`），而 `_norm` 只剥离行首列表符——
   规范文本侧（列表符在行首，已剥）与引句侧（句中，未剥）永不相等，
   4 条规则（X-018/R-003/X-028/X-033）`quote_in_spec` 恒 False。
2. **跨语言重叠死权重 + 等级措辞张力**（叠加项）：中文断言 vs 英文引句的词面重叠恒 0
   却占 0.3 权重；引句 "It **should** return a cleanup function" 是 React 文档教程语气，
   冻结规则判 MUST 属标注人裁量，原 `_level_consistent` 硬扣 0.2。

修复（`engine/verify.py`）：`_MID_BULLET` 句中列表符剥离；跨语言时权重重归一
（quote 0.5 + level 0.5）；等级检查区分「教程式 should（容忍 + note）」与
「软建议词 prefer/avoid（MUST 声明 = 过度声明，仍判 False）」。验证：**44/44 规则
grounding = 1.0，n_flagged = 0**（原 4 条被排除）。两个测试按新不变量同步（防回归）。

## 2. I4-③ B2 / B3 基线（补齐 plan §2.4 全套 B0–B4 中的 B2/B3）

### B3 静态检查（`baselines/b3_static.py`，零 LLM 零 API）

12 条冻结规则中 9 条可实现确定性启发式（R-005 无静态特征不实现）。
调优后（注释剥离 / return 作用域限制到同函数 / any-return-before-hook 语义 /
R-006 调用上下文检查 / R-008 仅认 `use(browser)` 模式）：

| 指标 | B3 | B1（全文 LLM） |
|---|---|---|
| 检出率 | **0.870**（20/23） | 0.870 |
| 误报率 | **0.077**（1/13） | 0.077 |
| 规则命中率 | **0.95** | —（基线不引用规则 ID） |
| tokens | **0** | 2.38M |

文档化漏检：TS-029（R-005 无静态特征）、TS-033（未缓存具名函数与缓存读取静态不可分）、
TS-038（Suspense 边界归属）。唯一 FP：TS-011（见 §4，属基准标注粒度问题）。
**RQ2/RQ4 含义：规则集已知时，把规范编译成静态检查器比全文 LLM 基线便宜无穷倍且同效。**

### B2 检索基线（`baselines/b2_rag.py`，纯 Python BM25，无向量库）

top-6 段落 + 单次审查：**检出 0.478 / 误报 0.077 / 31.9K tokens（B1 的 1.3%）**。
「代码找规则」范式的覆盖由词面命中决定——52% 漏检实证了与 M（规则找代码）的论文卖点差异。

## 3. I4-① RQ4 规格预算阶梯（B1 × 3 档 `spec_max_chars`，deepseek-flash × 40 cases）

| 预算 | 纳入文件 | 检出率 | 误报率 | tokens |
|---|---|---|---|---|
| 全文 236,158 字符（B1 原配置） | 6/6 | 0.870 | 0.077 | 2,376,388 |
| 120,000 | 3/6 | **0.565** | 0.077 | 917,000 |
| 60,000 | 2/6 | **0.435** | 0.077 | 482,333 |
| 30,000 | 1/6 | **0.217** | 0.000 | 56,636 |

**RQ4 失效模式定量成立**：120K 字符预算（≈128K-token 模型的实用档）检出即跌 30pp；
30K 档（多规范并发场景的均摊预算）只剩 0.217。误报率全程不升——截断只杀检出，
因为模型只对看得到的条文负责。全文基线的有效性**完全依赖「塞得下」**，
其成本随（规范数 × 规范长度 × 仓库规模）线性放大，而 B3 为 0、B2 为 1.3%、M-lite 为 16%。

## 4. I4-④ 错误分类学 v0（RQ3）

产物：`experiments/reports/error-taxonomy-v0.json`（6 类 × 5 方法逐 case 归类）。要点：

1. **fp-hallucinated-standard**（B0 的 7 FP 中 6 个）：zero-shot 用通用工程想象
   替代规范条文；规范在场（B1/M）后清零——误报率 0.539 → 0.077 的机制解释。
2. **fp-off-scope-true-pattern**（TS-011，全部 5 个方法一致"误报"）：案例标 R-008 合规，
   但代码含真实的 R-007 违规模式（内联未缓存 promise）——**基准标注粒度问题而非方法错误**，
   扩样前人工定夺（补标注或改代码）。
3. **fp-rule-overgeneralization**（TS-008，M-lite/M-verified 独有）：逐规则审查缺全文语境，
   把规范要求（模块级缓存）当风险——逐规则范式的语境代价。
4. **fn-should-soft-wording**（TS-001/027/029 对 LLM 基线）：SHOULD/描述性措辞不触发
   违规判定——"遵守不稳定"的主要形态在漏报方向，且 TS-001 只被 B3 静态命中。
5. **fn-route-review-miss**（TS-016 对 M 路径）/ **fn-static-indistinguishable**（B3 三条）。

## 5. 阻塞与顺延

- **第二模型**：需第二个 API key（用户提供后接 litellm 即可，配置模式已就绪）。
- **240 条扩样**：非单次会话可完成；TS-011 标注修正优先于扩样。
- run 产物目录：`litmus-b3-*`、`litmus-b2-*`、`litmus-b1-budget{120k,60k,30k}-*`；
  汇总报告 `experiments/reports/litmus-real-2026-11-15.md`。

## 6. 决策记录

| # | 决策 | 理由 |
|---|---|---|
| D1 | 等级张力降级为 note 而非扣分 | R-003 实证：教程式 should + 冻结 MUST 属标注人裁量；过度声明（软建议词 + MUST）仍判 False |
| D2 | B3 规则引句直接取自 rules.yaml | 静态检查器由规范编译而来是其定义使然；论文表述须与「未见规范」前提区分 |
| D3 | make_report 对 b3_static 不打 NON-SCIENTIFIC | B3 无随机成分，mock adapter 仅占位 |
| D4 | RQ4 用字符预算阶梯而非真实多仓库 | 现有 harness 以 case 为单位；预算阶梯是"多规范/小上下文"失效模式的等价量化，真实仓库嵌入留 I5 |
| D5 | TS-011 标注问题只记录不擅改 | 基准真值变更须人工定夺 |

---

## 7. 追记（2026-11-15：用户两项决议落地）

1. **TS-011 口径定夺**：选项 (b)——代码改为模块级缓存 promise（`SuspenseStatus.tsx`），
   消除范围外 R-007 模式；verdict/rule_ids 不变（R-008 合规）。meta 注明修订史。
   连带修复：`code_digest` 原不含 `bench/cases/**`，基准内容修订不产生新归档目录
   （被防覆盖护栏误拦）——已把 case 元数据与代码纳入摘要。B3 复跑（新 digest）：
   **检出 0.870 / 误报 0.000 / 规则命中 0.95 / 零 token**——静态基线误报清零。
   历史 run 归档保留（旧 digest 可追溯修订前状态）。
2. **第二模型 = MiniMax**：锁定版 litellm 1.109.1 原生支持 `minimax/` 前缀
   （OpenAI 兼容路由，模型 MiniMax-M2.1/M2.1-lightning/M2；M2.5 需升级 litellm，暂不采用）。
   已建 `litmus-minimax-{b0,b1,mlite,mverified}.yaml`（中国端点 api.minimaxi.com/v1、
   temperature 0、M 路径 rules_source=aligned；thinking 无关闭开关，组内一致），
   `env.py`/`.env.example` 已加 MINIMAX_API_KEY 映射。**待用户把 key 填入 .env 后**
   按 `docs/reproduce.md` §7 冒烟 + 全量四配置 + 新鲜度探测。
3. RQ3 遗留项收口：`fp-off-scope-true-pattern` 类随 TS-011 修订消除（taxonomy JSON 已记决议）。

## 8. 追记二（2026-11-15：双模型对照完成）

第二模型 = **MiniMax-M3.1-Flash**（配置里的 M2.1 被服务端弃用 err 2069，/v1/models 实测后改选；
Token Plan key 在 OpenAI 兼容路由上可用）。四配置 + 4 规范探测全部完成。

| 配置 | deepseek-flash 检出/误报 | MiniMax-M3.1-Flash 检出/误报 |
|---|---|---|
| B0 | 0.913 / 0.539 | 1.000 / 0.615 |
| B1 | 0.870 / 0.077 | 0.913 / 0.231 |
| M-lite | 0.913 / 0.154 | 0.870\* / 0.923 |
| M-verified(fail-open) | 0.870 / 0.077 | 1.000\* / 0.923 |
| B3 静态 | 0.870 / 0.000 | n/a（无模型） |

\* 含 case errors：mlite 4/40（TS-029/033/038 计 FN + TS-035 borderline；schema 三次重试均缺字段），
mverified 1/40。错误率如实报告。

跨模型发现：①检出侧 MiniMax 全面更强（M-verified 1.0）；②误报侧高度异质——M 路径 0.923 vs 0.154，
且出现新类 **fp-rule-inversion**（把 R-009 反向用成"要求补 status/value"）；③schema 脆弱率 10%；
④新鲜度跨模型不同：asvs 0.70（部分未见）vs deepseek 0.95——第二模型在 asvs 上更接近论文的 unseen 前提。
工程修复：runner fail-soft（单 case 异常不再击穿长 run，errors.json + n_case_errors）、probe --api-base
（MiniMax 中国区 key 绑定）、tenacity 补依赖（litellm 重试路径锁定树缺失）。产物：
`experiments/reports/litmus-minimax-2026-11-15.md`。
