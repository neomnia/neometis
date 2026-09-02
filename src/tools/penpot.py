"""Penpot API sidecar tools (stub)."""

from __future__ import annotations

import os

import httpx

from src.core.hermes.loop import Tool
from src.tools.base import make_tool

_PENPOT_URL = os.environ.get("PENPOT_API_URL", "http://localhost:6060")


async def _list_penpot_files(project_id: str) -> str:
    async with httpx.AsyncClient(base_url=_PENPOT_URL, timeout=30.0) as client:
        resp = await client.get(f"/api/rpc/command/get-project-files", params={"project-id": project_id})
        resp.raise_for_status()
        return resp.text


def build_penpot_tools() -> list[Tool]:
    return [
        make_tool(
            name="penpot_list_files",
            description="List design files in a Penpot project via the API sidecar.",
            parameters={
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "required": ["project_id"],
            },
            handler=_list_penpot_files,
        ),
    ]
