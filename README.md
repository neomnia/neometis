# NéoMêtis

> **The Lean, Single-Tenant AI Workbench — Hermes Agent engine, re-engineered for Advanced RAG & external UI.**

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-auto--on--push-green.svg)](#versioning--releases)
[![Hermes upstream](https://img.shields.io/badge/Hermes-NousResearch-orange.svg)](https://github.com/NousResearch/hermes-agent)

*NéoMêtis* (from the Greek *Mêtis*, the intelligence of execution and craft) takes the
**ReAct / native function-calling engine** from [Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent)
(MIT), strips its CLI/TUI/gateway shell, wraps it in a **FastAPI SSE API**, and pairs it
with an **Advanced RAG pipeline on Qdrant** — **Chainlit UI + FastAPI** on port **8000**, ready in **120 seconds**.

**Current version:** `<!-- VERSION-START -->0.2.0<!-- VERSION-END -->` · see [Versioning](#versioning--releases)

**Quick start:** [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## What we changed vs. upstream Hermes

| Upstream Hermes | NéoMêtis |
|-----------------|----------|
| Built-in Hermes CLI/TUI | **Replaced** — `./neometis.sh chat` (Rich TUI) + SSE API |
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
├── install.sh                       # Installer entry (Linux / macOS)
├── install.ps1                      # Installer entry (Windows)
├── bin/neometis                     # Global launcher (Unix)
├── bin/neometis.cmd                 # Global launcher (Windows)
├── neometis.sh                      # Main CLI script
├── scripts/install.sh               # Unix installer logic
├── scripts/install.ps1              # Windows installer logic
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
│   ├── cli/chat.py                  # Rich terminal TUI → SSE
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

## Getting started — 120 seconds

```bash
git clone https://github.com/neomnia/neometis.git
cd neometis
./install.sh          # Linux / macOS / Git Bash
neometis run
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/neomnia/neometis.git
cd neometis
.\install.ps1
neometis run
```

The installer supports **all major Linux distributions**, **macOS** (Intel & Apple Silicon), and **Windows 10/11**. It checks Docker & Python, installs the global `neometis` command, and configures your PATH.

Platform matrix: **[docs/INSTALL.md](docs/INSTALL.md)**

| Command | Description |
|---------|-------------|
| `neometis init` | Interactive provider + API key setup |
| `neometis run` | Full stack + browser |
| `neometis chat` | Terminal chat (Rich TUI → SSE) |
| `neometis stop` | Stop containers |
| `./install.sh` | Full install (Linux / macOS / Git Bash) |
| `./install.sh --install-deps` | Auto-install git, python, docker (apt/dnf/pacman/…) |
| `.\install.ps1` | Full install (Windows) |
| `.\install.ps1 -InstallDeps` | Auto-install via winget |

`./neometis.sh` remains an equivalent launcher from the repo root.

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for `./neometis.sh init` only)

### Manual Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| **Chainlit workbench** | http://localhost:8000 |
| API / SSE | http://localhost:8000/api/chat/stream |
| Qdrant | http://localhost:6333 |

### 2. Vendor the Hermes engine (optional, for real LLM runs)

```bash
./scripts/vendor-hermes.sh main
export HERMES_UPSTREAM=1
docker compose up --build core
```

See [docs/HERMES_INTEGRATION.md](docs/HERMES_INTEGRATION.md) for the exact files imported
and stripped.

### 3. Chat from the terminal

```bash
./neometis.sh chat
# or: python -m src.cli.chat
```

Markdown rendering, live token streaming, and RAG/tool-call visibility — no curl required.

### 4. Stream via curl (integrations)

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
