"""
NéoMêtis Chainlit workbench UI.

Mounted at ``/`` on the FastAPI app — interactive agent chat with live
reasoning steps, tool calls, and SSE-compatible event streaming.
"""

from __future__ import annotations

import os

import chainlit as cl

from src.api.agent_service import EventType, stream_agent_events
from src.neometis.version import __version__

if os.environ.get("CHAINLIT_AUTH_SECRET"):

    @cl.password_auth_callback
    def password_auth(username: str, password: str) -> cl.User | None:
        expected_user = os.environ.get("NEOMETIS_AUTH_USER", "admin")
        expected_password = os.environ.get("NEOMETIS_AUTH_PASSWORD", "")
        if username == expected_user and password == expected_password:
            return cl.User(identifier=username, metadata={"role": "admin"})
        return None


@cl.on_chat_start
async def on_chat_start() -> None:
    use_rag = os.environ.get("NEOMETIS_USE_RAG", "false").lower() in {"1", "true", "yes"}
    cl.user_session.set("use_rag", use_rag)

    settings = await cl.ChatSettings(
        [
            cl.input_widget.Switch(id="use_rag", label="Advanced RAG (Qdrant)", initial=use_rag),
        ]
    ).send()

    await cl.Message(
        content=(
            f"**NéoMêtis** v{__version__} — Hermes agent workbench.\n\n"
            "Ask anything about your workspace. Reasoning steps and tool calls appear in the timeline."
        )
    ).send()


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    cl.user_session.set("use_rag", bool(settings.get("use_rag")))


@cl.on_message
async def on_message(message: cl.Message) -> None:
    use_rag = bool(cl.user_session.get("use_rag", False))
    final_answer = ""

    async for event in stream_agent_events(message.content, use_rag=use_rag):
        if event.type == EventType.THOUGHT:
            async with cl.Step(name="Thinking", type="llm") as step:
                step.output = event.content

        elif event.type == EventType.TOOL_CALL:
            async with cl.Step(name=f"Tool · {event.content}", type="tool") as step:
                step.input = event.metadata.get("arguments", {})
                step.output = "Calling tool..."

        elif event.type == EventType.TOOL_RESULT:
            async with cl.Step(name="Tool result", type="tool") as step:
                step.output = event.content

        elif event.type == EventType.TOKEN:
            if not final_answer:
                final_answer = event.content
            else:
                final_answer += event.content

        elif event.type == EventType.FINAL_ANSWER:
            final_answer = event.content

        elif event.type == EventType.ERROR:
            await cl.Message(content=f"**Error:** {event.content}", author="Hermes").send()
            return

    if final_answer:
        await cl.Message(content=final_answer, author="Hermes").send()
