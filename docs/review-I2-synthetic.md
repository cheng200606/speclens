# I2 synthetic 案例人工复核清单（TS-018…TS-040）

> 复核人：项目作者（人工）。目标：逐条确认 AI 起草案例的 **verdict / rule_ids / difficulty** 是否成立，
> 通过后升 `origin: handcrafted`，解除「synthetic 不进核心判断集」的限制（标注指南 §5）。
> 依据真值源：`bench/specs/react19/rules.yaml`（12 条冻结规则，引句逐字）。
> 在 VS Code 中按 `Ctrl+Shift+V` 打开本文件预览，链接可直接点击跳转。

## 0. 判定标准（30 秒版）

- **violation**：代码确实违反引句原文的 MUST/SHOULD；borderline 只留给「两种读法都站得住」的样本。
- **compliant**：代码满足该规则，且**不是因为刻意回避了规则场景**（要测的是"做对了"，不是"没做"）。
- **difficulty**：easy=单条规则、一眼可判；medium=需要了解 React 19 API 语义；hard=边界条件或多规则交互。
- 拿不准的保持 `borderline`（宁可降级，不可硬判）。

## 1. 逐条清单（23 条，按 ID 顺序）

| ☐ | 案例 | verdict / 难度 | 规则 | 文件 | 复核要点 |
|---|---|---|---|---|---|
| - [ ] | TS-018 | compliant / medium | R-001 | [meta](../bench/cases/react19/TS-018/meta.yaml) · [code](../bench/cases/react19/TS-018/code/StatusPanel.tsx) | use() 读 Map 缓存 Promise + 上层 Suspense；确认这构成 R-001 的"正确做对"而非回避取数场景 |
| - [ ] | TS-019 | compliant / easy | R-002 | [meta](../bench/cases/react19/TS-019/meta.yaml) · [code](../bench/cases/react19/TS-019/code/NameForm.tsx) | form 的 action prop 用法是否正确（reducerAction 收 (prevState, FormData)） |
| - [ ] | TS-020 | compliant / easy | R-003 | [meta](../bench/cases/react19/TS-020/meta.yaml) · [code](../bench/cases/react19/TS-020/code/Heartbeat.tsx) | 定时器与订阅是否都返回清理；依赖数组 [onPing] 变化时清理是否生效 |
| - [ ] | TS-021 | compliant / medium | R-004 | [meta](../bench/cases/react19/TS-021/meta.yaml) · [code](../bench/cases/react19/TS-021/code/Toolbar.tsx) | 两个 Hook 是否都在 early return 之前；条件只影响渲染不影响 Hook 调用 |
| - [ ] | TS-022 | compliant / easy | R-005 | [meta](../bench/cases/react19/TS-022/meta.yaml) · [code](../bench/cases/react19/TS-022/code/LikeButton.tsx) | setter 是否在 startTransition 包裹的 Action 内 |
| - [ ] | TS-023 | compliant / easy | R-006 | [meta](../bench/cases/react19/TS-023/meta.yaml) · [code](../bench/cases/react19/TS-023/code/useTheme.tsx) | useTheme 是否符合自定义 Hook 约定（use 前缀、内部顶层调 use） |
| - [ ] | TS-024 | compliant / medium | R-009 | [meta](../bench/cases/react19/TS-024/meta.yaml) · [code](../bench/cases/react19/TS-024/code/ProfilePage.tsx) | Promise 直接交给 use；Suspense 边界是否在会 suspend 的组件**父级** |
| - [ ] | TS-025 | compliant / medium | R-011 | [meta](../bench/cases/react19/TS-025/meta.yaml) · [code](../bench/cases/react19/TS-025/code/DraftBox.tsx) | dispatchAction 是否包在 startTransition 内 |
| - [ ] | TS-026 | compliant / easy | R-012 | [meta](../bench/cases/react19/TS-026/meta.yaml) · [code](../bench/cases/react19/TS-026/code/TodoList.tsx) | reducer 是否纯（只依据入参；注意按钮里 Date.now 生成 id 是调用侧，不是 reducer 内） |
| - [ ] | TS-027 | violation / medium | R-002 | [meta](../bench/cases/react19/TS-027/meta.yaml) · [code](../bench/cases/react19/TS-027/code/SignupForm.tsx) | 手动 onSubmit+setState 是否确实构成 R-002 的违反（SHOULD 级） |
| - [ ] | TS-028 | violation / hard | R-003 | [meta](../bench/cases/react19/TS-028/meta.yaml) · [code](../bench/cases/react19/TS-028/code/Poller.tsx) | 无清理导致旧 interval 泄漏的论证是否成立；难度 hard 是否合理 |
| - [ ] | TS-029 | violation / medium | R-005 | [meta](../bench/cases/react19/TS-029/meta.yaml) · [code](../bench/cases/react19/TS-029/code/FollowCount.tsx) | 手写乐观+回滚是否算违反 SHOULD 级 R-005；是否应降 borderline |
| - [ ] | TS-030 | violation / hard | R-009 | [meta](../bench/cases/react19/TS-030/meta.yaml) · [code](../bench/cases/react19/TS-030/code/Profile.tsx) | 读 promise.status 分流是否构成"绕过 use"；use 位于条件分支是否需补 R-004 |
| - [ ] | TS-031 | violation / hard | R-011 | [meta](../bench/cases/react19/TS-031/meta.yaml) · [code](../bench/cases/react19/TS-031/code/ReportBug.tsx) | setTimeout 回调中 dispatch 已脱离 Action 作用域——对照 useActionState 快照 Note 段确认 |
| - [ ] | TS-032 | violation / medium | R-012 | [meta](../bench/cases/react19/TS-032/meta.yaml) · [code](../bench/cases/react19/TS-032/code/ChatFeed.tsx) | updater 修改模块级数组 + Date.now 是否明确不纯 |
| - [ ] | TS-033 | violation / hard | R-007 | [meta](../bench/cases/react19/TS-033/meta.yaml) · [code](../bench/cases/react19/TS-033/code/UserCard.tsx) | 未缓存 async 函数是否与快照 🔴 示例同构；与 TS-007（内联 .then）区分度是否足够 |
| - [ ] | TS-034 | violation / hard | R-001, R-003 | [meta](../bench/cases/react19/TS-034/meta.yaml) · [code](../bench/cases/react19/TS-034/code/Dashboard.tsx) | 双规则标注是否都成立（手动取数 R-001 + 无清理/中止 R-003）；缺 AbortController 是否足以判 R-003 |
| - [ ] | TS-035 | borderline / medium | R-007 | [meta](../bench/cases/react19/TS-035/meta.yaml) · [code](../bench/cases/react19/TS-035/code/UserBadge.tsx) | 单槽缓存踢出场景是否真实；borderline 判定你是否认同 |
| - [ ] | TS-036 | borderline / hard | R-010 | [meta](../bench/cases/react19/TS-036/meta.yaml) · [code](../bench/cases/react19/TS-036/code/VoteBar.tsx) | setter 在 await 之后是否确实"可能脱离 Transition"；这是快照没有明说的灰色地带 |
| - [ ] | TS-037 | violation / medium | R-004 | [meta](../bench/cases/react19/TS-037/meta.yaml) · [code](../bench/cases/react19/TS-037/code/Collapsible.tsx) | early return 之后调 Hook——对照引句 "before any early returns" 确认 |
| - [ ] | TS-038 | violation / hard | R-008 | [meta](../bench/cases/react19/TS-038/meta.yaml) · [code](../bench/cases/react19/TS-038/code/Header.tsx) | Suspense 只包住兄弟子树、CurrentTime 在边界外——SSR 失败论证是否成立 |
| - [ ] | TS-039 | violation / medium | R-010 | [meta](../bench/cases/react19/TS-039/meta.yaml) · [code](../bench/cases/react19/TS-039/code/CartCount.tsx) | onClick 直接调 setter 是否明确违反（对照快照 Troubleshooting 段） |
| - [ ] | TS-040 | violation / hard | R-002, R-011 | [meta](../bench/cases/react19/TS-040/meta.yaml) · [code](../bench/cases/react19/TS-040/code/InviteForm.tsx) | 双规则标注是否都成立；R-002 是 SHOULD、R-011 是 MUST，主次是否要调 |

## 2. 每条的三种结论与对应改法

**✅ 通过**（占多数的预期路径）——编辑该案例 `meta.yaml`：

```yaml
origin: handcrafted          # 由 synthetic 改为 handcrafted
    notes: "…原注…（2026-11-14 人工复核通过。）"   # 追加复核记录
```

**✏️ 修正**——同步改 `verdict` / `rule_ids` / `difficulty`（注意 `annotations` 与 `resolved` 两处一致），
`origin: handcrafted`，notes 写明修正内容。

**❌ 否决**——删除整个案例目录 `bench/cases/react19/TS-0xx/`（规则 ID 永不复用，目录删除即可），
并在本文件下方「复核结论」表记录理由。

> ⚠️ 只翻转 `origin` 不会影响任何测试；但**改 verdict 或删目录**会破坏
> `tests/test_loader.py` 与 `tests/test_agreement.py` 中按当前基准硬编码的计数
> （40 条 / 23v-13c-4b / hard 0.25）——改完让 agent 同步这两个文件并跑 `uv run pytest`。

## 3. 复核结论汇总（完成后填）

- 复核日期：＿＿＿＿
- 通过 ＿ 条；修正 ＿ 条（TS-＿＿）；否决 ＿ 条（TS-＿＿，理由：＿＿＿）
- 完成后运行：`uv run python -m bench.harness.agreement --root .`
  → origin 分布应显示 synthetic 归零；`uv run pytest` 应保持全绿。
