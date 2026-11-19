"""论文表格自动化（I6）：从 run 产物生成 paper/tables/*.tex。

原则（paper/main.tex 头注）：论文中所有数字必须由 runner 产物重新生成，勿手抄。

- 历史 run（litmus 40 例、budget 阶梯、rq4 仓库梯度）由 paper/canonical-runs.json
  固定 run ID（version-controlled，保证再生成确定性）；
- i6-* run 按命名 i6-{spec}-{ds|mx}-{b0|b1} 自动发现（取含 summary.json 的最新 run），
  跑完后重跑本脚本即刷新表格；
- 缺 run 的单元格写 `--` 并在 DIGEST.md 里标注 TODO，保证编译不中断。

用法：uv run python -m paper.tools.gen_tables
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bench.harness.stats import mcnemar_between_runs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments" / "runs"
REPORTS = ROOT / "experiments" / "reports"
OUT = ROOT / "paper" / "tables"
MANIFEST = ROOT / "paper" / "canonical-runs.json"

MODEL_LABEL = {
    "ds": "DeepSeek-Flash",
    "mx": "MiniMax-M3.1-Flash",
}
SPEC_LABEL = {
    "react19": "React 19",
    "airbnb": "Airbnb JS",
    "agents-sdk": "Agents SDK",
    "asvs": "OWASP ASVS",
}
TAXONOMY_LABEL = {
    "fp-hallucinated-standard": "FP: hallucinated standard",
    "fp-off-scope-true-pattern": "FP: out-of-scope real pattern",
    "fp-rule-overgeneralization": "FP: rule over-generalization",
    "fp-rule-inversion": "FP: rule inversion",
    "fn-should-soft-wording": "FN: SHOULD soft wording",
    "fn-route-review-miss": "FN: route/review miss",
    "fn-static-indistinguishable": "FN: statically indistinguishable",
}


def pct(x: float | None) -> str:
    return "--" if x is None else f"{100 * x:.1f}"


def pfmt(p: float) -> str:
    if p < 0.001:
        return "$<$0.001"
    return f"{p:.3f}"


def tok(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def run_dir(run_id: str) -> Path | None:
    d = RUNS / run_id
    return d if (d / "summary.json").exists() else None


def load(run_id: str) -> dict | None:
    d = run_dir(run_id)
    if d is None:
        return None
    return {
        "dir": d,
        "id": run_id,
        "summary": json.loads((d / "summary.json").read_text(encoding="utf-8")),
        "usage": json.loads((d / "usage.json").read_text(encoding="utf-8")),
    }


def find_i6(spec: str, mk: str, bk: str) -> dict | None:
    best: Path | None = None
    for d in RUNS.glob(f"i6-{spec}-{mk}-{bk}-*"):
        if (d / "summary.json").exists() and (best is None or d.stat().st_mtime > best.stat().st_mtime):
            best = d
    return load(best.name) if best else None


def pinned(section: str, key: str) -> dict | None:
    """按 manifest 固定 ID 取 run（I9）。

    论文数字必须可复现：M-lite / M-verified 的终版 run 一律按 ID 固定，
    不再依赖「mtime 最新的那个」——重跑或拷文件都会让 mtime 排序漂移，
    同一份代码重生成表格可能得到不同数字。
    """
    rid = manifest().get(section, {}).get(key, "")
    return load(rid) if rid else None


def mlite_v3(spec: str, mk: str = "ds") -> dict | None:
    """M-lite 终版 run：先取 manifest 固定 ID，缺失则退回自动发现。"""
    r = pinned("mlite-v3", spec if mk == "ds" else f"{spec}-{mk}")
    return r if r is not None else find_i6(spec, mk, "mlite")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def cell(run: dict | None, key: str) -> str:
    if run is None:
        return "--"
    return pct(run["summary"].get(key))


def n_cell(run: dict | None) -> str:
    """n 列：报告 provider 失败（case error）标记，错误按失败计入指标（I4 口径）。"""
    if run is None:
        return "--"
    n = run["summary"]["n_cases"]
    errs = run["summary"].get("n_case_errors", 0)
    return f"{n}$^{{e}}$" if errs else str(n)


def tokens(run: dict | None) -> str:
    if run is None:
        return "--"
    return tok(run["usage"].get("total_tokens", 0))


def p_b0_b1_compliant(a: dict | None, b: dict | None) -> str:
    if a is None or b is None:
        return "--"
    r = mcnemar_between_runs(a["dir"], b["dir"], subset="compliant")
    return pfmt(r["p_mcnemar_exact"])


# ---------------------------------------------------------------- rq1 cross-spec

def gen_rq2_failopen(m: dict) -> str:
    """RQ2 附表：M-lite vs M-verified（全量跨规范终版 run，按 ID 固定）。

    I9：原 RQ2 表只有 40 案例 pilot，正文「验证关不损检出」的跨规范复现
    （I8 的 8 次 fail-open 复现）没有对应表格。现用 manifest 里固定的
    mlite-v3 / mverified-v3 run 出表，并给出配对 McNemar p。
    """
    rows = [
        "\\begin{tabular}{lrrrrrrr}",
        "\\toprule",
        "Specification & \\multicolumn{3}{c}{M-lite} & \\multicolumn{3}{c}{M-verified} & \\\\",
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}",
        " & Det.\\ \\% & FP \\% & Tokens & Det.\\ \\% & FP \\% & Tokens & $p$ (det.) \\\\",
        "\\midrule",
    ]
    for spec in ("react19", "asvs", "agents-sdk", "airbnb"):
        ml = mlite_v3(spec)
        mv = pinned("mverified-v3", spec)
        # 只出成对单元格：缺任一侧 run 的规范不入表（react19 的 M-verified
        # 未在 routing v3 后重跑，其 pilot 对照在表~\ref{tab:rq2}）。
        if ml is None or mv is None:
            continue
        p = pfmt(mcnemar_between_runs(mv["dir"], ml["dir"], subset="violation")["p_mcnemar_exact"])
        rows.append(
            f"{SPEC_LABEL[spec]} & {cell(ml, 'detection_rate')} & "
            f"{cell(ml, 'false_positive_rate')} & {tokens(ml)} & "
            f"{cell(mv, 'detection_rate')} & {cell(mv, 'false_positive_rate')} & "
            f"{tokens(mv)} & {p} \\\\"
        )
    rows += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(rows)


def gen_rq1_crossspec(m: dict) -> str:
    rows = [
        "\\begin{tabular}{llrrrrrr}",
        "\\toprule",
        " & & \\multicolumn{2}{c}{B0 (no spec)} & \\multicolumn{2}{c}{B1 (full spec)} & & \\\\",
        "Specification & Model & Det.\\ \\% & FP \\% & Det.\\ \\% & FP \\% & $n$ & $p$ (FP) \\\\",
        "\\midrule",
    ]
    total_errs = 0
    for spec in ("react19", "airbnb", "agents-sdk", "asvs"):
        for mk in ("ds", "mx"):
            b0 = find_i6(spec, mk, "b0") if m.get("i6", {}).get("discover", True) else None
            b1 = find_i6(spec, mk, "b1") if m.get("i6", {}).get("discover", True) else None
            for r in (b0, b1):
                if r:
                    total_errs += r["summary"].get("n_case_errors", 0)
            s = b0["summary"] if b0 else None
            n = n_cell(b0) if s else "--"
            p = p_b0_b1_compliant(b0, b1)
            rows.append(
                f"{SPEC_LABEL[spec]} & {MODEL_LABEL[mk]} & "
                f"{cell(b0, 'detection_rate')} & {cell(b0, 'false_positive_rate')} & "
                f"{cell(b1, 'detection_rate')} & {cell(b1, 'false_positive_rate')} & "
                f"{n} & {p} \\\\"
            )
        if spec != "asvs":
            rows.append("\\addlinespace")
    # 覆盖率披露（I9）：全量重跑后基准又增补案例（react19 新增 10 条 mined），
    # 而 B0/B1 run 早于增补——表格须自曝「本 run 覆盖的案例数 < 当前基准规模」，
    # 否则读者会把 n 列当成全量。此处由 run 产物与基准目录实时比对得出。
    gaps = []
    for spec in ("react19", "airbnb", "agents-sdk", "asvs"):
        bench_n = sum(1 for d in (ROOT / "bench" / "cases" / spec).iterdir() if d.is_dir())
        run_ns = {
            find_i6(spec, mk, bk)["summary"]["n_cases"]
            for mk in ("ds", "mx")
            for bk in ("b0", "b1")
            if find_i6(spec, mk, bk)
        }
        if run_ns and max(run_ns) < bench_n:
            gaps.append(f"{SPEC_LABEL[spec]}: {max(run_ns)}/{bench_n}")
    if gaps:
        rows.append(
            "\\multicolumn{8}{l}{\\footnotesize Coverage: the B0/B1 runs predate the final case "
            "expansion ("
            + "; ".join(gaps)
            + " cases covered); the added cases post-date the rerun.} \\\\"
        )
    if total_errs:
        rows.append(
            "\\multicolumn{8}{l}{\\footnotesize $^{e}$ provider-failure cases "
            f"({total_errs} total) counted as failures per the error accounting}} \\\\"
        )
    rows += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(rows)


# ---------------------------------------------------------------- rq2 verification

def gen_rq2(m: dict) -> str:
    rows = [
        "\\begin{tabular}{llrrrrr}",
        "\\toprule",
        "Model & Config & Det.\\ \\% & FP \\% & Tokens & $n$ & $p$ (Mv vs Ml, det.) \\\\",
        "\\midrule",
    ]
    for model_key, group in m.get("litmus40", {}).items():
        ml = load(group.get("mlite", "")) if group.get("mlite") else None
        mv = load(group.get("mverified", "")) if group.get("mverified") else None
        if ml is None and mv is None:
            continue
        p = "--"
        if ml and mv:
            r = mcnemar_between_runs(mv["dir"], ml["dir"], subset="violation")
            p = pfmt(r["p_mcnemar_exact"])
        s = mv["summary"] if mv else (ml["summary"] if ml else {})
        rows.append(
            f"{MODEL_LABEL[model_key]} & M-lite & {cell(ml, 'detection_rate')} & "
            f"{cell(ml, 'false_positive_rate')} & {tokens(ml)} & {s.get('n_cases', '--')} & \\\\"
        )
        rows.append(
            f" & M-verified & {cell(mv, 'detection_rate')} & "
            f"{cell(mv, 'false_positive_rate')} & {tokens(mv)} & {s.get('n_cases', '--')} & {p} \\\\"
        )
        rows.append("\\addlinespace")
    rows = rows[:-1]
    rows += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(rows)


# ---------------------------------------------------------------- rq4 cost

def gen_rq4_ladder(m: dict) -> str:
    ladder = m.get("budget-ladder", {})
    rows = [
        "\\begin{tabular}{lrrr}",
        "\\toprule",
        "Context budget & Det.\\ \\% & FP \\% & Tokens \\\\",
        "\\midrule",
    ]
    for bid, label in (
        ("b1-full", "236K chars (full)"),
        ("b1-120k", "120K chars"),
        ("b1-60k", "60K chars"),
        ("b1-30k", "30K chars"),
    ):
        r = load(ladder.get(bid, "")) if ladder.get(bid) else None
        rows.append(
            f"{label} & {cell(r, 'detection_rate')} & {cell(r, 'false_positive_rate')} & {tokens(r)} \\\\"
        )
    rows += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(rows)


def gen_rq4_repo(m: dict) -> str:
    rows = [
        "\\begin{tabular}{lrrr}",
        "\\toprule",
        "Config & Det.\\ \\% & FP \\% & Tokens \\\\",
        "\\midrule",
    ]
    for rid, label in (
        ("b1", "B1 (full spec)"),
        ("mlite", "M-lite (routed)"),
        ("b3", "B3 (static)"),
    ):
        run_id = m.get("rq4-repo", {}).get(rid, "")
        r = load(run_id) if run_id else None
        rows.append(
            f"{label} & {cell(r, 'detection_rate')} & {cell(r, 'false_positive_rate')} & {tokens(r)} \\\\"
        )
    rows += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(rows)


# ---------------------------------------------------------------- prose macros

def _frac(run: dict | None, key: str) -> str:
    if run is None:
        return "\\textbf{TODO}"
    return f"{run['summary'][key]:.3f}"


def _detpct(run: dict | None) -> str:
    if run is None:
        return "\\textbf{TODO}"
    return f"{100 * run['summary']['detection_rate']:.1f}\\%"


def gen_macros(m: dict) -> str:
    g = m.get("litmus40", {})
    ds_b0 = load(g.get("ds", {}).get("b0", "")) if g.get("ds", {}).get("b0") else None
    ds_b1 = load(g.get("ds", {}).get("b1", "")) if g.get("ds", {}).get("b1") else None
    mx_b0 = load(g.get("mx", {}).get("b0", "")) if g.get("mx", {}).get("b0") else None
    mx_b1 = load(g.get("mx", {}).get("b1", "")) if g.get("mx", {}).get("b1") else None
    ds_ml = load(g.get("ds", {}).get("mlite", "")) if g.get("ds", {}).get("mlite") else None
    ds_mv = load(g.get("ds", {}).get("mverified", "")) if g.get("ds", {}).get("mverified") else None
    ladder = m.get("budget-ladder", {})
    bud_full = load(ladder.get("b1-full", "")) if ladder.get("b1-full") else None
    bud_30k = load(ladder.get("b1-30k", "")) if ladder.get("b1-30k") else None
    repo = m.get("rq4-repo", {})
    repo_b1 = load(repo.get("b1", "")) if repo.get("b1") else None
    repo_ml = load(repo.get("mlite", "")) if repo.get("mlite") else None
    repo_b3 = load(repo.get("b3", "")) if repo.get("b3") else None
    b2 = load(m.get("b2", "")) if m.get("b2") else None

    n_cases = sum(
        1
        for spec_dir in (ROOT / "bench" / "cases").iterdir()
        if spec_dir.is_dir() and not spec_dir.name.endswith("-repo")
        for d in spec_dir.iterdir()
        if d.is_dir()
    )
    # origin 口径（react19 mined 计数入稿防手抄）；I9：origin 分四档，
    # ai-reviewed = AI 起草 + AI 代复核（未真人签核），不得与 handcrafted 混列。
    origin_counts = {"handcrafted": 0, "ai-reviewed": 0, "synthetic": 0, "mined": 0}
    n_react_mined = 0
    for spec_dir in (ROOT / "bench" / "cases").iterdir():
        if not spec_dir.is_dir() or spec_dir.name.endswith("-repo"):
            continue
        for case_dir in spec_dir.iterdir():
            meta = case_dir / "meta.yaml"
            if not meta.exists():
                continue
            text = meta.read_text(encoding="utf-8")
            for o in origin_counts:
                if f"origin: {o}" in text:
                    origin_counts[o] += 1
                    if o == "mined" and spec_dir.name == "react19":
                        n_react_mined += 1
                    break

    # 跨规范误报口径（I9）：摘要必须引用 240 案例全量重跑的数字，而非
    # 40 案例 pilot。此处按 run 产物算出「规范在场使误报下降/上升」的格数，
    # 供摘要与正文直接引用（不手抄）。
    def _fp_pair(spec: str, mk: str) -> tuple[str, str] | None:
        b0 = find_i6(spec, mk, "b0")
        b1 = find_i6(spec, mk, "b1")
        if not b0 or not b1:
            return None
        return (
            f"{100 * b0['summary']['false_positive_rate']:.1f}",
            f"{100 * b1['summary']['false_positive_rate']:.1f}",
        )

    fp_cells_down = 0
    fp_cells_up = 0
    fp_cells_total = 0
    fp_worst_up = ("", 0.0)
    for spec in ("react19", "airbnb", "agents-sdk", "asvs"):
        for mk in ("ds", "mx"):
            pair = _fp_pair(spec, mk)
            if pair is None:
                continue
            fp_cells_total += 1
            if float(pair[1]) < float(pair[0]):
                fp_cells_down += 1
            elif float(pair[1]) > float(pair[0]):
                fp_cells_up += 1
                if float(pair[1]) - float(pair[0]) > fp_worst_up[1]:
                    fp_worst_up = (f"{SPEC_LABEL[spec]}/{MODEL_LABEL[mk]}", float(pair[1]) - float(pair[0]))
    # 「误报被规范压低」的最大降幅（DeepSeek 在 React 上的 59.2→8.2）
    fp_best_down = ("", 0.0)
    for spec in ("react19", "airbnb", "agents-sdk", "asvs"):
        for mk in ("ds", "mx"):
            pair = _fp_pair(spec, mk)
            if pair is None:
                continue
            drop = float(pair[0]) - float(pair[1])
            if drop > fp_best_down[1]:
                fp_best_down = (f"{SPEC_LABEL[spec]}/{MODEL_LABEL[mk]}", drop)
    p_ds = (
        pfmt(mcnemar_between_runs(ds_b0["dir"], ds_b1["dir"], subset="compliant")["p_mcnemar_exact"])
        if ds_b0 and ds_b1
        else "\\textbf{TODO}"
    )
    gap = (
        f"{repo_b1['usage']['total_tokens'] / repo_ml['usage']['total_tokens']:.0f}$\\times$"
        if repo_b1 and repo_ml
        else "\\textbf{TODO}"
    )
    b2_pct = (
        f"{100 * b2['usage']['total_tokens'] / ds_b1['usage']['total_tokens']:.1f}\\%"
        if b2 and ds_b1
        else "\\textbf{TODO}"
    )

    # M 管线跨规范迁移（i6 mlite）：对齐覆盖 + 检出
    def _ml_align(spec: str) -> str:
        r = mlite_v3(spec)
        if r is None:
            return "\\textbf{TODO}"
        diag = r["dir"] / "rules_diagnostic.json"
        a = json.loads(diag.read_text(encoding="utf-8"))["alignment"]
        return f"{a['n_matched']}/{a['n_canonical']}"

    def _ml_det(spec: str) -> str:
        r = mlite_v3(spec)
        if r is None:
            return "\\textbf{TODO}"
        return f"{r['summary']['detection_rate']:.3f}"

    # 提取器 v1（I6 历史 run，manifest 固定）→ RQ2 两版本对比
    def _ml_v1_align(spec: str) -> str:
        rid = m.get("mlite-v1", {}).get(spec, "")
        r = load(rid) if rid else None
        if r is None:
            return "\\textbf{TODO}"
        a = json.loads((r["dir"] / "rules_diagnostic.json").read_text(encoding="utf-8"))["alignment"]
        return f"{a['n_matched']}/{a['n_canonical']}"

    def _ml_v1_det(spec: str) -> str:
        rid = m.get("mlite-v1", {}).get(spec, "")
        r = load(rid) if rid else None
        if r is None:
            return "\\textbf{TODO}"
        return f"{r['summary']['detection_rate']:.3f}"

    def _spec_n(spec: str) -> int:
        return sum(
            1 for d in (ROOT / "bench" / "cases" / spec).iterdir() if d.is_dir()
        )

    lines = [
        "% 由 paper/tools/gen_tables.py 生成；勿手改（重跑脚本即刷新）。",
        f"\\newcommand{{\\benchN}}{{{n_cases}}}",
        f"\\newcommand{{\\nReact}}{{{_spec_n('react19')}}}",
        f"\\newcommand{{\\nAirbnb}}{{{_spec_n('airbnb')}}}",
        f"\\newcommand{{\\nAgents}}{{{_spec_n('agents-sdk')}}}",
        f"\\newcommand{{\\nAsvs}}{{{_spec_n('asvs')}}}",
        f"\\newcommand{{\\benchNHand}}{{{origin_counts['handcrafted']}}}",
        f"\\newcommand{{\\benchNAiRev}}{{{origin_counts['ai-reviewed']}}}",
        f"\\newcommand{{\\benchNSyn}}{{{origin_counts['synthetic']}}}",
        f"\\newcommand{{\\benchNMined}}{{{origin_counts['mined']}}}",
        f"\\newcommand{{\\reactNMined}}{{{n_react_mined}}}",
        # 跨规范误报格数（I9：摘要引用全量口径，不引 pilot）
        f"\\newcommand{{\\xsFpDown}}{{{fp_cells_down}}}",
        f"\\newcommand{{\\xsFpUp}}{{{fp_cells_up}}}",
        f"\\newcommand{{\\xsFpCells}}{{{fp_cells_total}}}",
        f"\\newcommand{{\\xsFpBestDrop}}{{{fp_best_down[0]}}}",
        f"\\newcommand{{\\xsFpBestDropVal}}{{{fp_best_down[1]:.1f}}}",
        f"\\newcommand{{\\xsFpWorstUp}}{{{fp_worst_up[0]}}}",
        f"\\newcommand{{\\xsFpWorstUpVal}}{{{fp_worst_up[1]:.1f}}}",
        f"\\newcommand{{\\dsBzeroDet}}{{{_detpct(ds_b0)}}}",
        f"\\newcommand{{\\dsBzeroFP}}{{{_frac(ds_b0, 'false_positive_rate')}}}",
        f"\\newcommand{{\\dsBoneDet}}{{{_detpct(ds_b1)}}}",
        f"\\newcommand{{\\dsBoneFP}}{{{_frac(ds_b1, 'false_positive_rate')}}}",
        f"\\newcommand{{\\dsMcNemarP}}{{{p_ds}}}",
        f"\\newcommand{{\\mxBzeroFP}}{{{_frac(mx_b0, 'false_positive_rate')}}}",
        f"\\newcommand{{\\mxBoneFP}}{{{_frac(mx_b1, 'false_positive_rate')}}}",
        f"\\newcommand{{\\mliteDetDS}}{{{_frac(ds_ml, 'detection_rate')}}}",
        f"\\newcommand{{\\mverDetDS}}{{{_frac(ds_mv, 'detection_rate')}}}",
        f"\\newcommand{{\\budFullDet}}{{{_frac(bud_full, 'detection_rate')}}}",
        f"\\newcommand{{\\budThirtyKDet}}{{{_frac(bud_30k, 'detection_rate')}}}",
        f"\\newcommand{{\\bTwoDet}}{{{_frac(b2, 'detection_rate')}}}",
        f"\\newcommand{{\\bTwoCostPct}}{{{b2_pct}}}",
        f"\\newcommand{{\\repoGap}}{{{gap}}}",
        f"\\newcommand{{\\bThreeRepoDet}}{{{_frac(repo_b3, 'detection_rate')}}}",
        f"\\newcommand{{\\bThreeRepoFP}}{{{_frac(repo_b3, 'false_positive_rate')}}}",
        f"\\newcommand{{\\mlAlignReact}}{{{_ml_align('react19')}}}",
        f"\\newcommand{{\\mlAlignAgents}}{{{_ml_align('agents-sdk')}}}",
        f"\\newcommand{{\\mlAlignAirbnb}}{{{_ml_align('airbnb')}}}",
        f"\\newcommand{{\\mlAlignAsvs}}{{{_ml_align('asvs')}}}",
        f"\\newcommand{{\\mliteDetAgents}}{{{_ml_det('agents-sdk')}}}",
        f"\\newcommand{{\\mliteDetAirbnb}}{{{_ml_det('airbnb')}}}",
        f"\\newcommand{{\\mliteDetAsvs}}{{{_ml_det('asvs')}}}",
        f"\\newcommand{{\\mlAlignReactVone}}{{{_ml_v1_align('react19')}}}",
        f"\\newcommand{{\\mlAlignAgentsVone}}{{{_ml_v1_align('agents-sdk')}}}",
        f"\\newcommand{{\\mlAlignAirbnbVone}}{{{_ml_v1_align('airbnb')}}}",
        f"\\newcommand{{\\mlAlignAsvsVone}}{{{_ml_v1_align('asvs')}}}",
        f"\\newcommand{{\\mliteDetAgentsVone}}{{{_ml_v1_det('agents-sdk')}}}",
        f"\\newcommand{{\\mliteDetAirbnbVone}}{{{_ml_v1_det('airbnb')}}}",
        f"\\newcommand{{\\mliteDetAsvsVone}}{{{_ml_v1_det('asvs')}}}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- rq3 taxonomy

TAXONOMY_V1_LABEL = {
    "fn-conservative-empty": "FN: conservative empty review",
    "fn-missed-rule": "FN: missed rule",
    "fp-annotated-rule-flag": "FP: annotated rule flagged",
    "fp-flagged-non-annotated": "FP: flagged, rule not annotated",
}


def gen_rq3() -> str:
    """RQ3 表：结构化分类学 v1（全量 16 个 B0/B1 run，非抽样）。

    I9：此前该表由 v0（40 案例 pilot、5 类）生成，而正文已按 v1 叙述
    （六类 / 100 例保守空审查 / 167 例未标注标记）——表与文口径不一致，
    且 caption 写「five configurations」而表体只有 4 列。现统一到 v1。
    """
    data = json.loads((REPORTS / "error-taxonomy-v1.json").read_text(encoding="utf-8"))
    runs = data["runs"]
    classes = [
        "fn-conservative-empty",
        "fn-missed-rule",
        "fp-annotated-rule-flag",
        "fp-flagged-non-annotated",
    ]
    rows = [
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Class & \\multicolumn{2}{c}{DeepSeek-Flash} & \\multicolumn{2}{c}{MiniMax-M3.1-Flash} \\\\",
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}",
        " & B0 & B1 & B0 & B1 \\\\",
        "\\midrule",
    ]
    totals = {c: 0 for c in classes}
    for cls in classes:
        cells = []
        for mk in ("ds", "mx"):
            for bk in ("b0", "b1"):
                n = sum(
                    blk.get("counts", {}).get(cls, 0)
                    for key, blk in runs.items()
                    if key.endswith(f"-{mk}-{bk}")
                )
                totals[cls] += n
                cells.append(str(n) if n else "--")
        if all(c == "--" for c in cells):
            continue
        rows.append(f"{TAXONOMY_V1_LABEL[cls]} & {' & '.join(cells)} \\\\")
    rows.append("\\midrule")
    classified = []
    for mk in ("ds", "mx"):
        for bk in ("b0", "b1"):
            classified.append(
                str(
                    sum(
                        blk.get("n_classified", 0)
                        for key, blk in runs.items()
                        if key.endswith(f"-{mk}-{bk}")
                    )
                )
            )
    rows.append(
        "Classified FP/FN cases (per run) & " + " & ".join(classified) + " \\\\"
    )
    rows += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(rows)


def gen_rq3_pilot_classes() -> str:
    """RQ3 语义分类学（v0，react19 40 案例 pilot，5 个配置）。

    I9：旧表的 caption 写「five configurations」而表体只有 4 列——v0 的
    per_run 实际有 5 个可计数的配置（B0/B1/M-lite/M-verified/B3），另有一份
    第二模型的 M-verified 只留了文字备注（无数值），故以脚注而非列呈现。
    旧表还漏掉了只出现在 B3 / 第二模型列里的两个类（fn-static-indistinguishable、
    fp-rule-inversion），使「六类」与表体 5 行对不上。现按定义全列。
    """
    data = json.loads((REPORTS / "error-taxonomy-v0.json").read_text(encoding="utf-8"))
    per_run = data.get("per_run", {})
    cols = [
        ("B0", "B0"),
        ("B1", "B1"),
        ("M-lite", "M-lite"),
        ("M-verified", "M-verified_fail-open"),
        ("B3", "B3"),
    ]
    rows = [
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Class & " + " & ".join(label for label, _ in cols) + " \\\\",
        "\\midrule",
    ]
    for cls in data["classes"]:
        label = TAXONOMY_LABEL.get(cls, cls)
        counts = []
        for _label, key in cols:
            block = per_run.get(key, {})
            n = 0
            for section in block.values():
                if isinstance(section, dict):
                    n += sum(1 for v in section.values() if v == cls)
            counts.append(str(n) if n else "--")
        rows.append(f"{label} & {' & '.join(counts)} \\\\")
    rows += [
        "\\midrule",
        "\\multicolumn{6}{l}{\\footnotesize The second model's M-verified run is reported in "
        "the text (no per-case class counts were archived).} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "",
    ]
    return "\n".join(rows)


def gen_rq3_per_spec() -> str:
    """RQ3 附表：保守空审查（过抑制）按规范 × 模型的分布。

    正文断言「100 例保守空审查，集中在 DeepSeek B1（React 20 / ASVS 14 /
    Agents SDK 11）」——本表把该断言的证据逐格列出，避免只给一个总数。
    """
    data = json.loads((REPORTS / "error-taxonomy-v1.json").read_text(encoding="utf-8"))
    runs = data["runs"]
    rows = [
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Specification & \\multicolumn{2}{c}{DeepSeek-Flash} & \\multicolumn{2}{c}{MiniMax-M3.1-Flash} \\\\",
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}",
        " & B0 & B1 & B0 & B1 \\\\",
        "\\midrule",
    ]
    for spec in ("react19", "asvs", "agents-sdk", "airbnb"):
        cells = []
        for mk in ("ds", "mx"):
            for bk in ("b0", "b1"):
                n = sum(
                    blk.get("counts", {}).get("fn-conservative-empty", 0)
                    for key, blk in runs.items()
                    if key.startswith(f"{spec}-{mk}-{bk}")
                )
                cells.append(str(n) if n else "--")
        rows.append(f"{SPEC_LABEL[spec]} & {' & '.join(cells)} \\\\")
    rows += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(rows)


# ---------------------------------------------------------------- main

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    m = manifest()
    digest = ["# paper/tables 生成摘要（gen_tables.py）", ""]
    emitted = {
        "rq1-crossspec.tex": gen_rq1_crossspec(m),
        "rq2-verification.tex": gen_rq2(m),
        "rq4-ladder.tex": gen_rq4_ladder(m),
        "rq4-repo.tex": gen_rq4_repo(m),
        "rq3-taxonomy.tex": gen_rq3(),
        "rq3-taxonomy-per-spec.tex": gen_rq3_per_spec(),
        "rq3-pilot-classes.tex": gen_rq3_pilot_classes(),
        "rq2-failopen.tex": gen_rq2_failopen(m),
        "macros.tex": gen_macros(m),
    }
    for name, content in emitted.items():
        (OUT / name).write_text(content, encoding="utf-8", newline="\n")
        digest.append(f"- `{name}` ({len(content.splitlines())} lines)")
    # i6 run 清单（可追溯）
    digest += ["", "## i6 runs used", ""]
    for spec in ("react19", "airbnb", "agents-sdk", "asvs"):
        for mk in ("ds", "mx"):
            for bk in ("b0", "b1"):
                r = find_i6(spec, mk, bk)
                digest.append(f"- i6-{spec}-{mk}-{bk}: {r['id'] if r else 'TODO missing'}")
    (OUT / "DIGEST.md").write_text("\n".join(digest) + "\n", encoding="utf-8", newline="\n")
    print("wrote", ", ".join(emitted), "+ DIGEST.md")


if __name__ == "__main__":
    main()
