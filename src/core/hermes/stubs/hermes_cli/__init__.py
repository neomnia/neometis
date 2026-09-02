"""Minimal hermes_cli stubs for headless NéoMêtis upstream mode."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_hermes_dotenv(*, hermes_home: Path | None = None, project_env: Path | None = None) -> list[Path]:
    return []


def get_provider_request_timeout() -> float:
    return 120.0


def get_provider_stale_timeout() -> float:
    return 300.0


def get_active_profile_name() -> str:
    return "default"


def windows_hide_flags() -> dict[str, int]:
    return {}


def discover_plugins() -> list[Any]:
    return []


def get_config_path() -> Path:
    return Path("/tmp/neometis-hermes-config.yaml")


def load_config(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {}


def load_config_readonly(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {}


def split_model_config_default(value: str) -> tuple[str, dict[str, Any]]:
    return value, {}


def require_readable_config_before_write(*args: Any, **kwargs: Any) -> None:
    return None


def _greedy_literal_match(*args: Any, **kwargs: Any) -> Any:
    return None


def _split_key_path(key: str) -> list[str]:
    return key.split(".")


def is_managed() -> bool:
    return False


def read_raw_config(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {}


def has_hook(*args: Any, **kwargs: Any) -> bool:
    return False


def invoke_hook(*args: Any, **kwargs: Any) -> None:
    return None


def apply_tool_request_middleware(*args: Any, **kwargs: Any) -> Any:
    return args[0] if args else None


def run_tool_execution_middleware(handler: Any, *args: Any, **kwargs: Any) -> Any:
    return handler(*args, **kwargs)


def trim_memory(*args: Any, **kwargs: Any) -> None:
    return None


def normalize_route_base_url(url: str) -> str:
    return url.rstrip("/")


def ensure_lmstudio_model_loaded(*args: Any, **kwargs: Any) -> None:
    return None


def copilot_request_headers(*args: Any, **kwargs: Any) -> dict[str, str]:
    return {}


def resolve_codex_runtime_credentials(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {}


def resolve_xai_oauth_runtime_credentials(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {}


def resolve_nous_runtime_credentials(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {}


PROVIDER_REGISTRY: dict[str, Any] = {}


def _resolve_kimi_base_url(*args: Any, **kwargs: Any) -> str:
    return ""


def _resolve_zai_base_url(*args: Any, **kwargs: Any) -> str:
    return ""


def _get_named_custom_provider(*args: Any, **kwargs: Any) -> None:
    return None


def _should_use_copilot_responses_api(*args: Any, **kwargs: Any) -> bool:
    return False


def copilot_default_headers(*args: Any, **kwargs: Any) -> dict[str, str]:
    return {}


def github_model_reasoning_efforts(*args: Any, **kwargs: Any) -> list[str]:
    return []


def lmstudio_model_reasoning_options(*args: Any, **kwargs: Any) -> list[str]:
    return []


def ollama_model_supports_thinking(*args: Any, **kwargs: Any) -> bool:
    return False


def _dispatch_pre_tool_call_hooks(*args: Any, **kwargs: Any) -> None:
    return None


class managed_scope:
    def __enter__(self) -> managed_scope:
        return self

    def __exit__(self, *args: Any) -> None:
        return None


def resolve_runtime_provider(*args: Any, **kwargs: Any) -> str:
    return "openai"


__version__ = "neometis-stub"
