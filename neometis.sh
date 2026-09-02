#!/usr/bin/env bash
# NéoMêtis — 120-second ready workbench
# Usage: ./neometis.sh [init|run|chat|stop|status|install]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

APP_PORT="${APP_PORT:-8000}"
APP_URL="http://localhost:${APP_PORT}"
COMPOSE=(docker compose)

log() { printf '\n\033[1;36m▸\033[0m %s\n' "$*"; }
warn() { printf '\n\033[1;33m!\033[0m %s\n' "$*"; }
die() { printf '\n\033[1;31m✗\033[0m %s\n' "$*" >&2; exit 1; }

need_docker() {
  command -v docker >/dev/null 2>&1 || die "Docker is required. Install Docker Desktop or Docker Engine first."
  docker info >/dev/null 2>&1 || die "Docker daemon is not running."
}

ensure_workspace() {
  mkdir -p workspace/docs workspace/specs workspace/.neometis
  if [[ ! -f workspace/docs/README.md ]]; then
    cat > workspace/docs/README.md <<'EOF'
# Drop your documents here

Supported: `.md`, `.txt`, `.json`, `.pdf`

Files are auto-indexed into Qdrant when NéoMêtis starts.
EOF
  fi
}

cmd_init() {
  need_docker
  ensure_workspace
  if ! command -v python3 >/dev/null 2>&1; then
    die "python3 is required for interactive init."
  fi
  python3 -m pip install -q httpx 2>/dev/null || pip3 install -q httpx
  python3 scripts/neometis_init.py
  if ! command -v neometis >/dev/null 2>&1; then
    log "Install the global command: ./neometis.sh install"
  fi
}

wait_for_health() {
  log "Waiting for NéoMêtis at ${APP_URL}/health ..."
  for _ in $(seq 1 90); do
    if curl -sf "${APP_URL}/health" >/dev/null 2>&1; then
      log "NéoMêtis is ready."
      return 0
    fi
    sleep 2
  done
  die "Timed out waiting for NéoMêtis. Check: docker compose logs neometis-app"
}

open_browser() {
  local url="$1"
  log "Opening ${url}"
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "$url" || true
  else
    warn "Open your browser manually: ${url}"
  fi
}

load_env() {
  if [[ -f .env ]]; then
    # shellcheck disable=SC1091
    set -a && source .env && set +a
    APP_PORT="${APP_PORT:-8000}"
    APP_URL="http://localhost:${APP_PORT}"
  fi
}

start_stack_detached() {
  need_docker
  ensure_workspace

  if [[ ! -f .env ]]; then
    log "No .env found — starting interactive setup."
    cmd_init
  fi

  load_env

  log "Starting NéoMêtis (Hermes + Qdrant + Chainlit on port ${APP_PORT})..."
  "${COMPOSE[@]}" up --build -d
  wait_for_health
}

cmd_run() {
  start_stack_detached
  open_browser "${APP_URL}"

  log "Drop files into ./workspace/docs/ — they will be auto-indexed."
  log "Press Ctrl+C to stop following logs (containers keep running)."
  "${COMPOSE[@]}" logs -f neometis-app qdrant
}

cmd_stop() {
  need_docker
  "${COMPOSE[@]}" down
  log "Stopped."
}

cmd_status() {
  if curl -sf "${APP_URL}/health" 2>/dev/null; then
    echo ""
  else
    die "NéoMêtis is not responding at ${APP_URL}"
  fi
}

cmd_install_cli() {
  local bin_dir="${NEOMETIS_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
  local target="${bin_dir}/neometis"
  local launcher="${ROOT}/bin/neometis"

  [[ -f "$launcher" ]] || die "Missing launcher: ${launcher}"
  chmod +x "$launcher"
  mkdir -p "$bin_dir"
  ln -sf "$launcher" "$target"

  log "Installed global command: ${target}"
  if [[ ":${PATH}:" != *":${bin_dir}:"* ]]; then
    warn "${bin_dir} is not in your PATH."
    cat <<EOF

Add this line to your shell profile (~/.bashrc, ~/.zshrc):

  export PATH="\${HOME}/.local/bin:\${PATH}"

Then reload: source ~/.bashrc   # or ~/.zshrc
EOF
  else
    log "You can now run: neometis run"
  fi
}

cmd_chat() {
  load_env

  if ! curl -sf "${APP_URL}/health" >/dev/null 2>&1; then
    warn "NéoMêtis API not reachable at ${APP_URL}"
    log "Starting stack (detached)…"
    start_stack_detached
  fi

  python3 -m pip install -q httpx rich 2>/dev/null || pip3 install -q httpx rich
  export NEOMETIS_API_URL="${APP_URL}"
  python3 -m src.cli.chat
}

usage() {
  cat <<EOF
NéoMêtis — Lean AI Workbench

  neometis init       Interactive LLM + .env setup
  neometis run        Setup (if needed), start Docker, open browser
  neometis chat       Terminal chat (Rich TUI → SSE API)
  neometis stop       Stop containers
  neometis status     Health check
  neometis install    Add \`neometis\` to ~/.local/bin (global alias)

Quick start:
  git clone https://github.com/neomnia/neometis.git && cd neometis
  ./neometis.sh install
  neometis run

From anywhere (after install):
  neometis run
  neometis chat
EOF
}

case "${1:-run}" in
  init) cmd_init ;;
  run) cmd_run ;;
  chat) cmd_chat ;;
  stop) cmd_stop ;;
  status) cmd_status ;;
  install|install-cli) cmd_install_cli ;;
  -h|--help|help) usage ;;
  *) die "Unknown command: $1 (try: init|run|chat|stop|status|install)" ;;
esac
