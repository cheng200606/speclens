"""错误分类学 v1（I7③）：新规范 + react19 全量的 B0/B1 FP/FN 结构化归类。

与 v0（react19-40 五配置、逐条人工判读）互补：v1 用**结构化规则**对 16 个
i6 B0/B1 run（4 规范 × 双模型）做全量程序归类，方法与口径写入 method 字段：

- FN（violation 未报）且 findings==0            → fn-conservative-empty（I6 新类：
  规范在场诱发保守空审查；agents-sdk PY-009 实证）
- FN（violation 未报）且 findings>0             → fn-missed-rule（报了别的规则）
- FP（compliant 报了）且 flagged ∩ annotated=∅  → fp-flagged-non-annotated
  （候选=范围外真实模式/幻觉标准；B0/B1 用文档原生规则标签而非冻结库 ID，
  ID 交集为近似口径，「真实」性确认需人工判读——v0 已对 react19-40 逐条判读）
- FP（compliant 报了）且 flagged ∩ annotated≠∅  → fp-annotated-rule-flag
  （在标注为合规的规则上报警 = 规则反转/误用候选）

用法：uv run python -m bench.tools.gen_taxonomy
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments" / "runs"
OUT = ROOT / "experiments" / "reports" / "error-taxonomy-v1.json"

SPECS = ("react19", "airbnb", "agents-sdk", "asvs")
MODELS = ("ds", "mx")


def _spec_rules(spec: str) -> set[str]:
    bank = yaml.safe_load(
        (ROOT / "bench" / "specs" / spec / "rules.yaml").read_text(encoding="utf-8")
    )
    return {r["id"] for r in bank["rules"]}


def _annotated(spec: str) -> dict[str, set[str]]:
    out = {}
    for d in (ROOT / "bench" / "cases" / spec).iterdir():
        meta = d / "meta.yaml"
        if meta.exists():
            m = yaml.safe_load(meta.read_text(encoding="utf-8"))
            out[m["case_id"]] = set(m["resolved"]["rule_ids"])
    return out


def _latest(spec: str, mk: str, bk: str) -> Path | None:
    best = None
    for d in RUNS.glob(f"i6-{spec}-{mk}-{bk}-*"):
        if (d / "summary.json").exists() and (best is None or d.stat().st_mtime > best.stat().st_mtime):
            best = d
    return best


def classify_run(run_dir: Path, spec: str) -> dict:
    annotated = _annotated(spec)
    valid = _spec_rules(spec)
    per_case: dict[str, dict] = {}
    counts: dict[str, int] = {}
    for line in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        cid = rec["case_id"]
        verdict = rec["resolved_verdict"]
        ann = annotated.get(cid, set())
        if verdict == "violation" and not rec["predicted"]:
            n_find = rec.get("n_findings") or 0
            cls = "fn-conservative-empty" if n_find == 0 else "fn-missed-rule"
        elif verdict == "compliant" and rec["predicted"]:
            raw_p = run_dir / "raw" / f"{cid}.json"
            flagged: set[str] = set()
            if raw_p.exists():
                try:
                    for f in json.loads(raw_p.read_text(encoding="utf-8")):
                        flagged |= set(f.get("rule_ids", []))
                except Exception:
                    pass
            if flagged & ann:
                cls = "fp-annotated-rule-flag"
            else:
                cls = "fp-flagged-non-annotated"
        else:
            continue
        per_case[cid] = {"verdict": verdict, "class": cls}
        counts[cls] = counts.get(cls, 0) + 1
    return {"run": run_dir.name, "n_classified": len(per_case), "counts": counts, "per_case": per_case}


def main() -> None:
    out = {
        "version": "v1",
        "scope": "i6 B0/B1 runs: 4 specs x 2 models (B0) + B1（全量 120/38/32/40 案例）",
        "method": "结构化程序归类（全量，非抽样）；fn-conservative-empty / fn-missed-rule / "
        "fp-off-scope-true-pattern（候选，引句均来自冻结规则=规范背书）/ fp-annotated-rule-flag / "
        "fp-invalid-rule-ref；「真实」性人工抽检另录 sample 字段",
        "runs": {},
    }
    for spec in SPECS:
        for mk in MODELS:
            for bk in ("b0", "b1"):
                d = _latest(spec, mk, bk)
                if d is None:
                    continue
                out["runs"][f"{spec}-{mk}-{bk}"] = classify_run(d, spec)
    OUT.write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    # 汇总
    agg: dict[str, int] = {}
    for r in out["runs"].values():
        for k, v in r["counts"].items():
            agg[k] = agg.get(k, 0) + v
    print(json.dumps(agg, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
