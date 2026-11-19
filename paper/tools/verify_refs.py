"""参考文献核验（I9）：refs.bib 每条条目与 arXiv 官方记录逐字比对。

背景（docs/LIMITATIONS.md §1）：I9 之前 refs.bib 的 5 条学术文献全部是
`author={TODO}` + **改写过的标题**——指向真实论文但无法按引用找到原文。
本工具把「引用可核验」变成 CI 可检查的门：

- 解析 refs.bib 的每条条目，抽出 arXiv id 与题名；
- 拉取 arXiv API 记录（export.arxiv.org/api/query），逐字比对题名；
- 作者列表与 bib 中声明的作者逐一核对（bib 作者必须出现在 arXiv 作者里）；
- 结果缓存到 paper/refs-verified.json，之后可 `--offline` 只读缓存比对。

用法：
    uv run python -m paper.tools.verify_refs            # 联网核验 + 刷新缓存
    uv run python -m paper.tools.verify_refs --offline  # 只用缓存核验（CI/离线）
    uv run python -m paper.tools.verify_refs --refresh  # 强制刷新缓存

退出码：0 全部通过；1 存在不一致（CI 会红）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIB = ROOT / "paper" / "refs.bib"
CACHE = ROOT / "paper" / "refs-verified.json"
API = "https://export.arxiv.org/api/query"

_ARXIV_ID = re.compile(r"arXiv:(\d{4}\.\d{4,5})")
_ENTRY = re.compile(r"@(\w+)\{([^,]+),(.*?)\n\}", re.S)
_TITLE = re.compile(r"\btitle\s*=\s*\{(.+?)\}\s*,\s*\n", re.S)
_AUTHOR = re.compile(r"\bauthor\s*=\s*\{(.+?)\}\s*,\s*\n", re.S)


def _strip_tex(s: str) -> str:
    """去掉 LaTeX 标记与花括号，仅留可比较的题名字符。

    重音宏（\\v{S} / \\c{c}）替换为空串而非空格：`\\c{c}` 留空格会把
    `icoz` 拆成 `i c oz`，与 arXiv 记录的连续字符串对不上。
    """
    s = re.sub(r"\\[a-zA-Z]+", "", s)  # \v \c \. 等宏名（\" 的引号留给标点删除）
    s = s.replace("{", "").replace("}", "")
    s = s.replace("``", '"').replace("''", '"')
    return re.sub(r"\s+", " ", s).strip()


def _norm(s: str) -> str:
    """题名/姓名比较用：统一大小写、标点、重音与空白。

    重音统一用 NFKD 分解去组合符号（İ→I, ç→c, š→s），使 bib 里写成
    LaTeX 重音宏（ASCII）与 arXiv 记录里的 UTF-8 原字符都能归一到同一形式。
    标点删除（不留空格）：重音宏 `\\"u` 拆开会是 `t uz un` 三个碎片，
    与 arXiv 的 `tuzun` 对不上；删除后两侧都是 `tuzun`。
    """
    s = _strip_tex(s).lower()
    s = s.replace("—", "-").replace("–", "-")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_bib(path: Path = BIB) -> dict[str, dict]:
    """解析 refs.bib，返回 {key: {type, title, authors, arxiv_id}}。"""
    text = path.read_text(encoding="utf-8")
    out: dict[str, dict] = {}
    for _kind, key, body in _ENTRY.findall(text):
        t = _TITLE.search(body)
        a = _AUTHOR.search(body)
        ids = _ARXIV_ID.findall(body)
        out[key.strip()] = {
            "type": _kind,
            "title": _strip_tex(t.group(1)) if t else "",
            "authors": [
                _strip_tex(x)
                for x in re.split(r"\s+and\s+", a.group(1))
                if _strip_tex(x)
            ]
            if a
            else [],
            "arxiv_id": ids[0] if ids else None,
        }
    return out


def fetch(arxiv_ids: list[str], timeout: int = 90) -> dict[str, dict]:
    """批量拉取 arXiv 元数据，返回 {id: {title, authors}}。"""
    out: dict[str, dict] = {}
    for i in range(0, len(arxiv_ids), 6):
        chunk = arxiv_ids[i : i + 6]
        url = API + "?" + urllib.parse.urlencode(
            {"id_list": ",".join(chunk), "max_results": len(chunk)}
        )
        with urllib.request.urlopen(url, timeout=timeout) as r:
            xml = r.read().decode("utf-8", "ignore")
        for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
            tid = re.search(r"<id>(.*?)</id>", entry, re.S)
            title = re.search(r"<title>(.*?)</title>", entry, re.S)
            if not tid or not title:
                continue
            aid = tid.group(1).split("/abs/")[-1].split("v")[0]
            out[aid] = {
                "title": " ".join(title.group(1).split()),
                "authors": re.findall(r"<name>(.*?)</name>", entry),
            }
    return out


def _surname(name: str) -> str:
    """取姓氏并归一（'Last, First' → 'Last'；'First Last' → 'Last'）。"""
    n = _strip_tex(name)
    if "," in n:
        return _norm(n.split(",")[0])
    parts = [p for p in n.split() if p]
    return _norm(parts[-1]) if parts else _norm(n)


def _name_tokens(name: str) -> frozenset[str]:
    """姓名归一为词集合：'Last, First' 与 'First Last' 归一到同一集合。

    避免多词姓氏（'Roshanak Zilouchian Moghaddam'）被按最后一个词误判。
    """
    return frozenset(w for w in _norm(name).split() if w)


def check(entries: dict[str, dict], records: dict[str, dict]) -> list[str]:
    """比对 bib 条目与 arXiv 记录，返回问题清单（空 = 全部通过）。"""
    problems: list[str] = []
    for key, e in entries.items():
        if not e["authors"]:
            problems.append(f"{key}: 缺少 author 字段")
            continue
        if any(a.lower() == "others" for a in e["authors"]):
            problems.append(
                f"{key}: author 含 'others' 占位符——作者表不完整（按 arXiv 记录补全）"
            )
        aid = e["arxiv_id"]
        if not aid:
            # 规范来源等非 arXiv 条目：只要求作者非空（上面已查）
            continue
        rec = records.get(aid)
        if rec is None:
            problems.append(f"{key}: arXiv API 无 {aid} 记录")
            continue
        if _norm(e["title"]) != _norm(rec["title"]):
            problems.append(
                f"{key}: 题名不一致\n  bib : {e['title']}\n  arXiv: {rec['title']}"
            )
        rec_names = [_name_tokens(a) for a in rec["authors"]]
        for a in e["authors"]:
            toks = _name_tokens(a)
            if not any(toks <= rn for rn in rec_names):
                problems.append(
                    f"{key}: 作者 '{a}' 不在 arXiv 作者表中（记录：{rec['authors']}）"
                )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="只用本地缓存核验")
    ap.add_argument("--refresh", action="store_true", help="强制刷新缓存")
    args = ap.parse_args()

    entries = parse_bib()
    ids = sorted({e["arxiv_id"] for e in entries.values() if e["arxiv_id"]})

    if args.offline and CACHE.exists() and not args.refresh:
        cached = json.loads(CACHE.read_text(encoding="utf-8"))
        records = cached["records"]
    else:
        try:
            records = fetch(ids)
        except Exception as exc:  # noqa: BLE001 - 网络失败时给出可行动提示
            print(f"[speclens] arXiv 拉取失败：{exc}", file=sys.stderr)
            print("  离线环境请用 --offline（需先有一次联网核验生成的缓存）", file=sys.stderr)
            return 2
        CACHE.write_text(
            json.dumps(
                {"verified_at": "2026-11-19", "records": records}, ensure_ascii=False, indent=1
            ),
            encoding="utf-8",
            newline="\n",
        )

    problems = check(entries, records)
    n_arxiv = len(ids)
    print(f"[speclens] refs.bib：{len(entries)} 条，{n_arxiv} 条带 arXiv id")
    if problems:
        print(f"[speclens] 核验未通过（{len(problems)} 项）：")
        for p in problems:
            print("  - " + p)
        return 1
    print("[speclens] 全部条目与 arXiv 记录一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
