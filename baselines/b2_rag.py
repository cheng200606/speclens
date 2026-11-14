"""B2 检索基线（plan.md §2.4）：BM25 段落检索 + 局部上下文单次审查。

定位：RQ2 的 RAG 对照臂——「代码找规则」范式的代表。与 B1 的差异：
模型只看到与 case 词面最相关的 top-k 规范段落（而非全文），
单次调用成本约为 B1 的 1/15~1/20。检索为纯 Python BM25，无向量库依赖
（plan.md §1.4：不做向量库/RAG 基建，B2 仅作基线）。

与 M（规则找代码）的本质差异即 RQ2 论点：检索命中决定覆盖，
漏检由「该 case 词面是否撞上相关段落」决定。
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import TYPE_CHECKING

from bench.harness.schemas import FindingsOutput

if TYPE_CHECKING:
    from bench.harness.loader import Case
    from bench.harness.model_adapter import ModelAdapter
    from bench.harness.schemas import Finding

BASELINE_ID = "b2_rag"

TOP_K = 6
_K1, _B = 1.5, 0.75

_TOKEN = re.compile(r"[a-z][a-z0-9_]{1,}|[\u4e00-\u9fff]{2,}")
_CAMEL = re.compile(r"[A-Z]?[a-z]{2,}|[A-Z]{2,}")

SYSTEM = (
    "You are a meticulous code reviewer. You are given a few excerpts retrieved "
    "from a technical specification document. Review the code ONLY against rules "
    "that are explicitly stated in those excerpts; report each violation with the "
    "excerpt text that supports it. Respond ONLY with a JSON object of the form "
    '{"findings": [{"file": str, "line_start": int, "line_end": int, '
    '"rule_ids": [str], "severity": "info"|"warning"|"error", "message": str, '
    '"evidence": {"rule_quote": str, "explanation": str}}]}. '
    "Report nothing when the code violates nothing in the excerpts."
)


def _split_paragraphs(md: str) -> list[str]:
    paras: list[str] = []
    for block in re.split(r"\n\s*\n", md):
        text = block.strip()
        if 40 <= len(text) <= 1500:
            paras.append(text)
    return paras


def _tokens(text: str) -> list[str]:
    tokens = _TOKEN.findall(text.lower())
    for raw in re.findall(r"[A-Za-z]{3,}", text):
        tokens.extend(t.lower() for t in _CAMEL.findall(raw))  # 驼峰拆分
    return tokens


def _build_index(spec_dir: Path) -> tuple:
    paragraphs: list[str] = []
    for md in sorted(spec_dir.glob("snapshot/*.md")):
        paragraphs.extend(_split_paragraphs(md.read_text(encoding="utf-8")))
    docs = [_tokens(p) for p in paragraphs]
    n = len(docs)
    avgdl = sum(len(d) for d in docs) / max(1, n)
    df: dict[str, int] = {}
    for doc in docs:
        for t in set(doc):
            df[t] = df.get(t, 0) + 1
    return paragraphs, docs, df, n, avgdl


_INDEXES: dict[str, tuple] = {}


def _index_for(spec_dir: Path) -> tuple:
    key = str(spec_dir.resolve())
    if key not in _INDEXES:
        _INDEXES[key] = _build_index(spec_dir)
    return _INDEXES[key]


def retrieve(spec_dir: Path, case: Case, k: int = TOP_K) -> list[str]:
    paragraphs, docs, df, n, avgdl = _index_for(spec_dir)
    query: list[str] = []
    for name in case.meta.files:
        query.extend(_tokens(case.read_file(name)))
    qtf: dict[str, int] = {}
    for t in query:
        qtf[t] = qtf.get(t, 0) + 1
    scores = [0.0] * n
    for t, qcount in qtf.items():
        postings = df.get(t)
        if not postings:
            continue
        idf = math.log(1 + (n - postings + 0.5) / (postings + 0.5))
        for i, doc in enumerate(docs):
            tf = doc.count(t)
            if not tf:
                continue
            denom = tf + _K1 * (1 - _B + _B * len(doc) / max(1.0, avgdl))
            scores[i] += qcount * idf * (tf * (_K1 + 1)) / denom
    order = sorted(range(n), key=lambda i: scores[i], reverse=True)[:k]
    return [paragraphs[i] for i in order if scores[i] > 0]


def build_user_prompt(case: Case, excerpts: list[str]) -> str:
    parts = ["# Retrieved specification excerpts\n"]
    for i, p in enumerate(excerpts, 1):
        parts.append(f"--- excerpt {i} ---\n{p}")
    parts.append(f"\n# Code to review (case {case.meta.case_id})\n")
    for name in case.meta.files:
        parts.append(f"--- {name} ---\n{case.read_file(name)}")
    return "\n".join(parts)


def predict_case(case: Case, adapter: ModelAdapter) -> list[Finding]:
    spec_dir = case.root.parents[2] / "specs" / case.root.parent.name
    excerpts = retrieve(spec_dir, case)
    out = adapter.complete_json(
        system=SYSTEM,
        user=build_user_prompt(case, excerpts),
        schema=FindingsOutput,
        meta={"case_id": case.meta.case_id, "phase": "b2_rag_review"},
    )
    for finding in out.findings:
        finding.case_id = case.meta.case_id
    return out.findings
