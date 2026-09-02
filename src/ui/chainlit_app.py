"""
NéoMêtis Chainlit workbench UI.

Mounted at ``/`` on the FastAPI app — interactive agent chat with live
reasoning steps, tool calls, drag-and-drop document upload, and RAG.
"""

from __future__ import annotations

import os
from pathlib import Path

import chainlit as cl

from src.api.agent_service import EventType, index_uploaded_text, stream_agent_events
from src.memory.rag.document_loader import SUPPORTED_EXTENSIONS, extract_text
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
    use_rag = os.environ.get("NEOMETIS_USE_RAG", "true").lower() in {"1", "true", "yes"}
    cl.user_session.set("use_rag", use_rag)

    await cl.ChatSettings(
        [
            cl.input_widget.Switch(id="use_rag", label="Advanced RAG (Qdrant)", initial=use_rag),
        ]
    ).send()

    await cl.Message(
        content=(
            f"**NéoMêtis** v{__version__} — ready in seconds.\n\n"
            "- Chat with Hermes below\n"
            "- **Drag & drop** `.md`, `.txt`, `.json`, `.pdf` files into the chat to index them\n"
            "- Or drop files into `./workspace/docs/` — auto-indexed on startup\n"
        )
    ).send()


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    cl.user_session.set("use_rag", bool(settings.get("use_rag")))


async def _handle_uploads(message: cl.Message) -> None:
    if not message.elements:
        return

    for element in message.elements:
        if not isinstance(element, cl.File):
            continue

        path = Path(element.path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            await cl.Message(content=f"Unsupported file type: {path.suffix}").send()
            continue

        try:
            text = extract_text(path)
            chunks = await index_uploaded_text(path.name, text)
            await cl.Message(
                content=f"Indexed **{path.name}** into Qdrant ({chunks} chunks). Ask questions about it!",
            ).send()
        except Exception as exc:  # noqa: BLE001
            await cl.Message(content=f"Failed to index **{path.name}**: {exc}").send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    await _handle_uploads(message)

    user_text = (message.content or "").strip()
    if not user_text and message.elements:
        return

    use_rag = bool(cl.user_session.get("use_rag", True))
    final_answer = ""

    async for event in stream_agent_events(user_text, use_rag=use_rag):
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
            final_answer = final_answer + event.content if final_answer else event.content

        elif event.type == EventType.FINAL_ANSWER:
            final_answer = event.content

        elif event.type == EventType.ERROR:
            await cl.Message(content=f"**Error:** {event.content}", author="Hermes").send()
            return

    if final_answer:
        await cl.Message(content=final_answer, author="Hermes").send()
