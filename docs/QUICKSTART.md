# NéoMêtis — 120-Second Quick Start

## The promise

```bash
git clone https://github.com/neomnia/neometis.git
cd neometis
./neometis.sh run
```

1. No `.env`? → interactive LLM setup (OpenAI / Anthropic / Ollama / Groq)
2. Docker Compose starts Hermes + Qdrant + Chainlit on **port 8000**
3. Browser opens automatically
4. Chat immediately — drag & drop documents into the chat or into `./workspace/docs/`

## Commands

| Command | Action |
|---------|--------|
| `./neometis.sh init` | Interactive `.env` setup + LLM connection test |
| `./neometis.sh run` | Init if needed, start stack, open browser |
| `./neometis.sh stop` | Stop containers |
| `./neometis.sh status` | Health check |

## Document RAG (zero config)

```
./workspace/docs/     ← drop .md, .txt, .json, .pdf here
```

- Auto-indexed on startup
- Re-scanned every 60s while running
- Drag & drop files directly in Chainlit chat

## LLM providers

| # | Provider | Notes |
|---|----------|-------|
| 1 | OpenAI | Direct API key |
| 2 | Anthropic | Via OpenRouter (OpenAI-compatible) |
| 3 | Ollama | Local, no key — default for quick dev |
| 4 | Groq | Fast inference API |

## Remote deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Traefik HTTPS + Basic Auth.
