"""SpecLens 审查引擎：文档 -> 验证过的规则 -> 带证据链的审查报告。

模块流水线（plan.md §2.2）：
ingest -> extract -> rule_bank -> verify -> route -> review -> trace

状态（2026-11-13，I1 后）：六个模块均已实现并可离线运行，不再是接口桩。
- ingest / extract：确定性章节树与规范句提取（LLM 规则合成顺延至 I2）。
- rule_bank：冻结规则库加载与合成规则 ID 对齐，统一评测命名空间。
- verify：grounding / executability / conflict 三道关（门 2、3 需 adapter）。
- route：基于 ast_cues 的规则主动扫描（tree-sitter AST 顺延至 I2）。
- review / trace：逐规则对照审查、证据链回填、去重聚合。

未落地的真实方法缺口与迭代计划见 docs/STATUS-I1.md。
"""
