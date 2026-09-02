"""
NéoMêtis terminal chat — Rich TUI connected to FastAPI SSE.

Usage:
    python -m src.cli.chat
    ./neometis.sh chat
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterator
from typing import Any

import httpx
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()


def api_url() -> str:
    base = os.environ.get("NEOMETIS_API_URL", os.environ.get("NEXT_PUBLIC_API_URL", ""))
    if base:
        return f"{base.rstrip('/')}/api/chat/stream"
    port = os.environ.get("APP_PORT", "8000")
    return f"http://127.0.0.1:{port}/api/chat/stream"


def iter_sse_events(response: httpx.Response) -> Iterator[tuple[str, dict[str, Any]]]:
    """Parse Server-Sent Events frames from the FastAPI stream."""
    event_type = "message"
    for raw_line in response.iter_lines():
        if raw_line is None:
            continue
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("event:"):
            event_type = line[6:].strip()
            continue
        if line.startswith("data:"):
            payload_str = line[5:].strip()
            if payload_str == "[DONE]":
                return
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                continue
            yield event_type, payload


def render_side_event(event_type: str, payload: dict[str, Any]) -> None:
    content = payload.get("content", "")
    metadata = payload.get("metadata") or {}

    if event_type == "thought":
        console.print(f"[dim yellow]⚡ {content}[/dim yellow]")
    elif event_type == "tool_call":
        args = metadata.get("arguments", {})
        console.print(f"[dim cyan]🔧 Tool · {content}[/dim cyan]")
        if args:
            console.print(f"[dim]{json.dumps(args, ensure_ascii=False)}[/dim]")
    elif event_type == "tool_result":
        preview = content if len(content) < 300 else content[:300] + "…"
        console.print(f"[dim green]✓ {preview}[/dim green]")
    elif event_type == "error":
        console.print(f"[bold red]✗ {content}[/bold red]")


def stream_chat_message(message: str, use_rag: bool) -> str:
    """Send one message and return the final assistant text."""
    final_text = ""

    with httpx.stream(
        "POST",
        api_url(),
        json={"message": message, "use_rag": use_rag},
        timeout=120.0,
    ) as response:
        response.raise_for_status()

        with Live(Markdown(""), refresh_per_second=12, console=console, transient=False) as live:
            for event_type, payload in iter_sse_events(response):
                etype = payload.get("type", event_type)
                content = payload.get("content", "")

                if etype in {"thought", "tool_call", "tool_result", "error"}:
                    render_side_event(etype, payload)
                    continue

                if etype == "token":
                    final_text += content
                    live.update(Markdown(final_text))
                elif etype == "final_answer":
                    final_text = content
                    live.update(Markdown(final_text))

    return final_text


def start_terminal_chat() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]NéoMêtis AI Workbench[/bold cyan] "
            "[dim](Hermes Core + Advanced RAG)[/dim]\n"
            f"[dim]{api_url()}[/dim]\n"
            "Tapez [bold red]exit[/bold red] ou [bold red]quit[/bold red] pour quitter.",
            border_style="cyan",
        )
    )

    use_rag = os.environ.get("NEOMETIS_USE_RAG", "true").lower() in {"1", "true", "yes"}
    if sys.stdin.isatty():
        use_rag = Confirm.ask("Activer le RAG (Qdrant) ?", default=use_rag)

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]Vous[/bold green]")
            if user_input.strip().lower() in {"exit", "quit"}:
                console.print("[dim]Fermeture de la session NéoMêtis…[/dim]")
                break
            if not user_input.strip():
                continue

            console.print("\n[bold blue]NéoMêtis[/bold blue]")
            stream_chat_message(user_input, use_rag=use_rag)

        except KeyboardInterrupt:
            console.print("\n[dim]Session interrompue.[/dim]")
            break
        except httpx.ConnectError:
            console.print(
                "[bold red]Impossible de joindre NéoMêtis.[/bold red] "
                "Lancez d'abord : [bold]./neometis.sh run[/bold]"
            )
        except httpx.HTTPStatusError as exc:
            console.print(f"[bold red]Erreur API ({exc.response.status_code})[/bold red]")
        except Exception as exc:  # noqa: BLE001
            console.print(f"[bold red]Erreur : {exc}[/bold red]")


def main() -> None:
    start_terminal_chat()


if __name__ == "__main__":
    main()
