"""本地 `.env` 加载（纯标准库，不引入 python-dotenv 依赖）与密钥缺失提示。

为什么需要这个文件
------------------
`LiteLLMAdapter` 只把模型串交给 litellm，密钥由 litellm 从**环境变量**读取。
项目原本没有任何「填 key 的文件」，且 `.gitignore` 未忽略 `.env`，
用户若在仓库根目录直接建 `.env` 有密钥误提交的风险。

约定：
- 复制 `.env.example` 为 `.env` 后填写；`.env` 已被 `.gitignore` 忽略。
- **不要把 key 写进 `experiments/configs/*.yaml`**：这些文件进 git，且会被
  `config.resolved.yaml` 原样归档到 run 产物里。
- 不覆盖已存在的环境变量（shell / CI 注入优先），文件不存在时静默跳过。
- 支持 `export KEY=...`、注释、单/双引号；不解析变量插值（避免意外展开）。
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_ENV_FILENAME = ".env"
_LINE = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$"
)

# 常见 provider 的 litellm 模型前缀 → 必需的环境变量。
# 以 litellm 官方文档为准；未知前缀不做检查（避免阻断自定义端点）。
_KEY_BY_PREFIX = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "vertex_ai": None,  # 走服务账号 JSON，非简单 key
    "deepseek": "DEEPSEEK_API_KEY",
    "minimax": "MINIMAX_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "azure": "AZURE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "xai": "XAI_API_KEY",
    "cohere": "COHERE_API_KEY",
    "together_ai": "TOGETHERAI_API_KEY",
}
_LOCAL_PREFIXES = {"ollama", "vllm", "hosted_vllm", "local", "llama_cpp", "mlx"}


def repo_root() -> Path:
    """speclens 仓库根目录（bench/harness/env.py -> parents[2]）。"""
    return Path(__file__).resolve().parents[2]


def candidate_paths(root: Path | None = None) -> list[Path]:
    """按优先级返回候选 .env 路径（去重，保序）。"""
    paths = [Path.cwd() / _ENV_FILENAME, (root or repo_root()) / _ENV_FILENAME]
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            out.append(p)
    return out


def parse_env(text: str) -> dict[str, str]:
    """解析 .env 文本为键值；跳过注释、空行与无 '=' 的行。"""
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        else:
            # 去掉行尾未加引号的注释
            value = re.sub(r"\s+#.*$", "", value).strip()
        result[key] = value
    return result


def load_dotenv(root: Path | None = None) -> dict[str, str]:
    """把 .env 中尚未设置的变量注入 os.environ。

    返回 {变量名: 来源文件路径}（**绝不返回值**，避免日志泄漏密钥）。
    """
    loaded: dict[str, str] = {}
    for path in candidate_paths(root):
        if not path.is_file():
            continue
        for key, value in parse_env(path.read_text(encoding="utf-8")).items():
            if not value or key in os.environ:
                continue  # 空值不注入；已有环境变量优先
            os.environ[key] = value
            loaded[key] = str(path)
    return loaded


def credential_hint(model: str) -> str | None:
    """返回该模型缺失的环境变量名；无需检查或已具备时返回 None。"""
    if "/" not in model:
        return None
    prefix = model.split("/", 1)[0].lower()
    if prefix in _LOCAL_PREFIXES:
        return None
    var = _KEY_BY_PREFIX.get(prefix)
    if var is None or os.environ.get(var):
        return None
    return var


def key_setup_hint(model: str) -> str:
    """给用户的可执行指引（不含任何密钥值）。"""
    var = credential_hint(model) or "对应 provider 的 API_KEY 变量"
    return (
        f"缺少 {var}。请复制仓库根目录的 .env.example 为 .env 并填写，"
        f"或在 shell 中执行 export {var}=<your-key>；"
        "不要把密钥写进 experiments/configs/*.yaml（会被归档到 run 产物）。"
        "若使用非标准认证（如 AZURE_AD_TOKEN），设置 SPECLENS_SKIP_KEY_CHECK=1 跳过本检查。"
    )
