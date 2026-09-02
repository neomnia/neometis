#!/usr/bin/env bash
# Vendor a lean subset of NousResearch/hermes-agent into src/core/hermes/upstream/.
#
# Usage:
#   ./scripts/vendor-hermes.sh [commit-ish]
#
# Default upstream: https://github.com/NousResearch/hermes-agent @ main
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM="${HERMES_UPSTREAM_REPO:-https://github.com/NousResearch/hermes-agent.git}"
REF="${1:-main}"
DEST="$ROOT/src/core/hermes/upstream"
TMP="$(mktemp -d)"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "==> Cloning Hermes Agent ($REF) ..."
git clone --depth 1 --branch "$REF" "$UPSTREAM" "$TMP/hermes-agent" 2>/dev/null \
  || git clone --depth 1 "$UPSTREAM" "$TMP/hermes-agent"

echo "==> Cleaning destination $DEST"
rm -rf "$DEST"
mkdir -p "$DEST"

# --- KEEP: core ReAct / tool-use engine ---
KEEP_DIRS=(
  agent
  tools
  providers
)
KEEP_FILES=(
  run_agent.py
  model_tools.py
  toolsets.py
  hermes_constants.py
  hermes_logging.py
  utils.py
)

for dir in "${KEEP_DIRS[@]}"; do
  if [[ -d "$TMP/hermes-agent/$dir" ]]; then
    rsync -a --exclude '__pycache__' "$TMP/hermes-agent/$dir" "$DEST/"
  fi
done

for file in "${KEEP_FILES[@]}"; do
  if [[ -f "$TMP/hermes-agent/$file" ]]; then
    cp "$TMP/hermes-agent/$file" "$DEST/"
  fi
done

# --- STRIP: CLI / TUI / gateway / messaging (handled by NéoMêtis API + Next.js UI) ---
# These paths are intentionally NOT copied:
#   cli.py, hermes_cli/, tui_gateway/, ui-tui/, gateway/, web/, website/
#   hermes_state*.py (SQLite session store — replaced by Qdrant Advanced RAG)
#   agent/memory_manager.py, agent/memory_provider.py (replaced by src/memory/rag/)

cat > "$DEST/.vendored" <<EOF
source=$UPSTREAM
ref=$REF
vendored_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
stripped=cli,tui,gateway,hermes_state,memory_manager
EOF

echo "==> Done. Set HERMES_UPSTREAM=1 and restart the core API."
echo "    See docs/HERMES_INTEGRATION.md for wiring details."
