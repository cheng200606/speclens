"""本地 .env 加载与密钥防泄漏（API key 配置路径）。"""

import os
import sys
import types
from pathlib import Path

import pytest

from bench.harness import env as envmod
from bench.harness.env import (
    credential_hint,
    key_setup_hint,
    load_dotenv,
    parse_env,
    repo_root,
)

REPO = Path(__file__).resolve().parent.parent


def test_parse_env_supports_common_forms():
    got = parse_env(
        """
# comment
export OPENAI_API_KEY="sk-abc123"
GEMINI_API_KEY='xyz'
DASHSCOPE_API_KEY=plain   # trailing comment
EMPTY=
NOT_A_PAIR
"""
    )
    assert got["OPENAI_API_KEY"] == "sk-abc123"
    assert got["GEMINI_API_KEY"] == "xyz"
    assert got["DASHSCOPE_API_KEY"] == "plain"
    assert got["EMPTY"] == ""
    assert "NOT_A_PAIR" not in got


def test_load_dotenv_never_overrides_existing(monkeypatch, tmp_path):
    path = tmp_path / ".env"
    path.write_text("OPENAI_API_KEY=from-file\nNEW_KEY=from-file\nEMPTY=\n", encoding="utf-8")
    monkeypatch.setattr(envmod, "candidate_paths", lambda root=None: [path])
    monkeypatch.setenv("OPENAI_API_KEY", "from-shell")
    monkeypatch.delenv("NEW_KEY", raising=False)
    monkeypatch.delenv("EMPTY", raising=False)
    loaded = load_dotenv(tmp_path)
    assert os.environ["OPENAI_API_KEY"] == "from-shell"
    assert os.environ["NEW_KEY"] == "from-file"
    assert "EMPTY" not in os.environ
    # 返回值只含变量名与来源路径，不含密钥值
    assert "from-file" not in str(loaded)
    assert "NEW_KEY" in loaded


def test_load_dotenv_missing_file_is_silent(monkeypatch, tmp_path):
    monkeypatch.setattr(envmod, "candidate_paths", lambda root=None: [tmp_path / "nope.env"])
    assert load_dotenv(tmp_path) == {}


def test_credential_hint(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert credential_hint("openai/gpt-4o") == "OPENAI_API_KEY"
    assert credential_hint("anthropic/claude-sonnet-4-5") == "ANTHROPIC_API_KEY"
    assert credential_hint("ollama/qwen2.5-coder") is None  # 本地模型
    assert credential_hint("gpt-4o") is None  # 无前缀，交给 litellm 推断
    assert credential_hint("custom-provider/foo") is None  # 未知前缀不阻断
    hint = key_setup_hint("openai/gpt-4o")
    assert "OPENAI_API_KEY" in hint and ".env.example" in hint
    assert "configs/*.yaml" in hint
    monkeypatch.setenv("OPENAI_API_KEY", "set")
    assert credential_hint("openai/gpt-4o") is None


def test_gitignore_and_template_protect_secrets():
    ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "\n.env\n" in ignore
    assert "!.env.example" in ignore
    template = REPO / ".env.example"
    assert template.exists()
    body = template.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" in body and "cp .env.example .env" in body
    # 模板里不得出现看起来像真实密钥的长串
    import re

    assert not re.search(r"sk-[A-Za-z0-9]{16,}", body)
    assert repo_root() == REPO


def test_adapter_reads_key_from_env_file(monkeypatch, tmp_path):
    """闭环：把 key 写进 .env 后，LiteLLMAdapter 应能读到并不再报缺失。"""
    from bench.harness.model_adapter import LiteLLMAdapter

    path = tmp_path / ".env"
    path.write_text("OPENAI_API_KEY=test-placeholder\n", encoding="utf-8")
    monkeypatch.setattr(envmod, "candidate_paths", lambda root=None: [path])
    monkeypatch.setitem(sys.modules, "litellm", types.ModuleType("litellm"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SPECLENS_SKIP_KEY_CHECK", raising=False)
    adapter = LiteLLMAdapter("openai/gpt-4o")
    assert adapter.model == "openai/gpt-4o"
    assert os.environ["OPENAI_API_KEY"] == "test-placeholder"


def test_missing_key_fails_fast_with_actionable_message(monkeypatch):
    """注入 litellm stub，验证缺 key 时直接给出「填哪个变量」的提示。"""
    from bench.harness.model_adapter import LiteLLMAdapter

    monkeypatch.setitem(sys.modules, "litellm", types.ModuleType("litellm"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SPECLENS_SKIP_KEY_CHECK", raising=False)
    monkeypatch.setattr(envmod, "load_dotenv", lambda root=None: {})
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        LiteLLMAdapter("openai/gpt-4o")

    monkeypatch.setenv("SPECLENS_SKIP_KEY_CHECK", "1")
    adapter = LiteLLMAdapter("openai/gpt-4o")
    assert adapter.model == "openai/gpt-4o"
