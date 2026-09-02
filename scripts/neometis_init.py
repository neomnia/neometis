#!/usr/bin/env python3
"""Interactive NéoMêtis environment bootstrap."""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"

PROVIDERS = {
    "1": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "needs_key": True,
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-small",
    },
    "2": {
        "name": "Anthropic (via OpenRouter)",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-3.5-sonnet",
        "needs_key": True,
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-small",
        "embedding_base_url": "https://openrouter.ai/api/v1",
    },
    "3": {
        "name": "Ollama / Local",
        "base_url": "http://host.docker.internal:11434/v1",
        "default_model": "llama3.2",
        "needs_key": False,
        "embedding_provider": "hash",
        "embedding_model": "n/a",
    },
    "4": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "needs_key": True,
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-small",
    },
}


def prompt(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{msg}{suffix}: ").strip()
    return value or default


def test_llm(base_url: str, api_key: str, model: str) -> None:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: NéoMêtis OK"}],
        "max_tokens": 16,
    }
    url = f"{base_url.rstrip('/')}/chat/completions"
    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
    print("✓ LLM connection OK")


def write_env(provider: dict, api_key: str, model: str) -> None:
    template = ENV_EXAMPLE.read_text(encoding="utf-8") if ENV_EXAMPLE.is_file() else ""
    lines: dict[str, str] = {}

    for line in template.splitlines():
        if line.strip().startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        lines[key.strip()] = value.strip()

    lines["HERMES_API_BASE_URL"] = provider["base_url"]
    lines["HERMES_MODEL_NAME"] = model
    lines["HERMES_API_KEY"] = api_key
    lines["EMBEDDING_PROVIDER"] = provider["embedding_provider"]
    lines["EMBEDDING_MODEL"] = provider.get("embedding_model", "text-embedding-3-small")
    lines["EMBEDDING_API_BASE_URL"] = provider.get("embedding_base_url", provider["base_url"])
    lines["EMBEDDING_API_KEY"] = api_key if provider["embedding_provider"] == "openai" else ""
    lines["NEOMETIS_USE_RAG"] = "true"
    lines["NEOMETIS_AUTO_INDEX"] = "true"
    lines["NEOMETIS_DOCS_DIR"] = "/app/workspace/docs"
    lines["APP_PORT"] = "8000"

    ordered_keys = list(lines.keys())
    if ENV_EXAMPLE.is_file():
        ordered_keys = []
        seen = set()
        for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key = line.split("=", 1)[0].strip()
                if key in lines:
                    ordered_keys.append(key)
                    seen.add(key)
        for key in lines:
            if key not in seen:
                ordered_keys.append(key)

    ENV_FILE.write_text("\n".join(f"{k}={lines[k]}" for k in ordered_keys) + "\n", encoding="utf-8")
    print(f"✓ Wrote {ENV_FILE}")


def ensure_workspace() -> None:
    docs = ROOT / "workspace" / "docs"
    specs = ROOT / "workspace" / "specs"
    state = ROOT / "workspace" / ".neometis"
    docs.mkdir(parents=True, exist_ok=True)
    specs.mkdir(parents=True, exist_ok=True)
    state.mkdir(parents=True, exist_ok=True)

    readme = docs / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Drop your documents here\n\n"
            "Supported formats: `.md`, `.txt`, `.json`, `.pdf`\n\n"
            "Files are auto-indexed into Qdrant when NéoMêtis starts.\n",
            encoding="utf-8",
        )
    print(f"✓ Workspace ready at {docs}")


def main() -> int:
    print("\n🪶 NéoMêtis — interactive setup\n")
    print("Which LLM provider do you want to use?")
    for key, cfg in PROVIDERS.items():
        print(f"  ({key}) {cfg['name']}")
    choice = prompt("Choice", "3")
    provider = PROVIDERS.get(choice, PROVIDERS["3"])

    api_key = ""
    if provider["needs_key"]:
        api_key = getpass.getpass(f"{provider['name']} API key: ").strip()
        if not api_key:
            print("API key required.", file=sys.stderr)
            return 1

    model = prompt("Model", provider["default_model"])

    print("\nTesting LLM connection...")
    test_base = provider["base_url"]
    if choice == "3":
        # Test host-local Ollama before Docker overrides the URL.
        test_base = "http://127.0.0.1:11434/v1"
    try:
        test_llm(test_base, api_key, model)
    except Exception as exc:  # noqa: BLE001
        if choice == "3":
            print(f"⚠ Ollama not reachable locally ({exc}). Continuing — Docker will use host.docker.internal.")
        else:
            print(f"✗ Connection failed: {exc}", file=sys.stderr)
            return 1

    write_env(provider, api_key, model)
    ensure_workspace()
    print("\nDone. Run: ./neometis.sh run\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
