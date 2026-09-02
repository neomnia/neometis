"""Local workspace specs reader/writer (stub)."""

from __future__ import annotations

import os
from pathlib import Path

from src.core.hermes.loop import Tool
from src.tools.base import make_tool

_SPECS_ROOT = Path(os.environ.get("NEOMETIS_SPECS_ROOT", "./workspace/specs"))


async def _read_spec(path: str) -> str:
    target = (_SPECS_ROOT / path).resolve()
    if not str(target).startswith(str(_SPECS_ROOT.resolve())):
        raise ValueError("Path escapes specs root")
    return target.read_text(encoding="utf-8") if target.is_file() else ""


async def _write_spec(path: str, content: str) -> str:
    target = (_SPECS_ROOT / path).resolve()
    if not str(target).startswith(str(_SPECS_ROOT.resolve())):
        raise ValueError("Path escapes specs root")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {target}"


def build_specs_tools() -> list[Tool]:
    return [
        make_tool(
            name="read_spec",
            description="Read a markdown spec file from the local workspace specs directory.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            handler=_read_spec,
        ),
        make_tool(
            name="write_spec",
            description="Write a markdown spec file to the local workspace specs directory.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
            handler=_write_spec,
        ),
    ]
