"""真实模型配置的一致性、密钥隔离与 litellm 参数透传。"""

import json
import re
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from bench.harness import env as envmod
from bench.harness.model_adapter import make_adapter
from bench.harness.schemas import FindingsOutput

REPO = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO / "experiments" / "configs"
LITMUS = ("litmus-b0", "litmus-b1", "litmus-mlite", "litmus-mverified")
OFFLINE = ("smoke-b0", "validate-b0", "validate-b1", "validate-mlite", "validate-mverified")
MODEL = "deepseek/deepseek-flash"


def _load(name: str) -> dict:
    return yaml.safe_load((CONFIG_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def test_four_litmus_configs_share_control_variables():
    cfgs = {name: _load(name) for name in LITMUS}
    assert {c["model"] for c in cfgs.values()} == {MODEL}
    assert {c["temperature"] for c in cfgs.values()} == {0.0}
    assert {c["run_index"] for c in cfgs.values()} == {0}
    assert {json.dumps(c["litellm_kwargs"], sort_keys=True) for c in cfgs.values()} == {
        json.dumps({"thinking": {"type": "disabled"}}, sort_keys=True)
    }
    assert {c["litellm_num_retries"] for c in cfgs.values()} == {3}
    assert cfgs["litmus-mlite"]["rules_source"] == "aligned"
    assert cfgs["litmus-mverified"]["rules_source"] == "aligned"
    # B0/B1 不应意外带 rules_source（会进 config.resolved.yaml 造成误读）
    assert "rules_source" not in cfgs["litmus-b0"]
    assert "rules_source" not in cfgs["litmus-b1"]


def test_no_secret_in_any_config():
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        body = path.read_text(encoding="utf-8")
        assert not re.search(r"sk-[A-Za-z0-9]{16,}", body), path.name
        assert not re.search(r"(?i)^\s*(api[_-]?key|secret)\s*:", body, re.M), path.name


def test_offline_configs_remain_mock():
    for name in OFFLINE:
        assert _load(name)["model"].startswith("mock-"), name


def _fake_response():
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"findings": []}'))],
        usage=None,
    )


def test_litellm_kwargs_are_passed_and_reserved_params_protected(monkeypatch):
    captured: dict = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return _fake_response()

    stub = types.ModuleType("litellm")
    stub.completion = fake_completion
    monkeypatch.setitem(sys.modules, "litellm", stub)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-placeholder")
    monkeypatch.setattr(envmod, "load_dotenv", lambda root=None: {})

    run_config = {
        "litellm_num_retries": 5,
        "litellm_timeout_s": 42,
        "litellm_kwargs": {
            "thinking": {"type": "disabled"},
            "model": "SHOULD_BE_STRIPPED",  # 保留参数不得覆盖控制变量
            "temperature": 9,
        },
    }
    adapter = make_adapter(MODEL, temperature=0.0, run_config=run_config)
    out = adapter.complete_json(
        system="Respond ONLY with a JSON object.",
        user="Return an empty findings list as JSON.",
        schema=FindingsOutput,
        meta={"case_id": "PING"},
    )
    assert out.findings == []
    assert captured["model"] == MODEL
    assert captured["temperature"] == 0.0
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["num_retries"] == 5
    assert captured["timeout"] == 42
    assert captured["thinking"] == {"type": "disabled"}
    assert adapter.usage.n_calls == 1
    assert adapter.usage.total_tokens > 0
