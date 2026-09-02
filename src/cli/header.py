"""NéoMêtis brand header — animated owl totem for the terminal TUI."""

from __future__ import annotations

import time
from dataclasses import dataclass

from rich.console import Console
from rich.live import Live
from rich.text import Text

from src.neometis.version import __version__

console = Console()

SEPARATOR = "\n[dim #334155]───────────────────────────────────────────────────────────────[/dim #334155]\n"


@dataclass(frozen=True)
class HeaderContext:
    version: str
    engine: str = "hermes-react"
    rag: str = "qdrant-hybrid"
    status: str = "active"

    @classmethod
    def from_health(cls, health: dict[str, str] | None, *, use_rag: bool) -> HeaderContext:
        if health:
            engine = health.get("hermes_engine", "hermes-react")
            embedding = health.get("embedding_provider", "openai")
            rag = f"qdrant-{embedding}" if health.get("rag_enabled") == "true" else "disabled"
            return cls(
                version=health.get("version", __version__),
                engine=engine,
                rag=rag,
                status=health.get("status", "active"),
            )
        return cls(
            version=__version__,
            rag="qdrant-hybrid" if use_rag else "disabled",
            status="connecting",
        )


def _owl_frames(version: str) -> list[str]:
    version_line = f"WORKBENCH v{version.split('+', 1)[0]}"
    tail_variants = ("█", "▄▀", "▀▄")
    frames: list[str] = []
    for tail in tail_variants:
        frames.append(
            f"""
 [bold #00F5FF] ▄▀▀▄   ▄▀▀▄ [/bold #00F5FF]  [bold #00F5FF]█▄ █ █▀▀ █▀█ █▀▄▀█ █▀▀ ▀█▀ █ █▀[/bold #00F5FF]
 [bold #00F5FF]█  ██   ██  █[/bold #00F5FF]  [bold #6366F1]█ ▀█ ██▄ █▄█ █ ▀ █ ██▄  █  █ ▄█[/bold #6366F1]
 [bold #00F5FF]█  [white]▀▄[/white] █ █ [white]▄▀[/white]  █[/bold #00F5FF]  [dim white]{version_line}[/dim white]
 [bold #00F5FF] ▀▄ [white] ▀▀ [/white] ▄▀ [/bold #00F5FF] [bold #00F5FF]{tail}[/bold #00F5FF]
"""
        )
    return frames


def render_header_frame(frame_index: int, ctx: HeaderContext) -> Text:
    frames = _owl_frames(ctx.version)
    content = frames[frame_index % len(frames)].strip("\n")
    status_color = "green" if ctx.status in {"ok", "active"} else "yellow"
    status_label = "active" if ctx.status == "ok" else ctx.status
    status_bar = (
        f" [bold cyan]engine[/bold cyan] {ctx.engine}  [dim]•[/dim]  "
        f"[bold purple]rag[/bold purple] {ctx.rag}  [dim]•[/dim]  "
        f"[bold {status_color}]status[/bold {status_color}] {status_label}"
    )
    return Text.from_markup(f"{content}{SEPARATOR}{status_bar}{SEPARATOR}")


def play_intro_animation(ctx: HeaderContext, *, duration_sec: float = 1.2) -> None:
    """Play the owl totem animation before opening the chat prompt."""
    with Live(render_header_frame(0, ctx), console=console, refresh_per_second=10) as live:
        start = time.time()
        frame = 0
        while time.time() - start < duration_sec:
            time.sleep(0.12)
            frame += 1
            live.update(render_header_frame(frame, ctx))


def print_static_header(ctx: HeaderContext) -> None:
    """Print the final header frame without animation."""
    console.print(render_header_frame(0, ctx))
