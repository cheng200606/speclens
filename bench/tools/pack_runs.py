"""实验产物打包（I9）：把 experiments/runs/ 打成可发布的归档。

背景（docs/LIMITATIONS.md §5）：论文摘要声明「all raw model outputs are
released」，但 experiments/runs/ 被 .gitignore 排除——仓库里实际只有
.gitkeep。该声明在打包流程落地前不成立。本工具把归档做成**可核验**的：

- 只收「论文引用的 run」（paper/canonical-runs.json 里固定的 ID）+ 其余全部
  run 目录（用 --all 收全量，默认只收被引用的）；
- 每个 run 附一份 MANIFEST：run_id / code_digest / n_cases / 检出误报 / token
  计数 / 关键配置摘要，审稿人不用跑模型也能核对论文数字；
- 输出 sha256，供 release 页面引用（论文里的每个数字都能追溯到具体文件）。

用法：
    uv run python -m bench.tools.pack_runs --output dist/          # 论文引用的 run
    uv run python -m bench.tools.pack_runs --output dist/ --all     # 全部 run
    uv run python -m bench.tools.pack_runs --output dist/ --dry-run

产物：
    dist/speclens-runs-<sha>.tar.gz   归档（内含 MANIFEST.json）
    dist/speclens-runs-<sha>.sha256    校验和
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments" / "runs"
MANIFEST = ROOT / "paper" / "canonical-runs.json"


def referenced_run_ids() -> set[str]:
    """canonical-runs.json 里出现的全部 run ID（递归收集字符串值）。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            if node.startswith(("i6-", "litmus-", "rq4-", "validate-")):
                out.add(node)

    walk(data)
    return out


def all_run_ids() -> set[str]:
    return {d.name for d in RUNS.iterdir() if d.is_dir() and (d / "summary.json").exists()}


def run_manifest(run_dir: Path) -> dict:
    """单个 run 的元数据摘要（供审稿人核对论文数字）。"""
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    usage_path = run_dir / "usage.json"
    usage = json.loads(usage_path.read_text(encoding="utf-8")) if usage_path.exists() else {}
    cfg_path = run_dir / "config.resolved.yaml"
    digest = ""
    model = ""
    if cfg_path.exists():
        text = cfg_path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if line.strip().startswith("code_digest:"):
                digest = line.split(":", 1)[1].strip()
            elif line.strip().startswith("model:"):
                model = line.split(":", 1)[1].strip()
    return {
        "run_id": run_dir.name,
        "model": model,
        "code_digest": digest,
        "n_cases": summary.get("n_cases"),
        "n_violation": summary.get("n_violation"),
        "n_compliant": summary.get("n_compliant"),
        "detection_rate": summary.get("detection_rate"),
        "false_positive_rate": summary.get("false_positive_rate"),
        "rule_match_rate": summary.get("rule_match_rate"),
        "n_case_errors": summary.get("n_case_errors"),
        "total_tokens": usage.get("total_tokens"),
        "n_calls": usage.get("n_calls"),
    }


def build(output_dir: Path, include_all: bool, dry_run: bool) -> int:
    ids = all_run_ids() if include_all else referenced_run_ids()
    ids = {i for i in ids if (RUNS / i / "summary.json").exists()}
    if not ids:
        print("[speclens] 没有可打包的 run")
        return 1

    manifest = {
        "project": "SpecLens",
        "note": (
            "Per-run products for the numbers reported in the paper. Each run directory "
            "contains summary.json (metrics), usage.json (token accounting), "
            "results.jsonl (per-case outcomes), config.resolved.yaml (resolved config "
            "incl. code_digest) and raw/ (unparsed model outputs)."
        ),
        "n_runs": len(ids),
        "scope": "all runs" if include_all else "runs referenced by paper/canonical-runs.json",
        "runs": [run_manifest(RUNS / i) for i in sorted(ids)],
    }
    payload = json.dumps(manifest, ensure_ascii=False, indent=1).encode("utf-8")
    tag = hashlib.sha256(payload).hexdigest()[:12]

    if dry_run:
        print(f"[speclens] dry-run: {len(ids)} 个 run，manifest sha={tag}")
        for r in manifest["runs"]:
            print(
                f"  {r['run_id']:44} n={r['n_cases']} det={r['detection_rate']} "
                f"fp={r['false_positive_rate']} tok={r['total_tokens']}"
            )
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    tar_path = output_dir / f"speclens-runs-{tag}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        info = tarfile.TarInfo("MANIFEST.json")
        info.size = len(payload)
        import io

        tar.addfile(info, io.BytesIO(payload))
        for i in sorted(ids):
            tar.add(RUNS / i, arcname=f"runs/{i}")
    digest = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    (output_dir / f"speclens-runs-{tag}.sha256").write_text(
        f"{digest}  {tar_path.name}\n", encoding="utf-8", newline="\n"
    )
    print(f"[speclens] wrote {tar_path} ({tar_path.stat().st_size / 1e6:.1f} MB, {len(ids)} runs)")
    print(f"[speclens] sha256 {digest}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="dist", help="输出目录")
    ap.add_argument("--all", action="store_true", help="打包全部 run（默认只打包论文引用的）")
    ap.add_argument("--dry-run", action="store_true", help="只打印清单，不落盘")
    args = ap.parse_args()
    return build(Path(args.output).resolve(), args.all, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
