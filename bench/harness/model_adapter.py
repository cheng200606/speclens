"""模型适配层：统一 LLM 访问 + JSON Schema 强校验 + 重试 ≤3（plan.md §3.4）。

- MockPerfectAdapter / MockImperfectAdapter：离线冒烟与指标口径校验
- MockScriptedAdapter：带已知误差模式的确定性适配器，用于端到端验证评测管线
- LiteLLMAdapter：真实调用（依赖 `litellm` extra），记录 token / 时延 / 调用数；
  初始化时从仓库根目录 `.env` 读取密钥并校验缺失项（见 bench/harness/env.py）

I1 新增（docs/STATUS-I1.md P0-4）：
- `UsageRecord` 统一记账，runner 落盘 `usage.json`，支撑 §1.3 成本指标与 RQ4。
- `temperature` 从实验配置真正透传；`run_config` 注入给基线读取
  （`spec_max_chars` / `rules_source`），避免全局可变状态。
- 所有 mock 适配器名称以 `mock-` 开头，报告生成器据此判定「非科学」。
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Protocol

from pydantic import BaseModel, ValidationError

MAX_RETRIES = 3


@dataclass
class UsageRecord:
    """单次 run 的模型调用记账（不硬编码价格，成本由配置中的单价换算）。"""

    n_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_s: float = 0.0
    by_phase: dict[str, int] = field(default_factory=dict)

    def record(
        self,
        *,
        phase: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_s: float = 0.0,
    ) -> None:
        self.n_calls += 1
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.latency_s = round(self.latency_s + latency_s, 6)
        self.by_phase[phase] = self.by_phase.get(phase, 0) + 1

    def to_dict(self) -> dict:
        return asdict(self)


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


class _AdapterBase:
    """公共字段：温度、run 配置、调用记账。"""

    name = "adapter"

    def __init__(
        self,
        *,
        temperature: float = 0.0,
        run_config: dict | None = None,
    ) -> None:
        self.temperature = temperature
        self.run_config = dict(run_config or {})
        self.usage = UsageRecord()

    def _record(self, meta: dict | None, prompt: str, completion: str, t0: float) -> None:
        phase = (meta or {}).get("phase", "review")
        self.usage.record(
            phase=phase,
            prompt_tokens=max(1, len(prompt) // 4),
            completion_tokens=max(1, len(completion) // 4),
            latency_s=time.perf_counter() - t0,
        )


class MockPerfectAdapter(_AdapterBase):
    """按 meta['case_id'] 原样输出期望 findings——冒烟与指标口径校验。"""

    name = "mock-perfect"

    def __init__(
        self,
        expected: dict[str, list[dict]] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.expected = expected or {}

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        meta: dict | None = None,
    ) -> BaseModel:
        t0 = time.perf_counter()
        case_id = (meta or {}).get("case_id", "")
        out = schema.model_validate({"findings": self.expected.get(case_id, [])})
        self._record(meta, system + user, out.model_dump_json(), t0)
        return out


class MockImperfectAdapter(MockPerfectAdapter):
    """漏报 medium/hard 的违规——验证 detection_rate 的计算口径。"""

    name = "mock-imperfect"

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        meta: dict | None = None,
    ) -> BaseModel:
        t0 = time.perf_counter()
        case_id = (meta or {}).get("case_id", "")
        findings = [
            f for f in self.expected.get(case_id, []) if f.get("difficulty") == "easy"
        ]
        out = schema.model_validate({"findings": findings})
        self._record(meta, system + user, out.model_dump_json(), t0)
        return out


class MockScriptedAdapter(_AdapterBase):
    """确定性「带已知缺陷」的审查器——**非科学**，仅用于端到端验证评测管线。

    误差模式（由 build_scripted_script 生成）：
    - 违规样本：漏掉所有 hard 样本；
    - 合规样本：固定对 1 个样本误报；
    - 逐规则审查：只有 rule_id 命中该 case 标注规则时才输出 finding；
    - 验证关 2：按规则 ID 的确定性哈希让约 1/4 规则自洽失败（pass/fail 混合）；
    - 验证关 3：确定性哈希让少量规则对被判为矛盾。

    它使 mock 下的指标不再全是 1.0/0.0，从而能真正验证 metrics、McNemar、
    证据链、usage 记账与报告防误读是否工作。绝不用于任何论文结论。
    """

    name = "mock-scripted"
    _NEG_MARKER = "// SPEC_LENS_NEG_EXAMPLE"
    _POS_MARKER = "// SPEC_LENS_POS_EXAMPLE"

    def __init__(self, script: dict | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.script = script or {}

    @staticmethod
    def _hash(text: str) -> int:
        return sum(ord(c) for c in text)

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel],
        meta: dict | None = None,
    ) -> BaseModel:
        t0 = time.perf_counter()
        m = meta or {}
        phase = m.get("phase", "review")
        schema_name = schema.__name__

        if schema_name == "RuleExamples":
            out = schema.model_validate(
                {
                    "pos_example": f"{self._POS_MARKER}\nconst ok = 1;",
                    "neg_example": f"{self._NEG_MARKER}\nconst bad = 1;",
                }
            )
        elif schema_name == "ContradictionVerdict":
            pair = f"{m.get('rule_id', '')}|{m.get('other', '')}"
            out = schema.model_validate({"contradict": self._hash(pair) % 17 == 0})
        else:
            findings = self._review_findings(m)
            out = schema.model_validate({"findings": findings})

        self._record(m, system + user, out.model_dump_json(), t0)
        return out

    def _review_findings(self, m: dict) -> list[dict]:
        case_id = m.get("case_id")
        rule_id = m.get("rule_id")
        code_head = m.get("code_head", "")

        # 验证关 2 的自审调用：case_id 为空，靠代码标记判定
        if case_id is None:
            if self._NEG_MARKER in code_head:
                # 约 1/4 规则自洽失败：反例未被自己的审查器检出
                if self._hash(rule_id or "") % 4 == 0:
                    return []
                return [self._finding("snippet.tsx", [rule_id or "UNKNOWN"], "self-test")]
            return []

        entry = self.script.get(case_id)
        if not entry or not entry.get("detected"):
            return []
        allowed = entry["rule_ids"]
        if rule_id is not None and rule_id not in allowed:
            return []
        rids = [rule_id] if rule_id is not None else allowed
        return [self._finding(entry["file"], rids, "scripted violation")]

    @staticmethod
    def _finding(file: str, rule_ids: list[str], message: str) -> dict:
        return {
            "file": file,
            "line_start": 1,
            "line_end": 1,
            "rule_ids": rule_ids,
            "severity": "warning",
            "message": message,
            "evidence": {"rule_quote": "", "explanation": ""},
        }


class LiteLLMAdapter(_AdapterBase):
    """litellm 统一接入；输出必须通过 schema 校验，否则带错误反馈重试（≤3 次）。"""

    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        run_config: dict | None = None,
    ) -> None:
        super().__init__(temperature=temperature, run_config=run_config)
        # 先加载仓库根目录的 .env（不覆盖已有环境变量），再交给 litellm。
        # 不依赖 litellm 自身对 dotenv 的隐式行为，保证 CLI / probe / pytest 一致。
        from bench.harness.env import credential_hint, key_setup_hint, load_dotenv

        load_dotenv()
        # litellm 启动时会联网拉取 model_prices_and_context_window.json；
        # 国内网络常超时（每次约 8s × 3 次重试）。本项目从 resp.usage 自行记账，
        # 不依赖其价格表，故默认改用本地备份。需要实时价格时可显式设为 False。
        os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
        try:
            import litellm
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("litellm 未安装：请运行 `uv sync --extra llm`") from exc
        if (
            not os.environ.get("SPECLENS_SKIP_KEY_CHECK")
            and credential_hint(model) is not None
        ):
            raise RuntimeError(key_setup_hint(model))
        self._litellm = litellm
        self.name = model
        self.model = model
        # 真实实验会产生数百次串行调用，必须对 429 / 超时 / 5xx 有退避能力，
        # 否则单个限流就会中断整次 run 并留下残缺产物。
        cfg = self.run_config
        self.num_retries = int(cfg.get("litellm_num_retries", 3))
        self.timeout_s = float(cfg.get("litellm_timeout_s", 180))
        self._extra_kwargs = dict(cfg.get("litellm_kwargs") or {})
        # 这些是控制变量 / 结构化输出的保留参数，不允许被实验配置覆盖
        for reserved in ("model", "temperature", "messages", "response_format"):
            self._extra_kwargs.pop(reserved, None)

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
            t0 = time.perf_counter()
            resp = self._litellm.completion(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                num_retries=self.num_retries,
                timeout=self.timeout_s,
                **self._extra_kwargs,
            )
            text = resp.choices[0].message.content or ""
            usage = getattr(resp, "usage", None)
            self._record(
                meta,
                system + user,
                text,
                t0,
            )
            # 用 provider 上报的真实 token 数覆盖字符估算
            if usage is not None:
                p = int(getattr(usage, "prompt_tokens", 0) or 0)
                c = int(getattr(usage, "completion_tokens", 0) or 0)
                delta_p, delta_c = p - max(1, len(system + user) // 4), c - max(1, len(text) // 4)
                self.usage.prompt_tokens += delta_p
                self.usage.completion_tokens += delta_c
                self.usage.total_tokens += delta_p + delta_c
            try:
                return schema.model_validate(json.loads(text))
            except (json.JSONDecodeError, ValidationError) as err:
                last_err = err
                user += (
                    f"\n\n上一次输出未通过 schema 校验：{err}\n"
                    "请只输出符合要求的 JSON 对象。"
                )
        raise RuntimeError(f"LLM 输出 {MAX_RETRIES} 次均未通过 schema 校验") from last_err


def make_adapter(
    model_spec: str,
    expected: dict[str, list[dict]] | None = None,
    *,
    script: dict | None = None,
    temperature: float = 0.0,
    run_config: dict | None = None,
) -> ModelAdapter:
    """按模型串构造适配器；mock-* 走确定性实现，其余视为 litellm 模型串。"""
    kwargs = {"temperature": temperature, "run_config": run_config}
    if model_spec == "mock-perfect":
        return MockPerfectAdapter(expected, **kwargs)
    if model_spec == "mock-imperfect":
        return MockImperfectAdapter(expected, **kwargs)
    if model_spec == "mock-scripted":
        return MockScriptedAdapter(script, **kwargs)
    return LiteLLMAdapter(model_spec, **kwargs)


def is_mock_model(model_spec: str) -> bool:
    """报告生成器据此判定结果是否具有科学意义。"""
    return model_spec.startswith("mock-")
