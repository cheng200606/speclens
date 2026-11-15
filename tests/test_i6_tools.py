"""I6 工具测试：配置生成器 / 表格自动化 / 复核清单。"""

import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- gen_i6_configs

def test_i6_configs_complete_and_valid():
    """24 份配置（4 规范 × 2 模型 × 3 基线），mlite 必须 rules_source: aligned。"""
    cfg_dir = REPO / "experiments" / "configs"
    specs = {"airbnb", "agents-sdk", "asvs", "react19"}
    models = {"ds", "mx"}
    baselines = {"b0", "b1", "mlite"}
    count = 0
    for path in cfg_dir.glob("i6-*.yaml"):
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        spec, model, bkey = path.stem[len("i6-"):].rsplit("-", 2)
        assert spec in specs and model in models and bkey in baselines
        assert cfg["run_name"] == path.stem
        assert cfg["temperature"] == 0.0
        if model == "mx":
            assert "api_base" in cfg.get("litellm_kwargs", {})
        if bkey == "mlite":
            assert cfg["rules_source"] == "aligned"
        else:
            assert "rules_source" not in cfg
        count += 1
    assert count == len(specs) * len(models) * len(baselines) == 24


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
    for rid in ids:
        assert (run_root / rid / "summary.json").exists(), rid


# ---------------------------------------------------------------- gen_review_checklist

def test_review_checklist_matches_origin_counts():
    """清单待复核数 = 库内 synthetic/mined 案例数（两边口径一致）。"""
    from bench.tools.gen_review_checklist import CASES

    n_origin = 0
    for spec in ("react19", "airbnb", "agents-sdk", "asvs"):
        for case_dir in (CASES / spec).iterdir():
            meta = case_dir / "meta.yaml"
            if meta.exists():
                text = meta.read_text(encoding="utf-8")
                if "origin: synthetic" in text or "origin: mined" in text:
                    n_origin += 1
    checklist = REPO / "docs" / "review-I6-origins.md"
    if not checklist.exists():
        import pytest

        pytest.skip("checklist not generated yet")
    body = checklist.read_text(encoding="utf-8")
    assert body.count("- [ ]") == n_origin
