# Hermes Agent Integration Guide

This document explains **exactly** how NéoMêtis imports, cleans, and encapsulates the
[Hermes Agent](https://github.com/NousResearch/hermes-agent) engine from Nous Research
(MIT license).

NéoMêtis is not a fork of the entire Hermes monolith. We **surgically vendor** the
ReAct / native function-calling engine and **delete** everything that assumes a built-in
CLI, TUI, or multi-platform chat gateway.

---

## Strategy Overview

| Layer | Hermes upstream | NéoMêtis decision |
|-------|-----------------|-------------------|
| Reasoning loop | `run_agent.AIAgent` + `agent/conversation_loop.py` | **Keep** — vendored into `src/core/hermes/upstream/` |
| Tool dispatch | `agent/tool_executor.py`, `model_tools.py`, `tools/registry.py` | **Keep** — register NéoMêtis native tools |
| LLM adapters | `agent/relay_llm.py`, provider adapters | **Keep selectively** — only providers you configure |
| Memory / RAG | `agent/memory_manager.py`, Honcho plugins | **Remove** — replaced by `src/memory/rag/` (Qdrant) |
| CLI / TUI | `cli.py`, `hermes_cli/`, `tui_gateway/`, `ui-tui/` | **Remove completely** |
| Messaging gateway | `gateway/` (Telegram, Discord, …) | **Remove** — Next.js UI + FastAPI SSE instead |
| Session state | `hermes_state*.py` (SQLite) | **Remove** — single-tenant; optional session id via API |
| Web dashboard | `web/`, `website/` | **Remove** — NéoMêtis `ui/` replaces it |

---

## Directory Mapping

After `./scripts/vendor-hermes.sh`, upstream files land here:

```
src/core/hermes/
├── adapter.py          # NéoMêtis facade — upstream or lean fallback
├── stream_bridge.py    # Maps upstream callbacks → SSE AgentEvent
├── upstream.py         # Factory: headless AIAgent, no CLI/TUI
├── loop.py             # Lean fallback ReAct loop (no vendor yet)
├── events.py           # Stable SSE contract for the UI
└── upstream/           # Vendored Hermes subset (gitignored until vendor run)
    ├── run_agent.py
    ├── model_tools.py
    ├── agent/
    │   ├── conversation_loop.py   ← main ReAct loop (~500 KB)
    │   ├── tool_executor.py       ← sequential/concurrent tool dispatch
    │   ├── chat_completion_helpers.py
    │   └── … (support modules pulled transitively)
    └── tools/
        └── registry.py
```

NéoMêtis API layer:

```
src/api/main.py  →  HermesEngineAdapter.run()  →  SSE /api/chat/stream
```

Advanced RAG (substitutes Hermes memory):

```
src/memory/rag/pipeline.py  →  Qdrant hybrid search + reranking
```

---

## Step-by-Step Import Procedure

### 1. Vendor upstream code

```bash
./scripts/vendor-hermes.sh main
# or pin a commit:
./scripts/vendor-hermes.sh 26f178e5fa78c691cadf847058ef1d55a707bfb0
```

The script copies **only** the engine directories listed in `scripts/vendor-hermes.sh`
and writes `upstream/.vendored` with provenance metadata.

### 2. Enable upstream mode

```bash
export HERMES_UPSTREAM=1
export HERMES_MODEL_NAME=NousResearch/Hermes-3-Llama-3.1-8B
export HERMES_API_BASE_URL=http://localhost:8080/v1
export HERMES_API_KEY=sk-...
```

Restart the core API (`docker compose up core` or `uvicorn src.api.main:app`).

Verify:

```bash
curl -s http://localhost:8000/health | jq
# "hermes_engine": "upstream"
```

### 3. Strip CLI / TUI dependencies (already done by vendor script)

The vendor script **never copies**:

| Upstream path | Reason |
|---------------|--------|
| `cli.py` (1 MB+) | Interactive terminal chat — replaced by SSE API |
| `hermes_cli/` | Profile/config TUI bridge |
| `tui_gateway/`, `ui-tui/` | Terminal UI servers |
| `gateway/` | Telegram/Discord/Slack adapters |
| `hermes_state.py` + siblings | Multi-session SQLite — conflicts with single-tenant Qdrant RAG |
| `agent/memory_manager.py` | Plugin memory orchestration — replaced by `AdvancedRAGPipeline` |
| `web/`, `website/` | Hermes dashboard — replaced by `ui/` (Next.js 15) |

If you manually sync upstream later, re-run the vendor script rather than copying the
full repository.

### 4. Isolate the conversation loop

Upstream entry point:

```python
# upstream/run_agent.py
class AIAgent:
    def run_conversation(self, user_message: str) -> str: ...
```

Implementation body (extracted upstream):

```python
# upstream/agent/conversation_loop.py
async def run_conversation_loop(agent, user_message, ...): ...
```

NéoMêtis wraps this in `src/core/hermes/stream_bridge.py`:

1. Patches quiet mode (`HERMES_QUIET=1`, `HERMES_NO_TUI=1`).
2. Runs `run_conversation` in a thread pool (upstream is sync).
3. Emits normalized `AgentEvent` frames for SSE.

### 5. Register NéoMêtis-native tools

Hermes discovers tools via `tools/registry.py` (`register()` decorator) and exposes
schemas through `model_tools.get_tool_definitions()`.

NéoMêtis tools live in `src/tools/`:

| Module | Tools |
|--------|-------|
| `specs.py` | `read_spec`, `write_spec` |
| `penpot.py` | `penpot_list_files` |
| `plane.py` | `plane_list_issues` |

Wire them in `src/core/hermes/upstream.py#create_agent()` once vendored
`model_tools.py` is present (hook point marked in source).

### 6. Substitute memory with Advanced RAG

**Remove / do not vendor:**

- `agent/memory_manager.py`
- `agent/memory_provider.py`
- Honcho / external memory plugins under `plugins/`

**Use instead:**

```python
from src.memory.rag import AdvancedRAGPipeline

rag = AdvancedRAGPipeline()
chunks = await rag.retrieve(query, query_vector)
```

The FastAPI layer optionally prepends retrieved context before calling
`HermesEngineAdapter.run()` when `use_rag: true` is sent to `/api/chat/stream`.

Pipeline stages (`src/memory/rag/`):

1. `chunking.py` — Parent-Child semantic chunks
2. `hybrid_search.py` — BM25 + dense (dense wired; sparse vectors next)
3. `reranker.py` — BGE / FlashRank
4. `pipeline.py` — orchestrator over Qdrant

---

## Key Upstream Classes & Files

| Upstream symbol | File | NéoMêtis usage |
|-----------------|------|----------------|
| `AIAgent` | `run_agent.py` | Instantiated by `upstream.create_agent()` |
| `run_conversation_loop` | `agent/conversation_loop.py` | Core ReAct + tool-use loop |
| `execute_tool_calls_*` | `agent/tool_executor.py` | Native function calling execution |
| `get_tool_definitions` | `model_tools.py` | OpenAI-compatible tool schemas |
| `handle_function_call` | `model_tools.py` | Dispatch to registered handlers |
| `MemoryManager` | `agent/memory_manager.py` | **Not used** — delete on sync |
| `cli.py` / `hermes_cli` | root | **Not used** — delete on sync |

---

## SSE Event Contract (stable for UI)

Regardless of upstream or lean mode, the API emits:

| Event | Description |
|-------|-------------|
| `thought` | Reasoning step / status |
| `token` | Streamed LLM token |
| `tool_call` | Function name + arguments |
| `tool_result` | Tool output |
| `final_answer` | Completed assistant message |
| `error` | Failure |

Example:

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize the auth spec", "use_rag": true}'
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `HERMES_UPSTREAM` | `1` to load vendored engine |
| `HERMES_MODEL_NAME` | Model id for upstream `AIAgent` |
| `HERMES_API_BASE_URL` | OpenAI-compatible base URL |
| `HERMES_API_KEY` | API key |
| `QDRANT_URL` | Qdrant REST endpoint |
| `QDRANT_COLLECTION` | Collection name |
| `NEOMETIS_SPECS_ROOT` | Local specs workspace root |
| `PENPOT_API_URL` | Penpot sidecar |
| `PLANE_API_URL` / `PLANE_API_TOKEN` | Plane.so API |

---

## Upgrade Policy

1. Run `./scripts/vendor-hermes.sh <new-ref>`.
2. Run CI (`pytest` + API smoke test).
3. Check `docs/HERMES_INTEGRATION.md` for new upstream modules referenced by
   `conversation_loop.py` imports — add them to `KEEP_DIRS` / `KEEP_FILES` in the
   vendor script if needed.
4. Never re-introduce CLI/TUI/gateway paths into `upstream/`.

---

## License Compatibility

Both NéoMêtis and Hermes Agent are **MIT licensed**. Vendored files retain Nous
Research copyright headers. NéoMêtis modifications are Copyright (c) Neomnia Studio.
See [LICENSE](../LICENSE).
