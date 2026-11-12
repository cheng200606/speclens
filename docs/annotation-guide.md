# SpecLens-Bench 标注指南 v1（2026-11-13 冻结）

> **v1 变更**：react19 规则编号 **R-001…R-005 冻结**；每条规则附快照原文引句（溯源）；
> 确立跨规范编号政策与其他规范命名空间。本指南对应快照：见各 `bench/specs/<id>/snapshot/manifest.yaml`。

## 1. 判定三分类（verdict）

| verdict | 定义 |
|---|---|
| `violation` | 代码明确违反某条规范规则，能指出违规位置（行级）与规则依据 |
| `compliant` | 代码符合其覆盖范围内的规则要求 |
| `borderline` | 规则是否适用/是否构成违规存在真实争议（如 SHOULD 级规则的边界场景） |

评测只使用 `resolved` 字段（仲裁结论）。borderline 不进主指标（metrics.py 已实现单列）。

## 2. 难度分级（difficulty）

- `easy`：单条规则、局部明确违反（通常 ≤10 行内可判定）
- `medium`：需要跨行/跨文件理解（数据流、生命周期）
- `hard`：边界场景，或多条规则交互

`hard` 样本在全量集中占比 ≥ 20%（plan.md §2.3.2）。

## 3. react19 规则（v1 冻结编号）

规则类型分类学：T1 样式 / T2 API 用法 / T3 架构分层 / T4 安全 / T5 并发与资源。
每条规则的 `source` 均指 `bench/specs/react19/snapshot/` 内文件（2026-11-13 抓取，源仓库 pin `46a54e059272`）。

| 规则 ID | 等级 | 类型 | 断言（assertion） | 快照原文引句 |
|---|---|---|---|---|
| R-001 | SHOULD | T2 | 组件内取数优先 `use()`（配合框架缓存/Suspense），而非 `useEffect`+`setState` 手动取数 | "Before `use`, a common approach was to fetch data in an Effect and update state when the data arrives. Compared to `use`, this approach requires managing loading and error states manually."；"…why fetching in an Effect is **discouraged**" |
| R-002 | SHOULD | T2 | 表单提交/表单动作使用 Actions（`useActionState`、`action` 属性）处理，而非手动 `onSubmit`+setState | "`useActionState` is a React Hook that lets you update state with side effects using Actions." |
| R-003 | MUST | T5 | `useEffect` 中建立订阅/连接/定时器的，必须返回清理函数（cleanup） | "It **should return a *cleanup function*** with cleanup code that disconnects from that system."；"When your component is removed from the page, your Effect will disconnect one last time." |
| R-004 | MUST | T2 | Hook 只能在组件函数体顶层（early return 之前）或自定义 Hook 顶层调用 | "**Don't call Hooks inside loops, conditions, nested functions, or `try`/`catch`/`finally` blocks.** Instead, always use Hooks at the top level of your React function, before any early returns." |
| R-005 | SHOULD | T2 | 异步操作的乐观更新使用 `useOptimistic` 实现 | "`useOptimistic` is a React Hook that lets you optimistically update the UI." |

**Grounding 预警（写给验证模块/标注人）**：R-001/R-002/R-005 的原文是"描述性/不鼓励"措辞而非强制句——
预期 grounding 分低，属于 engine.verify（验证关 1）的好案例；TS-005（borderline）正是 R-005 的边界样例，保留。
R-003/R-004 原文为明确规范句，grounding 应接近满分。

## 4. 其他规范的规则编号政策（M1 生效）

- 每份规范独立命名空间：`agents-xxx`、`asvs-xxx`、`airbnb-xxx`（react19 用 `R-xxx` 历史遗留）。
- 规则编号一经分配**永不复用**；作废规则标 `deprecated` 并保留条目。
- 新规则必须附 `source`（快照文件 + 章节/行）与 RFC2119 等级（MUST/SHOULD/MAY）。
- 规则来源统一从快照提取，禁止凭记忆写规则（与新鲜度探测同源，保证版本一致）。

## 5. 样本来源（origin）

- `handcrafted`：按规则手工构造（正/反例对）
- `mined`：GitHub 违规修复对挖掘（修复前=violation、修复后=compliant）
- `synthetic`：LLM 生成 + 人工逐条审核（不进核心判断集）

## 6. 标注流程与质量保证（plan.md §2.3.3）

1. 每个样本独立标注：`verdict` + `rule_ids` + 证据行号，写入 `meta.yaml` 的 `annotations`。
2. Phase 0 的 40 条**全量双标**，Cohen's κ ≥ 0.6 方可继续；分歧样本第三方仲裁。
3. 全量集分层抽取 40% 双标；κ < 0.6 修订本指南并重标。
4. 第二标注人缺位的降级预案：隔 ≥2 周自我盲标 + 未参与开发的 LLM 第三标，κ 照算并如实报告。
5. `meta.annotations` 保留原始判定（可与 resolved 不一致），用于标注一致性审计。

## 7. 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0 (DRAFT) | 2026-11-12 | 骨架：三分类、难度、R-001…R-005 占位 |
| v1 | 2026-11-13 | 冻结 react19 R-001…R-005；逐条快照引句；跨规范编号政策；grounding 预警 |
