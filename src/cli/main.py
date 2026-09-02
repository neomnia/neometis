"""Console entry point for the global ``neometis`` command (pip install)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    script = _REPO_ROOT / "neometis.sh"
    if not script.is_file():
        print(f"neometis: missing launcher at {script}", file=sys.stderr)
        raise SystemExit(1)
    os.chdir(_REPO_ROOT)
    raise SystemExit(subprocess.call(["bash", str(script), *sys.argv[1:]]))


if __name__ == "__main__":
    main()
