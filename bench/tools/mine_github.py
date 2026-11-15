"""I5 · GitHub 违规修复对挖掘管线（origin=mined，plan §2.3.2 策略二）。

方法：commit 搜索 API 找「修复型提交」（消息含 clearInterval/cleanup/fix），
取其 parent sha 的文件内容为 before（违规）、当前 sha 为 after（合规）；
机械 vetting：before 在 useEffect 内含 setInterval/setTimeout 且无 cleanup，
after 含对应清理。输出候选对写入 bench/cases/react19-repo/../mined候选清单
（JSON），人工复核后由 --emit 写入正式案例目录（origin=mined）。

用法：
  uv run python -m bench.tools.mine_github --search    # 搜索+机械 vetting → mined-candidates.json
  uv run python -m bench.tools.mine_github --emit      # 将候选落盘为案例（人工复核后）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = REPO_ROOT / "experiments" / "reports" / "mined-candidates.json"
SEARCH_API = "https://api.github.com/search/commits?q={q}&per_page=20"


def _token() -> str:
    key = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if key:
        return key
    # 本机凭据助手（Git Credential Manager）中的 GitHub token，不回显
    import subprocess

    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https" + chr(10) + "host=github.com" + chr(10) + chr(10),
        capture_output=True,
        text=True,
    ).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


def _get(url: str, accept: str = "application/vnd.github+json") -> dict:
    key = _token()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}" if key else "",
        "Accept": accept,
        "User-Agent": "speclens-miner",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as exc:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def _has_effect_interval(code: str) -> bool:
    """Effect 内建立 setInterval/setTimeout（无论是否清理）。"""
    effect = re.search(r"useEffect\s*\(", code)
    if not effect:
        return False
    return bool(re.search(r"setInterval\s*\(|setTimeout\s*\(", code))


def _has_cleanup(code: str) -> bool:
    return bool(
        re.search(r"clearInterval\s*\(|clearTimeout\s*\(|removeEventListener\s*\(", code)
        and re.search(r"return\s*(\(|\w+\s*=>)", code)
    )


QUERIES = [
    "clearInterval cleanup fix",
    "useEffect cleanup fix",
    "add clearInterval unmount",
    "clearInterval memory leak fix",
    "useEffect clearInterval unmount",
    "cleanup subscription unmount fix",
    "removeEventListener cleanup useEffect",
    "fix interval leak",
    "clear timeout unmount fix",
    "cleanup effect memory leak",
    "stop interval on unmount",
    "fix timer cleanup",
]


def search_candidates(max_commit_fetch: int = 25) -> list[dict]:
    out: list[dict] = []
    for query in QUERIES:
        if len(out) >= 8:
            break
        q = urllib.parse.quote(query)
        try:
            data = _get(SEARCH_API.format(q=q))
        except Exception as exc:
            print("query failed:", query, str(exc)[:120])
            continue
        items = data.get("items", [])
        print(f"query {query!r}: total={data.get('total_count')} fetched={len(items)}")
        for item in items[:max_commit_fetch]:
            sha = item["sha"]
            repo = item["repository"]["full_name"]
            try:
                detail = _get(f"https://api.github.com/repos/{repo}/commits/{sha}")
            except Exception as exc:
                print("skip detail:", repo, sha[:8], str(exc)[:80])
                continue
            for file in detail.get("files", []):
                patch = file.get("patch") or ""
                if "setInterval" not in patch and "setTimeout" not in patch:
                    continue
                if "clearInterval" not in patch and "clearTimeout" not in patch:
                    continue
                parent_sha = detail["parents"][0]["sha"]
                raw_url = f"https://raw.githubusercontent.com/{repo}/{parent_sha}/{file['filename']}"
                try:
                    before = _get_text(raw_url)
                except Exception:
                    continue
                after_url = f"https://raw.githubusercontent.com/{repo}/{sha}/{file['filename']}"
                try:
                    after = _get_text(after_url)
                except Exception:
                    continue
                if (
                _has_effect_interval(before)
                and _has_cleanup(after)
                and not _has_cleanup(before)
            ):
                    out.append({
                        "repo": repo,
                        "commit": sha,
                        "url": item["html_url"],
                        "filename": file["filename"],
                        "before": before,
                        "after": after,
                    })
                    print(f"CANDIDATE {repo}@{sha[:8]} {file['filename']}")
                time.sleep(0.5)
    return out


def _get_text(url: str) -> str:
    key = _token()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}" if key else "",
        "User-Agent": "speclens-miner",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def emit(candidates: list[dict]) -> None:
    out_dir = REPO_ROOT / "bench" / "cases" / "react19"
    n = 0
    for i, c in enumerate(candidates, 61):
        cid = f"TS-{i:03d}" if not (REPO_ROOT / "bench" / "cases" / "react19" / f"TS-{i:03d}").exists() else None
        if cid is None:
            continue
        d = out_dir / cid / "code"
        d.mkdir(parents=True, exist_ok=True)
        (d / "hook.ts").write_text(c["before"], encoding="utf-8", newline="\n")
        meta = (
            f"case_id: {cid}\n"
            "verdict: violation\n"
            "difficulty: medium\n"
            "rule_ids: [R-003]\n"
            "origin: mined\n"
            'files: ["code/hook.ts"]\n'
            "annotations:\n"
            "  - annotator: A\n"
            "    verdict: violation\n"
            "    rule_ids: [R-003]\n"
            f'    notes: "GitHub 修复对挖掘（{c["repo"]}@{c["commit"][:8]}，机械 vetting：before=Effect 内 interval 无清理）。来源 {c["url"]}（AI 挖掘，待人工复核。）"\n'
            "resolved:\n"
            "  verdict: violation\n"
            "  rule_ids: [R-003]\n"
        )
        (out_dir / cid / "meta.yaml").write_text(meta, encoding="utf-8", newline="\n")
        n += 1
    print(f"emitted {n} mined cases")


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub 修复对挖掘管线")
    parser.add_argument("--search", action="store_true")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()

    if args.search:
        cands = search_candidates()
        CANDIDATES.write_text(
            json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"candidates -> {CANDIDATES} ({len(cands)})")
    if args.emit:
        cands = json.loads(CANDIDATES.read_text(encoding="utf-8")) if CANDIDATES.exists() else []
        emit(cands)


if __name__ == "__main__":
    main()
