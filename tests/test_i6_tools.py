"""I6 工具测试：配置生成器 / 表格自动化 / 复核清单。"""

import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- gen_i6_configs

def test_i6_configs_complete_and_valid():
    """32 份配置（4 规范 × 2 模型 × 4 基线），mlite/mverified 必须 rules_source: aligned。"""
    cfg_dir = REPO / "experiments" / "configs"
    specs = {"airbnb", "agents-sdk", "asvs", "react19"}
    models = {"ds", "mx"}
    baselines = {"b0", "b1", "mlite", "mverified"}
    count = 0
    for path in cfg_dir.glob("i6-*.yaml"):
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        spec, model, bkey = path.stem[len("i6-"):].rsplit("-", 2)
        assert spec in specs and model in models and bkey in baselines
        assert cfg["run_name"] == path.stem
        assert cfg["temperature"] == 0.0
        if model == "mx":
            assert "api_base" in cfg.get("litellm_kwargs", {})
        if bkey in ("mlite", "mverified"):
            assert cfg["rules_source"] == "aligned"
        else:
            assert "rules_source" not in cfg
        count += 1
    assert count == len(specs) * len(models) * len(baselines) == 32


# ---------------------------------------------------------------- gen_tables

def test_gen_tables_tolerates_missing_runs(tmp_path):
    """缺 run 时表格单元格为 --，宏为 TODO 占位，且文件仍可生成。"""
    import sys

    sys.path.insert(0, str(REPO / "paper" / "tools"))
    import gen_tables  # noqa: E402

    manifest = {
        "litmus40": {"ds": {}, "mx": {}},
        "budget-ladder": {},
        "rq4-repo": {},
        "i6": {"discover": False},
    }
    rq1 = gen_tables.gen_rq1_crossspec(manifest)
    assert "\\end{tabular}" in rq1
    assert rq1.count("--") >= 32  # 8 行 × 4 指标列 + p 列
    macros = gen_tables.gen_macros(manifest)
    assert "\\newcommand{\\benchN}" in macros
    assert "TODO" in macros  # 缺 run 的数值宏显式标注，不得静默为 0


def test_canonical_runs_manifest_pins_existing_dirs():
    """清单固化的 run ID 必须真实存在（本地产物；CI 上此测试跳过）。"""
    run_root = REPO / "experiments" / "runs"
    if not (run_root / "litmus-b0-5f5dfcc1e01e").exists():
        import pytest

        pytest.skip("run products not present (CI)")
    manifest = json.loads(
        (REPO / "paper" / "canonical-runs.json").read_text(encoding="utf-8")
    )
    ids = list(manifest["budget-ladder"].values()) + list(manifest["rq4-repo"].values())
    ids.append(manifest["b2"])
    for group in manifest["litmus40"].values():
        ids.extend(group.values())
    # I9：mlite-v1 / mlite-v3 / mverified-v3 的固定 ID 也必须真实存在
    for section in ("mlite-v1", "mlite-v3", "mverified-v3"):
        ids.extend(v for k, v in manifest.get(section, {}).items() if not k.startswith("_"))
    for rid in ids:
        assert (run_root / rid / "summary.json").exists(), rid


# ---------------------------------------------------------------- gen_review_checklist

def test_review_checklist_matches_origin_counts():
    """清单待复核数 = 库内待真人签核案例数（两边口径一致）。

    I9：待复核来源为 synthetic / mined / ai-reviewed 三档（ai-reviewed =
    AI 起草 + AI 代复核，尚缺真人签核）。
    """
    from bench.tools.gen_review_checklist import CASES, PENDING_ORIGINS

    n_origin = 0
    for spec in ("react19", "airbnb", "agents-sdk", "asvs"):
        for case_dir in (CASES / spec).iterdir():
            meta = case_dir / "meta.yaml"
            if meta.exists():
                text = meta.read_text(encoding="utf-8")
                if any(f"origin: {o}" in text for o in PENDING_ORIGINS):
                    n_origin += 1
    checklist = REPO / "docs" / "review-I6-origins.md"
    if not checklist.exists():
        import pytest

        pytest.skip("checklist not generated yet")
    body = checklist.read_text(encoding="utf-8")
    assert body.count("- [ ]") == n_origin


def test_origin_four_tiers_no_ai_reviewed_claim_as_handcrafted():
    """origin 四档口径：AI 代复核的案例不得标为 handcrafted。

    I9 前 TS-018…TS-040（AI 起草 + AI 代人工复核）被标为 handcrafted，
    使论文的「人工标注」计数虚高 23 条。此处锁死迁移后的状态。
    """
    from bench.harness.schemas import CaseMeta

    ai_reviewed = []
    for spec in ("react19", "airbnb", "agents-sdk", "asvs", "react19-repo"):
        for case_dir in sorted((REPO / "bench" / "cases" / spec).iterdir()):
            meta = case_dir / "meta.yaml"
            if not meta.exists():
                continue
            text = meta.read_text(encoding="utf-8")
            m = CaseMeta.model_validate(yaml.safe_load(text))
            if "AI 代人工复核" in text:
                ai_reviewed.append((spec, case_dir.name, m.origin.value))
    assert len(ai_reviewed) == 23
    for spec, cid, origin in ai_reviewed:
        assert origin == "ai-reviewed", f"{spec}/{cid} 应为 ai-reviewed，实为 {origin}"


def test_case_meta_accepts_reviewed_by():
    """reviewed_by 可写回 meta.yaml（I9 前 schema extra=forbid 使复核流程不可执行）。"""
    from bench.harness.schemas import CaseMeta

    d = yaml.safe_load((REPO / "bench" / "cases" / "react19" / "TS-018" / "meta.yaml").read_text(encoding="utf-8"))
    d["reviewed_by"] = "advisor-signoff"
    m = CaseMeta.model_validate(d)
    assert m.reviewed_by == "advisor-signoff"
