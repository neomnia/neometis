# NéoMêtis

> **The Lean, Single-Tenant AI Workbench — Hermes Agent engine, re-engineered for Advanced RAG & external UI.**

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-auto--on--push-green.svg)](#versioning--releases)
[![Hermes upstream](https://img.shields.io/badge/Hermes-NousResearch-orange.svg)](https://github.com/NousResearch/hermes-agent)

*NéoMêtis* (from the Greek *Mêtis*, the intelligence of execution and craft) takes the
**ReAct / native function-calling engine** from [Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent)
(MIT), strips its CLI/TUI/gateway shell, wraps it in a **FastAPI SSE API**, and pairs it
with an **Advanced RAG pipeline on Qdrant** — all behind a **Next.js 15** UI you own.

**Current version:** `<!-- VERSION-START -->0.2.0<!-- VERSION-END -->` · see [Versioning](#versioning--releases)

---

## What we changed vs. upstream Hermes

| Upstream Hermes | NéoMêtis |
|-----------------|----------|
| Built-in CLI + TUI chat | **Removed** — SSE API for any UI |
| Telegram/Discord/Slack gateway | **Removed** — single-tenant web UI |
| Plugin memory (Honcho, SQLite state) | **Replaced** — Qdrant Advanced RAG |
| Monolithic install (~700k LOC) | **Vendored lean engine** (~engine subset) |
| Multi-session SaaS assumptions | **Single workspace, single team** |

Full import/cleanup guide: **[docs/HERMES_INTEGRATION.md](docs/HERMES_INTEGRATION.md)**

---

## Architecture

```
┌──────────────────────┐   SSE (tokens, thoughts, tool calls)   ┌──────────────────────┐
│  Next.js 15 (ui/)     │  <──────────────────────────────────  │  FastAPI (src/api/)   │
│  Tailwind · Shadcn/UI │  ──────────────────────────────────>  │  /api/chat/stream     │
└──────────────────────┘                                         └──────────┬───────────┘
                                                                              │
                                                                              ▼
                                                               ┌──────────────────────────┐
                                                               │ src/core/hermes/          │
                                                               │  adapter.py               │
                                                               │  ├─ upstream/ (vendored)  │
                                                               │  └─ loop.py (fallback)    │
                                                               └──────────┬───────────────┘
                                                    ┌────────────────────┼────────────────────┐
                                                    ▼                    ▼                    ▼
                                         ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
                                         │ src/memory/rag/  │  │ src/tools/    │  │ LLM provider     │
                                         │ Hybrid + Rerank  │  │ Specs Penpot  │  │ (OpenAI-compat)  │
                                         │ Qdrant           │  │ Plane.so      │  │                  │
                                         └────────┬────────┘  └──────────────┘  └─────────────────┘
                                                  ▼
                                         ┌─────────────────┐
                                         │ Qdrant           │
                                         └─────────────────┘
```

### Repository layout

```
neometis/
├── VERSION                          # Base semver (dynamic suffix from git/CI)
├── docker-compose.yml               # core + qdrant + web
├── docs/
│   └── HERMES_INTEGRATION.md        # Import/cleanup/encapsulation guide
├── scripts/
│   └── vendor-hermes.sh             # Vendor Hermes engine subset
├── src/
│   ├── neometis/version.py          # Dynamic version resolver
│   ├── core/hermes/                 # Adapted Hermes engine
│   │   ├── adapter.py               # Upstream vs lean facade
│   │   ├── stream_bridge.py         # Hermes → SSE events
│   │   ├── upstream/                # Vendored Nous Research code (generated)
│   │   └── loop.py                  # Lean fallback ReAct loop
│   ├── memory/rag/                  # Advanced RAG (substitutes Hermes memory)
│   ├── tools/                       # Native Penpot, Plane, Specs tools
│   └── api/main.py                  # FastAPI + SSE
└── ui/                              # Next.js 15 App Router
```

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Agent engine | Hermes ReAct loop (vendored from Nous Research, MIT) |
| Backend | FastAPI (Python 3.12+), SSE streaming |
| Vector DB / RAG | Qdrant — hybrid BM25 + dense, Parent-Child chunking, BGE/FlashRank reranking |
| Frontend | Next.js 15, Tailwind CSS, Shadcn/UI (roadmap) |
| Tooling | Local specs workspace, Penpot API sidecar, Plane.so API |

---

## Getting started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (local dev)
- Node.js 20+ (UI dev)

### 1. Run with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:3000 |
| Core API | http://localhost:8000 |
| Qdrant | http://localhost:6333 |

### 2. Vendor the Hermes engine (optional, for real LLM runs)

```bash
./scripts/vendor-hermes.sh main
export HERMES_UPSTREAM=1
docker compose up --build core
```

See [docs/HERMES_INTEGRATION.md](docs/HERMES_INTEGRATION.md) for the exact files imported
and stripped.

### 3. Stream a chat completion

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Hermes", "use_rag": false}'
```

Health (includes dynamic version + engine mode):

```bash
curl -s http://localhost:8000/health | jq
```

---

## Versioning & releases

NéoMêtis uses **two-tier versioning**:

1. **Base semver** — stored in [`VERSION`](VERSION) (currently `0.2.0`).
2. **Dynamic build id** — appended at runtime and in CI:
   - Local git: `0.2.0+branch-name.abc1234`
   - `main` branch releases: `v0.2.0`

### Automatic releases

Every push to **any branch** triggers [`.github/workflows/release.yml`](.github/workflows/release.yml):

| Branch | GitHub Release tag | Type |
|--------|-------------------|------|
| `main` | `v{VERSION}` | Stable release |
| Other branches | `v{VERSION}-{branch}.{sha}` | Pre-release (traceable snapshot) |

Each release attaches `dist/version.json` with `{ version, branch, sha, tag }`.

Check your running build:

```bash
python -c "from src.neometis.version import __version__; print(__version__)"
curl -s http://localhost:8000/health | jq .version
```

Response headers on `/api/chat/stream`:

- `X-Neometis-Version`
- `X-Hermes-Engine` (`lean` or `upstream`)

---

## Roadmap

- [x] Repository scaffold with `core/hermes/`, `memory/rag/`, `tools/`, `api/`, `ui/`
- [x] Hermes integration guide + vendor script
- [x] FastAPI SSE wrapper with lean fallback loop
- [x] Advanced RAG pipeline skeleton (Qdrant)
- [x] Native tool stubs (Specs, Penpot, Plane.so)
- [x] Auto-release on every branch push
- [ ] Full upstream Hermes vendor CI smoke test
- [ ] Hybrid BM25 sparse vectors in Qdrant
- [ ] Embedding + ingest pipeline
- [ ] Next.js chat UI with live thought/tool timeline (Shadcn/UI)
- [ ] Production single-tenant deployment guide

---

## Contributing

MIT licensed — issues and PRs welcome. Keep changes lean and aligned with the
single-tenant philosophy. When touching the Hermes engine, update
[docs/HERMES_INTEGRATION.md](docs/HERMES_INTEGRATION.md).

## License

MIT — see [LICENSE](LICENSE). Compatible with the MIT license of
[Hermes Agent](https://github.com/NousResearch/hermes-agent) from
[Nous Research](https://nousresearch.com).
