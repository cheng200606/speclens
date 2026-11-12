"""M-verified：完整方法 M（plan.md §2.2）。

extract → verify（三道关）→ 过滤不合格规则 → route → review
→ trace（证据链回填）→ deduplicate/aggregate（聚合去重）。

与 M-lite 的差异即消融对象：verify 过滤 + 证据链 + 聚合。
排除策略（excluded）：
- grounding < 0.6（确定性，离线即可执行）
- exec_test == "fail"（自洽失败；pending=门不可用，保留待人工）
- 存在冲突记录
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from engine.verify import verify_rules

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding, RuleRecord

BASELINE_ID = "m_verified"


@lru_cache(maxsize=4)
def _verified_rules(spec_dir_str: str) -> tuple:
    from engine.extract import extract_rules

    rules = extract_rules(Path(spec_dir_str))
    verified, _report = verify_rules(rules, Path(spec_dir_str))
    return tuple(verified)


def _excluded(rule: RuleRecord) -> bool:
    v = rule.verification
    if v.grounding is not None and v.grounding < 0.6:
        return True
    if v.exec_test == "fail":
        return True
    if v.conflicts:
        return True
    return False


def _spec_dir_for_case(case: Case) -> Path:
    return case.root.parents[2] / "specs" / case.root.parent.name


def predict_case(case: Case, adapter: ModelAdapter) -> list[Finding]:
    from engine.review import review_code
    from engine.trace import aggregate

    spec_dir = _spec_dir_for_case(case)
    rules = [r for r in _verified_rules(str(spec_dir.resolve())) if not _excluded(r)]
    findings = review_code(case, rules, adapter)
    return aggregate(findings, rules)
