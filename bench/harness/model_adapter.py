"""模型适配层：统一 LLM 访问 + JSON Schema 强校验 + 重试 ≤3（plan.md §3.4）。

- MockPerfectAdapter / MockImperfectAdapter：离线冒烟与指标校验用的确定性适配器
- LiteLLMAdapter：真实调用（依赖 `litellm` extra）
"""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import BaseModel, ValidationError

MAX_RETRIES = 3


class ModelAdapter(Protocol):
    name: str

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        meta: dict | None = None,
    ) -> BaseModel: ...


class MockPerfectAdapter:
    """按 meta['expected_findings'] 原样输出——用于冒烟测试与指标口径校验。"""

    name = "mock-perfect"

    def __init__(self, expected: dict[str, list[dict]] | None = None) -> None:
        self.expected = expected or {}

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        meta: dict | None = None,
    ) -> BaseModel:
        case_id = (meta or {}).get("case_id", "")
        return schema.model_validate({"findings": self.expected.get(case_id, [])})


class MockImperfectAdapter(MockPerfectAdapter):
    """漏报 medium/hard 的违规——用于验证 detection_rate 的计算口径。"""

    name = "mock-imperfect"

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        meta: dict | None = None,
    ) -> BaseModel:
        case_id = (meta or {}).get("case_id", "")
        findings = [
            f for f in self.expected.get(case_id, []) if f.get("difficulty") == "easy"
        ]
        return schema.model_validate({"findings": findings})


class LiteLLMAdapter:
    """litellm 统一接入；输出必须通过 schema 校验，否则带错误反馈重试（≤3 次）。"""

    def __init__(self, model: str, temperature: float = 0.0) -> None:
        try:
            import litellm
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "litellm 未安装：请运行 `uv sync --extra llm`"
            ) from exc
        self._litellm = litellm
        self.name = model
        self.model = model
        self.temperature = temperature

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        meta: dict | None = None,
    ) -> BaseModel:
        last_err: Exception | None = None
        for _ in range(MAX_RETRIES):
            resp = self._litellm.completion(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
            text = resp.choices[0].message.content
            try:
                return schema.model_validate(json.loads(text))
            except (json.JSONDecodeError, ValidationError) as err:
                last_err = err
                user += (
                    f"\n\n上一次输出未通过 schema 校验：{err}\n"
                    "请只输出符合要求的 JSON 对象。"
                )
        raise RuntimeError(
            f"LLM 输出 {MAX_RETRIES} 次均未通过 schema 校验"
        ) from last_err


def make_adapter(
    model_spec: str, expected: dict[str, list[dict]] | None = None
) -> ModelAdapter:
    """`mock-perfect` / `mock-imperfect` 走确定性适配器，其余视为 litellm 模型串。"""
    if model_spec == "mock-perfect":
        return MockPerfectAdapter(expected)
    if model_spec == "mock-imperfect":
        return MockImperfectAdapter(expected)
    return LiteLLMAdapter(model_spec)
