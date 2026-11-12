# SpecLens-Bench 标注指南（DRAFT v0 · M0 骨架）

> 状态：草稿。M1（2026-12-07 起）将扩充为标注指南 v1 并**冻结 react19 规则编号**；
> 当前 R-001…R-005 仅为 5 个种子样本使用的占位规则，编号在指南 v1 前可能调整。

## 1. 判定三分类（verdict）

| verdict | 定义 |
|---|---|
| `violation` | 代码明确违反某条规范规则，能指出违规位置（行级）与规则依据 |
| `compliant` | 代码符合其覆盖范围内的规则要求 |
| `borderline` | 规则是否适用/是否构成违规存在真实争议（如 SHOULD 级规则的边界场景） |

## 2. 难度分级（difficulty）

- `easy`：单条规则、局部明确违反（通常 ≤10 行内可判定）
- `medium`：需要跨行/跨文件理解（数据流、生命周期）
- `hard`：边界场景，或多条规则交互

`hard` 样本在全量集中占比 ≥ 20%（plan.md §2.3.2）。

## 3. react19 种子规则（占位，M1 冻结）

| 规则 ID | 等级 | 类型 | 内容（简述） | 来源 |
|---|---|---|---|---|
| R-001 | MUST | T2 | 异步数据获取使用 `use()`（配合框架缓存/Suspense），而非 `useEffect`+`setState` | react.dev/reference/react/use |
| R-002 | MUST | T2 | 表单动作使用 Actions（`useActionState`/`action` 属性），而非手动 `onSubmit`+setState | react.dev/reference/react/useActionState |
| R-003 | MUST | T5 | `useEffect` 内的订阅/定时器必须返回清理函数 | react.dev/reference/react/useEffect |
| R-004 | MUST | T2 | Hook 只能在组件顶层调用，不得位于条件/循环/嵌套函数中 | react.dev/reference/rules/rules-of-hooks |
| R-005 | SHOULD | T2 | 乐观更新优先使用 `useOptimistic`，而非手动 pending state | react.dev/reference/react/useOptimistic |

## 4. 标注流程（plan.md §2.3.3）

1. 每个样本独立标注：`verdict` + `rule_ids` + 证据行号，写入 `meta.yaml` 的 `annotations`。
2. Phase 0 的 40 条**全量双标**，Cohen's κ ≥ 0.6 方可继续；分歧样本第三方仲裁。
3. 全量集分层抽取 40% 双标；κ < 0.6 则修订本指南并重标。
4. 第二标注人缺位时的降级预案：隔 ≥2 周自我盲标 + 未参与开发的 LLM 第三标，κ 照算并如实报告（plan.md §2.3.3）。
5. `resolved` 字段以仲裁结论为准，是唯一评测依据。

## 5. 样本来源（origin）

- `handcrafted`：按规则手工构造（正/反例对）
- `mined`：GitHub 违规修复对挖掘（修复前=violation、修复后=compliant）
- `synthetic`：LLM 生成 + 人工逐条审核（不进核心判断集）
