"""Dynamic versioning for NéoMêtis.

The base semver lives in ``VERSION`` at the repository root. When built from
git, ``__version__`` appends branch and commit metadata so every deployment
is traceable (mirrors CI release tags).
"""

from __future__ import annotations

import os
import subprocess
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VERSION_FILE = _REPO_ROOT / "VERSION"


def _read_base_version() -> str:
    if _VERSION_FILE.is_file():
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0"


@lru_cache(maxsize=1)
def _git_metadata() -> tuple[str, str]:
    """Return (branch, short_sha) or empty strings when git is unavailable."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return branch, sha
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "", ""


def resolve_version() -> str:
    """Build the runtime version string."""
    base = _read_base_version()
    branch, sha = _git_metadata()

    # CI sets these explicitly for reproducible release artifacts.
    ci_branch = os.environ.get("NEOMETIS_BRANCH", "").strip()
    ci_sha = os.environ.get("NEOMETIS_SHA", "").strip()
    branch = ci_branch or branch
    sha = ci_sha or sha

    if branch and sha:
        slug = branch.replace("/", "-")
        if slug in ("main", "master") and not ci_branch:
            return base
        return f"{base}+{slug}.{sha}"
    return base


__version__ = resolve_version()
