"""Plane.so API tools (stub)."""

from __future__ import annotations

import os

import httpx

from src.core.hermes.loop import Tool
from src.tools.base import make_tool

_PLANE_URL = os.environ.get("PLANE_API_URL", "http://localhost:8001")
_PLANE_TOKEN = os.environ.get("PLANE_API_TOKEN", "")


async def _list_plane_issues(project_id: str) -> str:
    headers = {"Authorization": f"Bearer {_PLANE_TOKEN}"} if _PLANE_TOKEN else {}
    async with httpx.AsyncClient(base_url=_PLANE_URL, timeout=30.0) as client:
        resp = await client.get(
            f"/api/v1/workspaces/default/projects/{project_id}/issues/",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.text


def build_plane_tools() -> list[Tool]:
    return [
        make_tool(
            name="plane_list_issues",
            description="List issues for a Plane.so project.",
            parameters={
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "required": ["project_id"],
            },
            handler=_list_plane_issues,
        ),
    ]
