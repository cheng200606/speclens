"""SpecLens 审查引擎：文档 -> 验证过的规则 -> 带证据链的审查报告。

模块流水线（plan.md §2.2）：
ingest -> extract -> verify -> route -> review -> trace
六个模块当前均为接口桩，M2（2027-01-25 起）实现。
"""
