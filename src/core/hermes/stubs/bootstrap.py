"""Install headless stubs for Hermes modules stripped by NéoMêtis."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType


def install_upstream_stubs() -> None:
    """Register stub packages before loading vendored upstream modules."""
    stubs_root = Path(__file__).resolve().parent
    stubs_str = str(stubs_root)
    if stubs_str not in sys.path:
        sys.path.insert(0, stubs_str)

    for name in ("hermes_cli", "gateway", "hermes_state", "hermes_bootstrap"):
        if name not in sys.modules:
            mod = ModuleType(name)
            mod.__path__ = []  # type: ignore[attr-defined]
            sys.modules[name] = mod

    bootstrap = ModuleType("hermes_bootstrap")
    sys.modules["hermes_bootstrap"] = bootstrap

    gateway = ModuleType("gateway")
    gateway.__path__ = []  # type: ignore[attr-defined]
    sys.modules["gateway"] = gateway

    session_ctx = ModuleType("gateway.session_context")
    from src.core.hermes.stubs.gateway import session_context as sc

    session_ctx.get_session_env = sc.get_session_env  # type: ignore[attr-defined]
    sys.modules["gateway.session_context"] = session_ctx

    hs = ModuleType("hermes_state")
    from src.core.hermes.stubs import hermes_state as hs_impl

    hs.get_shared_session_db = hs_impl.get_shared_session_db  # type: ignore[attr-defined]
    hs.release_or_close = hs_impl.release_or_close  # type: ignore[attr-defined]
    sys.modules["hermes_state"] = hs

    from src.core.hermes.stubs import hermes_cli
    from src.core.hermes.stubs.hermes_cli import env_loader, profiles, timeouts

    sys.modules["hermes_cli.env_loader"] = env_loader
    sys.modules["hermes_cli.timeouts"] = timeouts
    sys.modules["hermes_cli.profiles"] = profiles
    sys.modules["hermes_cli"].__version__ = hermes_cli.__version__  # type: ignore[attr-defined]

    from src.core.hermes.stubs.hermes_cli import _subprocess_compat, config, goals

    sys.modules["hermes_cli._subprocess_compat"] = _subprocess_compat
    sys.modules["hermes_cli.config"] = config
    sys.modules["hermes_cli.goals"] = goals

    import src.core.hermes.stubs.cron as cron_pkg

    sys.modules["cron"] = cron_pkg

    from src.core.hermes.stubs import hermes_state_common, plugins

    sys.modules["hermes_state_common"] = hermes_state_common
    plugins_mod = ModuleType("plugins")
    plugins_mod.__path__ = []  # type: ignore[attr-defined]
    plugins_mod.discover = plugins.discover  # type: ignore[attr-defined]
    sys.modules["plugins"] = plugins_mod

    for sub in ("web", "video_gen"):
        sys.modules[f"plugins.{sub}"] = ModuleType(f"plugins.{sub}")


def install_tool_stubs() -> None:
    """Pre-register heavy upstream tool modules (sys.modules wins over sys.path)."""
    terminal_tool = ModuleType("tools.terminal_tool")
    terminal_tool.cleanup_vm = lambda *a, **k: None  # type: ignore[attr-defined]
    terminal_tool.get_active_env = lambda *a, **k: "local"  # type: ignore[attr-defined]
    sys.modules["tools.terminal_tool"] = terminal_tool

    browser_tool = ModuleType("tools.browser_tool")
    browser_tool.cleanup_browser = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules["tools.browser_tool"] = browser_tool

    interrupt_mod = ModuleType("tools.interrupt")
    interrupt_mod.set_interrupt = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules["tools.interrupt"] = interrupt_mod


def install_agent_stubs() -> None:
    """Stub heavy agent modules that pull CLI dependencies."""

    def sanitize_context(messages, **kwargs):
        return messages

    memory_manager = ModuleType("agent.memory_manager")
    memory_manager.sanitize_context = sanitize_context  # type: ignore[attr-defined]
    sys.modules["agent.memory_manager"] = memory_manager
