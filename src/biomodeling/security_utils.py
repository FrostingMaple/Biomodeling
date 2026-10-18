"""Security and privacy helpers shared by tools and the CLI."""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def is_within(path, root):
    """Return True when path is root or a descendant of root."""
    try:
        target = Path(path).expanduser().resolve()
        base = Path(root).expanduser().resolve()
    except OSError:
        return False
    return target == base or base in target.parents


def require_project_path(path):
    """Resolve a path and require it to be inside the project root."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    resolved = p.resolve()
    if not is_within(resolved, PROJECT_ROOT):
        raise ValueError(
            "read_text only allows files inside the project root by default; "
            "set BIOMODEL_ALLOW_EXTERNAL_READS=1 to allow an external path"
        )
    return resolved


def external_reads_allowed():
    return os.getenv("BIOMODEL_ALLOW_EXTERNAL_READS", "").strip().lower() in {
        "1", "true", "yes", "on"
    }


def safe_identifier(value, default=None, max_length=100):
    """Return a safe filename segment, rejecting path traversal."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    if not isinstance(value, str):
        raise ValueError("identifier must be a string")
    if value in {".", ".."} or "/" in value or "\\" in value or ":" in value:
        raise ValueError(f"unsafe identifier: {value!r}")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    if not cleaned:
        raise ValueError(f"identifier contains no safe characters: {value!r}")
    return cleaned[:max_length]


def safe_filename(value):
    """Validate a report filename without allowing directory traversal."""
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("filename must be a non-empty string")
    if value in {".", ".."} or "/" in value or "\\" in value or ":" in value:
        raise ValueError(f"unsafe filename: {value!r}")
    if Path(value).name != value:
        raise ValueError(f"unsafe filename: {value!r}")
    return value



def redact_secrets(text, secrets=None):
    """Redact known API keys and obvious sk-* tokens from text."""
    if not isinstance(text, str):
        return text
    candidates = []
    if secrets:
        candidates.extend(str(item) for item in secrets if item)
    for name in ("USTC_LLM_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(name)
        if value:
            candidates.append(value)
    candidates.extend(re.findall(r"\bsk-[A-Za-z0-9_-]{6,}\b", text))
    for secret in sorted(set(candidates), key=len, reverse=True):
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text
