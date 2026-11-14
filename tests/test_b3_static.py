"""B3 静态检查基线测试：确定性、零 API，锁定 I4 调优后的行为。"""

from pathlib import Path

from baselines import get_baseline
from bench.harness.loader import load_cases

REPO = Path(__file__).resolve().parent.parent
CASES = load_cases(REPO / "bench" / "cases" / "react19")


def _by_id() -> dict:
    return {c.meta.case_id: c for c in CASES}


def test_b3_registered_and_deterministic():
    b3 = get_baseline("b3_static")
    case = _by_id()["TS-031"]
    first = b3.predict_case(case, None)
    second = b3.predict_case(case, None)
    assert [f.model_dump() for f in first] == [f.model_dump() for f in second]


def test_b3_detects_expected_violations():
    b3 = get_baseline("b3_static")
    cases = _by_id()
    expect = {
        "TS-028": "R-003",  # interval 无清理
        "TS-031": "R-011",  # setTimeout 中 dispatch
        "TS-040": "R-011",
        "TS-027": "R-002",  # 手动 onSubmit
        "TS-032": "R-012",  # updater 依赖 Date.now
        "TS-007": "R-007",  # 内联 fetch promise
        "TS-006": "R-006",  # 工具函数中 use()
        "TS-037": "R-004",  # early return 后调 Hook
        "TS-030": "R-009",  # 读 promise.status
        "TS-034": "R-001",  # Effect 取数
        "TS-001": "R-001",
    }
    for cid, rule in expect.items():
        rules_fired = {rid for f in b3.predict_case(cases[cid], None) for rid in f.rule_ids}
        assert rule in rules_fired, f"{cid} 应触发 {rule}，实际 {rules_fired}"


def test_b3_spares_compliant_cases():
    b3 = get_baseline("b3_static")
    cases = _by_id()
    # 合规案例应零 finding（TS-011 是已知例外：R-008 合规案例代码中
    # 附带 R-007 模式，按 case 级指标计一次 FP——见 STATUS-I4 错误分类学）
    for cid in ("TS-019", "TS-020", "TS-021", "TS-022", "TS-023", "TS-024", "TS-025", "TS-026"):
        assert not b3.predict_case(cases[cid], None), f"{cid} 不应有 finding"


def test_b3_documented_misses():
    b3 = get_baseline("b3_static")
    cases = _by_id()
    # 文档化的静态不可判项：R-005 未实现 / R-007 具名未缓存函数 / R-008 边界归属
    for cid in ("TS-029", "TS-033", "TS-038"):
        assert not b3.predict_case(cases[cid], None), f"{cid} 属文档化漏检"
