# NéoMêtis

> **The Lean, Single-Tenant AI Workbench powered by Hermes Agent & Advanced RAG.**

*NéoMêtis* (from the Greek *Mêtis*, the intelligence of cunning and execution) is a
stripped-down, self-hosted, single-tenant AI workbench. It brings studio-grade
agentic capabilities — specs, UX, and code generation — to a single team or a
single developer, without the operational weight of a multi-tenant SaaS
platform.

It is built around the **Hermes** agent engine (a lean fork/module inspired by
[Nous Research's Hermes models](https://github.com/NousResearch)), a native
**ReAct + Function Calling** loop, and an **Advanced RAG** pipeline on top of
**Qdrant**.

## Why NéoMêtis?

- 🪶 **Lean by design** — no tenants, no billing, no multi-org plumbing. One
  workspace, one team, zero incidental complexity.
- 🧠 **Hermes-native reasoning** — a transparent ReAct loop with native
  function calling, streamed token-by-token so you can watch the agent think.
- 🔎 **Advanced RAG, not naive RAG** — hybrid BM25 + dense retrieval,
  Parent-Child semantic chunking, and BGE/FlashRank reranking out of the box.
- 🛠️ **Workspace-native tools** — first-class tools for local specs, a Penpot
  API sidecar, and the Plane.so API, so the agent can act on your real project
  artifacts.
- 🧩 **Modern, open stack** — FastAPI + SSE, Next.js 15, Tailwind, Shadcn/UI,
  Qdrant. No proprietary lock-in.

## Architecture

```
┌─────────────────────┐      SSE (reasoning + tool calls)      ┌─────────────────────┐
│   Next.js 15 (UI)    │  <───────────────────────────────────  │   FastAPI (API)      │
│  Tailwind + Shadcn/UI │  ────────────────────────────────────>  │  src/api/main.py     │
└─────────────────────┘        POST /api/chat/stream            └──────────┬──────────┘
                                                                            │
                                                                            ▼
                                                                 ┌─────────────────────┐
                                                                 │   Hermes Agent Core  │
                                                                 │  src/core/agent.py   │
                                                                 │  ReAct + Function    │
                                                                 │  Calling loop        │
                                                                 └──────────┬──────────┘
                                                              ┌─────────────┼─────────────┐
                                                              ▼             ▼             ▼
                                                     ┌───────────────┐ ┌─────────┐ ┌───────────────┐
                                                     │ src/memory     │ │ src/tools│ │ Native tools  │
                                                     │ Qdrant Advanced│ │ Function │ │ Specs, Penpot,│
                                                     │ RAG (hybrid +  │ │ calling  │ │ Plane.so APIs │
                                                     │ rerank)        │ │ registry │ │               │
                                                     └───────┬───────┘ └─────────┘ └───────────────┘
                                                              ▼
                                                     ┌───────────────┐
                                                     │    Qdrant      │
                                                     │ (vector store) │
                                                     └───────────────┘
```

### Repository layout

```
neometis/
├── docker-compose.yml        # Core API + Qdrant + Web, one command to run everything
├── docker/                   # Dockerfiles for the core API and the web UI
├── requirements.txt          # Python dependencies for the core/API
├── .env.example              # Environment variables template
└── src/
    ├── core/                 # Hermes ReAct agent loop (agent.py)
    ├── memory/               # Qdrant-backed Advanced RAG memory (qdrant_store.py)
    ├── tools/                # Native function-calling tools (specs, Penpot, Plane.so)
    └── api/                  # FastAPI app + SSE streaming endpoints (main.py)
└── ui/                       # Next.js 15 App Router frontend (Tailwind + Shadcn/UI)
```

## Tech stack

| Layer            | Technology                                                        |
| ---------------- | ------------------------------------------------------------------ |
| Agent engine     | Hermes (ReAct loop, native function calling)                       |
| Backend / API    | FastAPI (Python 3.12+), Server-Sent Events (SSE)                    |
| Vector DB / RAG  | Qdrant — hybrid BM25 + dense search, Parent-Child chunking, BGE/FlashRank reranking |
| Frontend         | Next.js 15 (App Router), Tailwind CSS, Shadcn/UI                    |
| Tooling          | Local workspace files, Penpot API sidecar, Plane.so API             |

## Getting started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development without Docker)
- Node.js 20+ (for local UI development without Docker)

### Run with Docker Compose (recommended)

```bash
cp .env.example .env
docker compose up --build
```

This starts three services:

- `qdrant` — the vector database, on `http://localhost:6333`
- `core` — the FastAPI + Hermes agent API, on `http://localhost:8000`
- `web` — the Next.js UI, on `http://localhost:3000`

### Run the core API locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

Health check: `curl http://localhost:8000/health`

Stream a chat completion:

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Hermes!"}'
```

### Run the UI locally

```bash
cd ui
npm install
npm run dev
```

## Roadmap

- [x] Repository scaffold: `core`, `memory`, `tools`, `api`, `ui`
- [x] Minimal Hermes ReAct loop with SSE streaming (FastAPI)
- [ ] Wire the Hermes engine to a real model backend (local or hosted)
- [ ] Advanced RAG: hybrid BM25 + dense search on Qdrant
- [ ] Parent-Child semantic chunking pipeline
- [ ] BGE / FlashRank reranking stage
- [ ] Native tools: local workspace (specs) reader/writer
- [ ] Native tools: Penpot API sidecar integration
- [ ] Native tools: Plane.so API integration
- [ ] Next.js 15 chat UI with live thought/tool-call timeline (Shadcn/UI)
- [ ] Authentication-free, single-tenant deployment guide

## Contributing

NéoMêtis is open source under the MIT License. Issues and pull requests are
welcome — please keep changes lean and in line with the single-tenant
philosophy of the project.

## License

MIT — see [LICENSE](LICENSE). Compatible with the MIT license of the Hermes
engine from [Nous Research](https://github.com/NousResearch).

