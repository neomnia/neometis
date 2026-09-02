#!/usr/bin/env bash
# NéoMêtis cross-platform installer
#
# Supported:
#   Linux  — Debian/Ubuntu/Mint, Fedora/RHEL/Rocky, Arch/Manjaro, openSUSE, Alpine, …
#   macOS  — Intel & Apple Silicon (Homebrew)
#   Windows — PowerShell script (install.ps1) + Git Bash
#
# Usage:
#   ./install.sh
#   ./install.sh --install-deps   # apt/dnf/pacman/brew + Docker
#   ./install.sh --check-only
#   ./install.sh --cli-only
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=lib/platform.sh
source "${ROOT}/scripts/lib/platform.sh"

CLI_ONLY=0
CHECK_ONLY=0
SKIP_PATH=0
INSTALL_DEPS=0
BIN_DIR="${NEOMETIS_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"

log() { printf '\n\033[1;36m▸\033[0m %s\n' "$*"; }
warn() { printf '\n\033[1;33m!\033[0m %s\n' "$*"; }
ok() { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
die() { printf '\n\033[1;31m✗\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
NéoMêtis installer — all major platforms

  ./install.sh                 Full install (CLI + PATH + checks)
  ./install.sh --install-deps  Install git, python, docker via native package manager
  ./install.sh --cli-only      Install global neometis command only
  ./install.sh --check-only    Verify prerequisites
  ./install.sh --help

Platforms:
  Linux    Debian/Ubuntu/Mint, Fedora/RHEL/Rocky, Arch, openSUSE, Alpine, …
  macOS    Intel & Apple Silicon
  Windows  .\\install.ps1  (PowerShell)

Environment:
  NEOMETIS_BIN_DIR    Target bin directory (default: ~/.local/bin)
  NEOMETIS_SKIP_PATH  Do not modify shell profile
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cli-only) CLI_ONLY=1 ;;
    --check-only) CHECK_ONLY=1 ;;
    --skip-path) SKIP_PATH=1 ;;
    --install-deps) INSTALL_DEPS=1 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

detect_shell_profile() {
  if [[ -n "${ZSH_VERSION:-}" ]] || [[ "${SHELL:-}" == *zsh* ]]; then
    PROFILE="${ZDOTDIR:-$HOME}/.zshrc"
  elif [[ "${SHELL:-}" == *fish* ]] && [[ -d "$HOME/.config/fish" ]]; then
    PROFILE="$HOME/.config/fish/config.fish"
    PROFILE_KIND="fish"
  elif [[ -f "$HOME/.bashrc" ]]; then
    PROFILE="$HOME/.bashrc"
  elif [[ -f "$HOME/.profile" ]]; then
    PROFILE="$HOME/.profile"
  else
    PROFILE="$HOME/.profile"
  fi
}

check_prerequisites() {
  local missing=0

  if command -v git >/dev/null 2>&1; then
    ok "git $(git --version | awk '{print $3}')"
  else
    warn "git not found"
    print_git_hint
    missing=1
  fi

  if command -v python3 >/dev/null 2>&1; then
    ok "python3 $(python3 --version 2>&1 | awk '{print $2}')"
  else
    warn "python3 not found"
    print_python_hint
    missing=1
  fi

  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    ok "docker $(docker --version | awk '{print $3}' | tr -d ',')"
  else
    warn "Docker is not running or not installed"
    print_docker_hint
    missing=1
  fi

  return "$missing"
}

install_cli() {
  local launcher="${ROOT}/bin/neometis"
  local target="${BIN_DIR}/neometis"

  [[ -f "$launcher" ]] || die "Missing launcher: ${launcher}"
  chmod +x "$launcher"
  mkdir -p "$BIN_DIR"
  ln -sf "$launcher" "$target"
  ok "Global command: ${target} → ${launcher}"
}

ensure_path_in_profile() {
  [[ "$SKIP_PATH" -eq 1 ]] && return 0
  [[ ":${PATH}:" == *":${BIN_DIR}:"* ]] && return 0

  detect_shell_profile
  local marker="# Added by NéoMêtis installer"

  if [[ -f "$PROFILE" ]] && grep -Fq "$marker" "$PROFILE" 2>/dev/null; then
    ok "PATH already configured in ${PROFILE}"
    return 0
  fi

  if [[ "${PROFILE_KIND:-}" == "fish" ]]; then
    {
      echo ""
      echo "$marker"
      echo "fish_add_path ${BIN_DIR}"
    } >> "$PROFILE"
  else
    {
      echo ""
      echo "$marker"
      echo "export PATH=\"${BIN_DIR}:\${PATH}\""
    } >> "$PROFILE"
  fi

  ok "Added ${BIN_DIR} to PATH in ${PROFILE}"
  warn "Reload your shell: source \"${PROFILE}\""
}

install_python_extras() {
  if ! command -v python3 >/dev/null 2>&1; then
    return 0
  fi
  log "Installing Python CLI dependencies (httpx, rich)…"
  python3 -m pip install -q --user httpx rich 2>/dev/null \
    || pip3 install -q --user httpx rich 2>/dev/null \
    || warn "Could not install Python extras — run later: pip install httpx rich"
}

print_next_steps() {
  cat <<EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NéoMêtis is ready on ${PLATFORM_LABEL}

  From any terminal:
    neometis run      Start workbench (browser + Docker)
    neometis chat     Terminal chat (Rich TUI)
    neometis init     Configure LLM provider

  Repo: ${ROOT}
  Docs: ${ROOT}/workspace/docs/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
}

main() {
  detect_platform
  log "NéoMêtis installer — ${PLATFORM_LABEL}"
  if [[ "$OS" == "linux" && "$DISTRO_ID" != "unknown" ]]; then
    ok "Detected: ${DISTRO_ID} (${PKG_MGR:-unknown pkg mgr})"
  fi

  if [[ "$INSTALL_DEPS" -eq 1 ]]; then
    install_system_dependencies || warn "Some dependencies could not be installed automatically."
  fi

  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    supported_distro_hint
    check_prerequisites || die "Some prerequisites are missing. Try: ./install.sh --install-deps"
    ok "All prerequisites look good."
    exit 0
  fi

  install_cli

  if [[ "$CLI_ONLY" -eq 0 ]]; then
    ensure_path_in_profile
    supported_distro_hint
    check_prerequisites || warn "Fix prerequisites above, or run: ./install.sh --install-deps"
    install_python_extras
    mkdir -p "${ROOT}/workspace/docs" "${ROOT}/workspace/specs" "${ROOT}/workspace/.neometis"
    print_next_steps
  elif [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
    warn "${BIN_DIR} is not in your PATH."
    echo "  export PATH=\"${BIN_DIR}:\${PATH}\""
  else
    ok "Run: neometis run"
  fi
}

main
