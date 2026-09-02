# NéoMêtis — 120-Second Quick Start

## The promise

```bash
git clone https://github.com/neomnia/neometis.git
cd neometis
./install.sh
neometis run
```

**Windows:**

```powershell
git clone https://github.com/neomnia/neometis.git
cd neometis
.\install.ps1
neometis run
```

1. Installer checks Docker + Python and configures PATH
2. No `.env`? → interactive LLM setup (OpenAI / Anthropic / Ollama / Groq)
3. Docker Compose starts Hermes + Qdrant + Chainlit on **port 8000**
4. Browser opens automatically

## Commands

| Command | Action |
|---------|--------|
| `neometis init` | Interactive `.env` setup + LLM connection test |
| `neometis run` | Init if needed, start stack, open browser |
| `neometis chat` | Terminal chat (Rich TUI, no browser) |
| `neometis stop` | Stop containers |
| `neometis status` | Health check |
| `./install.sh` | Full install (Linux / macOS / Git Bash) |
| `.\install.ps1` | Full install (Windows PowerShell) |

### Prerequisites by platform

See **[docs/INSTALL.md](docs/INSTALL.md)** for the full matrix (all Linux distros, macOS, Windows).

| Platform | Distros / variants | Install |
|----------|-------------------|---------|
| **Linux** | Debian, Ubuntu, Mint, Fedora, RHEL, Rocky, Arch, openSUSE, Alpine, … | `./install.sh` |
| **macOS** | Intel & Apple Silicon | `./install.sh` |
| **Windows** | Windows 10 / 11, WSL2, Git Bash | `.\install.ps1` |

Auto-install system packages:

```bash
./install.sh --install-deps          # Linux / macOS
```

```powershell
.\install.ps1 -InstallDeps           # Windows (winget)
```

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
