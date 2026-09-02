import sys

from src.core.hermes.stubs.hermes_cli import windows_hide_flags

IS_WINDOWS = sys.platform.startswith("win")

__all__ = ["IS_WINDOWS", "windows_hide_flags"]
