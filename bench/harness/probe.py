"""新鲜度探测 runner（plan.md §2.3.1）。

对每份规范运行 `freshness_probe.yaml`（20 道选择题），测被测模型对规范的「已有知识」。
正确率接近随机 ⇒ 视为「未见规范」；探测结果随论文报告，堵「模型见过规范」的质疑。

用法：
    uv run python -m bench.harness.probe \
        --probe bench/specs/react19/freshness_probe.yaml --model mock-correct
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from bench.harness.model_adapter import ModelAdapter

SYSTEM = (
    "You are answering a multiple-choice question about a technical specification. "
    'Respond ONLY with a JSON object: {"choice": <index of the correct option, integer>}'
)


class ProbeQuestion(BaseModel):
    id: str
    question: str
    options: list[str] = Field(min_length=2, max_length=6)
    answer_index: int = Field(ge=0)
    source: str = ""

    @model_validator(mode="after")
    def _answer_within_options(self) -> "ProbeQuestion":
        if self.answer_index >= len(self.options):
            raise ValueError(
                f"{self.id}: answer_index={self.answer_index} 越界（共 {len(self.options)} 个选项）"
            )
        return self


class ProbeBank(BaseModel):
    spec_id: str
    created: _dt.date | None = None  # YAML 日期字面量自动解析为 date
    grounding: str = ""
    questions: list[ProbeQuestion]


class ProbeAnswer(BaseModel):
    choice: int


def load_probe(path: Path) -> ProbeBank:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProbeBank.model_validate(data)


def build_user_prompt(q: ProbeQuestion) -> str:
    lines = [q.question]
    for i, opt in enumerate(q.options):
        lines.append(f"{i}. {opt}")
    return "\n".join(lines)


class MockCorrectProbeAdapter:
    """探测冒烟用：总是选 meta['answer_index']。"""

    name = "mock-correct"

    def complete_json(self, *, system, user, schema, meta=None):
        return ProbeAnswer(choice=(meta or {})["answer_index"])


def make_probe_adapter(model_spec: str) -> ModelAdapter:
    if model_spec == "mock-correct":
        return MockCorrectProbeAdapter()
    from bench.harness.model_adapter import LiteLLMAdapter

    return LiteLLMAdapter(model_spec)


def run_probe(
    probe_path: Path, adapter: ModelAdapter, output_dir: Path, force: bool = False
) -> tuple[Path, dict]:
    """运行题库并返回 (run_dir, summary)。

    I1 修订：run 目录包含**模型名**，否则跨模型的新鲜度探测会互相覆盖
    （而「模型见过规范」的辩护恰恰需要跨模型对比）；同时禁止覆盖已有 run。
    """
    bank = load_probe(probe_path)
    digest = hashlib.sha256(probe_path.read_bytes()).hexdigest()[:12]
    model_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", adapter.name)[:48]
    run_dir = output_dir / f"probe-{bank.spec_id}-{model_slug}-{digest}"
    if run_dir.exists() and not force:
        raise RuntimeError(
            f"probe run 已存在，禁止覆盖：{run_dir}（确需重跑请传 force=True / --force）"
        )
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)

    per_question = []
    correct_count = 0
    for q in bank.questions:
        answer: ProbeAnswer = adapter.complete_json(
            system=SYSTEM,
            user=build_user_prompt(q),
            schema=ProbeAnswer,
            meta={"question_id": q.id, "answer_index": q.answer_index},
        )
        correct = answer.choice == q.answer_index
        correct_count += correct
        (run_dir / "raw" / f"{q.id}.json").write_text(
            json.dumps(
                {
                    "question_id": q.id,
                    "choice": answer.choice,
                    "answer_index": q.answer_index,
                    "correct": correct,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        per_question.append({"id": q.id, "correct": correct})

    summary = {
        "spec_id": bank.spec_id,
        "n_questions": len(bank.questions),
        "accuracy": round(correct_count / len(bank.questions), 4)
        if bank.questions
        else None,
        "model": adapter.name,
        "probe_path": str(probe_path).replace("\\", "/"),
        "created": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "note": "accuracy 接近随机(0.25) => 视为未见规范；显著偏高 => 模型已熟悉",
        "per_question": per_question,
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return run_dir, summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SpecLens 新鲜度探测")
    parser.add_argument("--probe", required=True, help="freshness_probe.yaml 路径")
    parser.add_argument("--model", default="mock-correct")
    parser.add_argument("--output-dir", default="experiments/runs")
    parser.add_argument("--force", action="store_true", help="允许覆盖同名 probe run")
    args = parser.parse_args(argv)

    run_dir, summary = run_probe(
        Path(args.probe),
        make_probe_adapter(args.model),
        Path(args.output_dir),
        force=args.force,
    )
    print(f"[speclens] probe completed -> {run_dir}")
    printable = {k: v for k, v in summary.items() if k != "per_question"}
    print(json.dumps(printable, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
