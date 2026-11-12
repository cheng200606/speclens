"""SpecLens 数据 schema（plan.md §2.3.4）。

所有基准与引擎产出均经 pydantic 强校验：
- bench/specs/<spec>/spec.yaml      -> SpecMeta
- bench/cases/<spec>/<ID>/meta.yaml -> CaseMeta
- engine 规则库条目                  -> RuleRecord
- LLM 审查输出（JSON）              -> FindingsOutput / Finding

规则类型分类学（plan.md §2.3.1）：
T1 样式 / T2 API 用法 / T3 架构分层 / T4 安全 / T5 并发与资源。
"""

from __future__ import annotations

import datetime as _dt
import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CaseId = str  # 形如 "TS-014"
RuleId = str  # 形如 "R-047"


class Verdict(str, Enum):
    VIOLATION = "violation"
    COMPLIANT = "compliant"
    BORDERLINE = "borderline"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Origin(str, Enum):
    HANDCRAFTED = "handcrafted"
    MINED = "mined"
    SYNTHETIC = "synthetic"


class Annotation(BaseModel):
    """单个标注人的判定（双标记录，plan.md §2.3.3）。"""

    annotator: str
    verdict: Verdict
    rule_ids: list[RuleId] = Field(default_factory=list)
    notes: str = ""


class ResolvedVerdict(BaseModel):
    """仲裁后的最终判定（评测以此为准）。"""

    verdict: Verdict
    rule_ids: list[RuleId] = Field(default_factory=list)


class CaseMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    verdict: Verdict  # 标注人的原始判定（与 resolved 可不一致，保留审计）
    difficulty: Difficulty
    rule_ids: list[RuleId]
    origin: Origin
    files: list[str]
    annotations: list[Annotation] = Field(default_factory=list)
    resolved: ResolvedVerdict

    @field_validator("case_id")
    @classmethod
    def _check_case_id(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Z]{2}-\d{3,}", v):
            raise ValueError(f"case_id 必须形如 'TS-014'，收到 {v!r}")
        return v


class SpecMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_id: str
    name: str
    source_url: str
    snapshot_date: _dt.date | None = None
    license: str
    version: str = ""
    language: str = ""
    freshness_probe: str | None = None  # 新鲜度探测结果文件（plan.md §2.3.1）
    status: Literal["skeleton", "snapshot", "frozen"] = "skeleton"
    notes: str = ""


class SourceSpan(BaseModel):
    """规则在规范原文中的溯源（证据链第一环）。"""

    section: str
    quote: str


class Trigger(BaseModel):
    """规则的适用场景描述与代码特征线索（规则路由的输入）。"""

    scenario: str = ""
    ast_cues: list[str] = Field(default_factory=list)


class RuleVerification(BaseModel):
    """三道验证关的结果（plan.md §2.2）。"""

    grounding: float | None = None  # 规则判定标准 ↔ 原文 entailment 分数
    exec_test: Literal["pass", "fail", "pending"] = "pending"  # 正反例自洽测试
    conflicts: list[RuleId] = Field(default_factory=list)  # 检出的冲突规则


class RuleRecord(BaseModel):
    """引擎规则库条目：engine.extract 产出、engine.verify 补全校验。"""

    id: RuleId
    spec_id: str
    level: Literal["MUST", "SHOULD", "MAY"]  # RFC2119
    category: Literal[
        "T1-style",
        "T2-api-usage",
        "T3-architecture",
        "T4-security",
        "T5-concurrency-resource",
    ]
    trigger: Trigger = Field(default_factory=Trigger)
    assertion: str  # 可判定的检查标准
    source_span: SourceSpan
    pos_example: str = ""  # 正面代码示例
    neg_example: str = ""  # 反面代码示例
    verification: RuleVerification = Field(default_factory=RuleVerification)


class FindingEvidence(BaseModel):
    rule_quote: str = ""  # 引用的规范原文
    explanation: str = ""  # 结论如何被原文支持


class Finding(BaseModel):
    """单条审查结论（带证据链：结论 -> 规则 -> 原文）。"""

    case_id: CaseId | None = None
    file: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    rule_ids: list[RuleId]
    severity: Literal["info", "warning", "error"] = "warning"
    message: str
    evidence: FindingEvidence = Field(default_factory=FindingEvidence)


class FindingsOutput(BaseModel):
    """LLM 结构化输出容器（model_adapter 的校验目标）。"""

    findings: list[Finding] = Field(default_factory=list)
