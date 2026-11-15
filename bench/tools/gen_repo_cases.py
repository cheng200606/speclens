"""I5 RQ4 · 真实仓库梯度案例生成器（RP-001…RP-018）。

把 6 个种子模式（3 违规 / 3 合规，对应冻结规则 R-003/R-007/R-011）嵌入
程序化生成的 benign React 仓库，构成 3 个规模档（≈1k / 10k / 50k 行）。
确定性：random.seed 由 (pattern, scale) 决定，同参数重跑字节一致。

设计要点（docs/STATUS-I5.md）：
- benign 文件刻意避开全部规则路由键（含路由 v2 从断言派生的英文内容词），
  使 M 路径成本有界——这是「规则找代码」方法的实证设计，报告中如实说明；
- 目标文件嵌在种子位置，检验两种范式在仓库规模下的检出与成本衰减；
- 案例目录 bench/cases/react19-repo/（共享 react19 快照与冻结规则库，
  loader.spec_name_for_case 剥离 -repo 后缀）。

用法：
    uv run python -m bench.tools.gen_repo_cases            # 生成全部 18 案例
    uv run python -m bench.tools.gen_repo_cases --stats    # 仅输出路由/规模统计
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = REPO_ROOT / "bench" / "cases" / "react19-repo"

SCALES = {"1k": 1_000, "10k": 10_000, "50k": 50_000}  # 行数目标（按实测块长折算文件数）

_META_TEMPLATE = """case_id: {case_id}
verdict: {verdict}
difficulty: medium
rule_ids: [{rule_ids}]
origin: synthetic
files:
{files}
annotations:
  - annotator: A
    verdict: {verdict}
    rule_ids: [{rule_ids}]
    notes: "{notes}（AI 起草，待人工复核后可升 handcrafted。）"
resolved:
  verdict: {verdict}
  rule_ids: [{rule_ids}]
"""

# ---------------------------------------------------------------- 种子模式

TARGETS = {
    "poller-no-cleanup": {
        "verdict": "violation",
        "rule_ids": ["R-003"],
        "note": "useEffect 建立 setInterval 轮询但未返回清理函数，endpoint 变化时旧定时器泄漏。",
        "code": '''import { useEffect, useState } from "react";

export function ServicePoller({ endpoint }: { endpoint: string }) {
  const [hits, setHits] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      fetch(endpoint)
        .then((res) => res.json())
        .then(() => setHits((n) => n + 1));
    }, 5000);
    console.log("polling started for", endpoint, id);
  }, [endpoint]);

  return <p>poll hits: {hits}</p>;
}
''',
    },
    "poller-clean": {
        "verdict": "compliant",
        "rule_ids": ["R-003"],
        "note": "useEffect 建立定时器与订阅并返回清理函数，依赖变化与卸载均正确断开。",
        "code": '''import { useEffect, useState } from "react";

export function ServicePoller({ endpoint }: { endpoint: string }) {
  const [hits, setHits] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      fetch(endpoint)
        .then((res) => res.json())
        .then(() => setHits((n) => n + 1));
    }, 5000);
    const onOnline = () => setHits((n) => n + 1);
    window.addEventListener("online", onOnline);
    return () => {
      clearInterval(id);
      window.removeEventListener("online", onOnline);
    };
  }, [endpoint]);

  return <p>poll hits: {hits}</p>;
}
''',
    },
    "promise-inline": {
        "verdict": "violation",
        "rule_ids": ["R-007"],
        "note": "每次渲染新建 Promise 并直接交给 use，未做任何缓存，Suspense 会在重渲染时反复回退。",
        "code": '''import { use } from "react";

type Repo = { stars: number };

export function RepoStars({ repo }: { repo: string }) {
  const data = use(
    fetch(`/api/repos/${repo}`)
      .then((res) => res.json())
  );
  return <span>{(data as Repo).stars} stars</span>;
}
''',
    },
    "promise-cached": {
        "verdict": "compliant",
        "rule_ids": ["R-007"],
        "note": "模块级 Map 缓存 Promise，同参数跨重渲染复用同一实例，交给 use。",
        "code": '''import { use } from "react";

type Repo = { stars: number };
const cache = new Map<string, Promise<Repo>>();

function getCachedRepo(repo: string): Promise<Repo> {
  if (!cache.has(repo)) {
    cache.set(
      repo,
      fetch(`/api/repos/${repo}`).then((res) => res.json())
    );
  }
  return cache.get(repo)!;
}

export function RepoStars({ repo }: { repo: string }) {
  const data = use(getCachedRepo(repo));
  return <span>{data.stars} stars</span>;
}
''',
    },
    "dispatch-deferred": {
        "verdict": "violation",
        "rule_ids": ["R-011"],
        "note": "dispatchAction 在 setTimeout 回调里执行，已脱离任何 Action/Transition 作用域。",
        "code": '''import { useActionState } from "react";

async function pushNote(prev: string | null, note: string): Promise<string | null> {
  const res = await fetch("/api/notes", { method: "POST", body: note });
  return res.ok ? note : prev;
}

export function NotePusher() {
  const [note, dispatchAction, isPending] = useActionState(pushNote, null);

  function handlePush() {
    setTimeout(() => {
      dispatchAction("deferred note");
    }, 800);
  }

  return (
    <div>
      <button onClick={handlePush} disabled={isPending}>Push later</button>
      {note && <p>pushed: {note}</p>}
    </div>
  );
}
''',
    },
    "dispatch-in-action": {
        "verdict": "compliant",
        "rule_ids": ["R-011"],
        "note": "dispatchAction 包在 startTransition（Action）内调用。",
        "code": '''import { useActionState, startTransition } from "react";

async function pushNote(prev: string | null, note: string): Promise<string | null> {
  const res = await fetch("/api/notes", { method: "POST", body: note });
  return res.ok ? note : prev;
}

export function NotePusher() {
  const [note, dispatchAction, isPending] = useActionState(pushNote, null);

  function handlePush() {
    startTransition(() => {
      dispatchAction("queued note");
    });
  }

  return (
    <div>
      <button onClick={handlePush} disabled={isPending}>Push</button>
      {note && <p>pushed: {note}</p>}
    </div>
  );
}
''',
    },
}

PATTERN_ORDER = list(TARGETS)  # poller-no-cleanup, poller-clean, promise-inline, ...

# ---------------------------------------------------------------- benign 模板
# 刻意避开全部路由键（useEffect/Promise/Suspense/context/useActionState/
# dispatchAction/startTransition/useOptimistic/reducer/updater/use(/browser/
# setter/Action…），注释用中文以杜绝英文内容词误命中（I5 路由 v2 的实证前提）。

_NAMES = [
    "Chart", "Ledger", "Summary", "Timeline", "Board", "Panel", "Banner",
    "Footer", "Header", "Card", "Tile", "Badge", "Meter", "Tracker", "Marker",
    "Sheet", "Field", "Picker", "Switch", "Slider", "Label", "Tag", "Chip",
    "Stat", "Row", "Grid", "Pane", "Modal", "Drawer", "Tooltip",
]
_COLORS = ["#2563eb", "#059669", "#d97706", "#7c3aed", "#dc2626", "#0891b2"]


def _benign_component(idx: int, rnd: random.Random) -> str:
    name = f"{_NAMES[idx % len(_NAMES)]}{idx:04d}"
    color = _COLORS[idx % len(_COLORS)]
    kind = idx % 5
    if kind == 0:
        return (
            '''import { useState } from "react";

// 展示面板：受控展开/收起
type __NAME__Props = { title: string; rows: string[] };

export function __NAME__({ title, rows }: __NAME__Props) {
  const [open, setOpen] = useState(false);

  return (
    <section data-component="__NAME__">
      <h3 style={{ color: "__COLOR__" }}>{title}</h3>
      <button onClick={() => setOpen(!open)}>{open ? "收起" : "展开"}</button>
      {open && (
        <ul>
          {rows.map((row, i) => (
            <li key={i}>{row}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
'''.replace("__NAME__", name).replace("__COLOR__", color)
        )
    if kind == 1:
        return (
            '''import { useState } from "react";

// 步进计数器
export function __NAME__({ step = 1 }: { step?: number }) {
  const [value, setValue] = useState(0);

  return (
    <div data-component="__NAME__">
      <span style={{ color: "__COLOR__" }}>当前 {value}</span>
      <button onClick={() => setValue((v) => v + step)}>+{step}</button>
      <button onClick={() => setValue((v) => Math.max(0, v - step))}>-{step}</button>
    </div>
  );
}
'''.replace("__NAME__", name).replace("__COLOR__", color)
        )
    if kind == 2:
        return (
            '''// 纯展示卡片：无状态组件
type __NAME__Props = { label: string; value: number; hint?: string };

export function __NAME__({ label, value, hint }: __NAME__Props) {
  const highlight = value > 100;

  return (
    <div data-component="__NAME__" data-highlight={highlight}>
      <dt>{label}</dt>
      <dd>
        {value.toLocaleString("zh-CN")}
        {hint && <small>{hint}</small>}
      </dd>
      <style>{`dd { border-left: 3px solid __COLOR__; }`}</style>
    </div>
  );
}
'''.replace("__NAME__", name).replace("__COLOR__", color)
        )
    if kind == 3:
        return (
            '''import { useState } from "react";

// 选项卡视图
const TABS = ["概览", "明细", "设置"] as const;

export function __NAME__() {
  const [active, setActive] = useState<(typeof TABS)[number]>("概览");

  return (
    <nav data-component="__NAME__">
      {TABS.map((tab) => (
        <button
          key={tab}
          data-active={tab === active}
          style={{ borderColor: tab === active ? "__COLOR__" : "transparent" }}
          onClick={() => setActive(tab)}
        >
          {tab}
        </button>
      ))}
      <p>当前页：{active}</p>
    </nav>
  );
}
'''.replace("__NAME__", name).replace("__COLOR__", color)
        )
    return (
        '''// 工具函数：纯计算模块
export function clamp__NAME__(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

export function format__NAME__(v: number, digits = 2): string {
  return v.toFixed(digits);
}

export function scale__NAME__(values: number[], factor: number): number[] {
  return values.map((v) => v * factor);
}

export const LIMIT__TAG__ = __LIMIT__;
'''.replace("__NAME__", name).replace("__COLOR__", color)
        .replace("__TAG__", str(idx % 7 + 1)).replace("__LIMIT__", str(rnd.randint(10, 99)))
    )


def _build_files(pattern: str, scale: str, rnd: random.Random) -> dict[str, str]:
    """返回 {相对路径: 内容}。目标文件嵌在种子位置。"""
    # 每个 benign 文件由 3 个子组件拼成（~60 行），文件数按行数目标动态折算
    sample = "".join(_benign_component(i, rnd) for i in range(3))
    est_lines = max(1, sample.count(chr(10)))  # 3 组件/文件
    n_benign = max(4, round(SCALES[scale] / est_lines))
    files: dict[str, str] = {}
    for i in range(n_benign):
        rel = f"code/src/components/Widget{i:04d}.tsx"
        files[rel] = "".join(
            _benign_component(3 * i + k, rnd) for k in range(3)
        )
    target_rel = "code/src/features/Target.tsx"
    # 目标文件插到中部偏后的种子位置（列表保持有序，meta.files 排序输出）
    files[target_rel] = TARGETS[pattern]["code"]
    files["code/src/index.tsx"] = (
        '// 应用入口（节选）：仅导出相关模块\n'
        'export * from "./features/Target";\n'
        f'export {{ default }} from "./components/Widget0000";\n'
    )
    return files


def _case_id(pattern_idx: int, scale: str) -> str:
    scale_idx = list(SCALES).index(scale)
    return f"RP-{pattern_idx * 3 + scale_idx + 1:03d}"


def generate(stats_only: bool = False) -> None:
    import yaml

    from bench.harness.loader import load_cases
    from engine.route import route_rules
    from engine.rule_bank import build_rules

    rules, _ = build_rules(REPO_ROOT / "bench" / "specs" / "react19", "aligned")
    stats: list[dict] = []

    for pi, pattern in enumerate(PATTERN_ORDER):
        spec = TARGETS[pattern]
        for scale in SCALES:
            rnd = random.Random(f"specgens-{pattern}-{scale}")
            files = _build_files(pattern, scale, rnd)
            case_id = _case_id(pi, scale)
            total_lines = sum(c.count("\n") + 1 for c in files.values())

            benign_hits: list[int] = []
            if stats_only:
                for rel, code in files.items():
                    if "features/Target" in rel:
                        target_hits = len(route_rules(rules, code))
                    else:
                        benign_hits.append(len(route_rules(rules, code)))
            stats.append(
                {
                    "case_id": case_id,
                    "pattern": pattern,
                    "scale": scale,
                    "files": len(files),
                    "lines": total_lines,
                    "target_routed_rules": target_hits if stats_only else None,
                    "benign_routed_mean": round(sum(benign_hits) / max(1, len(benign_hits)), 3)
                    if stats_only
                    else None,
                    "benign_routed_max": max(benign_hits) if stats_only and benign_hits else 0,
                }
            )
            if stats_only:
                continue

            case_dir = OUT_ROOT / case_id
            (case_dir / "code").mkdir(parents=True, exist_ok=True)
            for rel, content in files.items():
                out = case_dir / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(content, encoding="utf-8", newline="\n")

            rel_list = "\n".join(f'  - "{rel}"' for rel in sorted(files))
            meta = _META_TEMPLATE.format(
                case_id=case_id,
                verdict=spec["verdict"],
                rule_ids=", ".join(spec["rule_ids"]),
                files=rel_list,
                notes=f"{spec['note']} 规模档 {scale}（{len(files)} 文件 / {total_lines} 行），目标文件嵌于 src/features/Target.tsx。",
            )
            (case_dir / "meta.yaml").write_text(meta, encoding="utf-8", newline="\n")

    if stats_only:
        import json

        print(json.dumps(stats, ensure_ascii=False, indent=1))
        return

    # 生成后校验：loader 可读 + 路由统计
    cases = load_cases(OUT_ROOT)
    print(f"generated {len(cases)} cases under {OUT_ROOT}")
    for c in cases[:2] + cases[-2:]:
        benign = [f for f in c.meta.files if "features/Target" not in f]
        hits = [len(route_rules(rules, c.read_file(f))) for f in benign[:50]]
        print(
            c.meta.case_id,
            c.meta.verdict.value,
            f"files={len(c.meta.files)}",
            f"benign_routed_mean={round(sum(hits)/max(1,len(hits)), 3)}",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="I5 RQ4 仓库梯度案例生成器")
    parser.add_argument("--stats", action="store_true", help="仅输出路由/规模统计（不写文件）")
    args = parser.parse_args()
    generate(stats_only=args.stats)


if __name__ == "__main__":
    main()
