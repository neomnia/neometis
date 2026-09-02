#!/usr/bin/env bash
# Platform detection and distro-specific dependency hints for NéoMêtis.
# Sourced by scripts/install.sh — do not execute directly.

detect_platform() {
  OS="unknown"
  DISTRO_ID="unknown"
  DISTRO_NAME="Unknown"
  DISTRO_VERSION=""
  PKG_MGR=""
  PLATFORM_LABEL="unknown"

  case "$(uname -s)" in
    Linux)
      OS="linux"
      if [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        DISTRO_ID="${ID:-unknown}"
        DISTRO_NAME="${PRETTY_NAME:-${NAME:-Linux}}"
        DISTRO_VERSION="${VERSION_ID:-}"
      fi
      PKG_MGR="$(detect_linux_pkg_mgr "$DISTRO_ID" "${ID_LIKE:-}")"
      PLATFORM_LABEL="${DISTRO_NAME}"
      ;;
    Darwin)
      OS="macos"
      DISTRO_ID="macos"
      DISTRO_NAME="macOS $(sw_vers -productVersion 2>/dev/null || echo "")"
      PKG_MGR="brew"
      PLATFORM_LABEL="${DISTRO_NAME}"
      ;;
    MINGW*|MSYS*|CYGWIN*)
      OS="windows-gitbash"
      DISTRO_ID="windows"
      DISTRO_NAME="Windows (Git Bash)"
      PKG_MGR="winget"
      PLATFORM_LABEL="${DISTRO_NAME}"
      ;;
    *)
      PLATFORM_LABEL="$(uname -s)"
      ;;
  esac
}

detect_linux_pkg_mgr() {
  local id="$1"
  local id_like="$2"

  case "$id" in
    ubuntu|debian|linuxmint|pop|elementary|zorin|kali|raspbian|neon)
      echo "apt"; return ;;
    fedora|nobara)
      echo "dnf"; return ;;
    rhel|centos|rocky|almalinux|ol|amzn|azurelinux)
      if command -v dnf >/dev/null 2>&1; then echo "dnf"; else echo "yum"; fi
      return ;;
    arch|manjaro|endeavouros|garuda|cachyos)
      echo "pacman"; return ;;
    opensuse*|sles|sled)
      echo "zypper"; return ;;
    alpine)
      echo "apk"; return ;;
    void)
      echo "xbps"; return ;;
  esac

  case "$id_like" in
    *debian*|*ubuntu*) echo "apt" ;;
    *fedora*|*rhel*) command -v dnf >/dev/null 2>&1 && echo "dnf" || echo "yum" ;;
    *arch*) echo "pacman" ;;
    *suse*) echo "zypper" ;;
    *) echo "" ;;
  esac
}

supported_distro_hint() {
  case "$OS" in
    linux)
      cat <<EOF
  Supported Linux families:
    • Debian / Ubuntu / Mint / Pop!_OS / Kali     (apt)
    • Fedora / Nobara                             (dnf)
    • RHEL / CentOS / Rocky / Alma / Amazon Linux (dnf/yum)
    • Arch / Manjaro / EndeavourOS                (pacman)
    • openSUSE / SLE                              (zypper)
    • Alpine                                      (apk)
EOF
      ;;
    macos)
      echo "  • macOS (Intel & Apple Silicon) — Homebrew recommended"
      ;;
    windows-gitbash)
      echo "  • Windows 10 / 11 — PowerShell: .\\install.ps1"
      ;;
  esac
}

print_docker_hint() {
  case "$OS" in
    macos)
      echo "  → macOS: brew install --cask docker"
      echo "  → Or Docker Desktop: https://docs.docker.com/desktop/setup/install/mac-install/"
      ;;
    linux)
      case "$PKG_MGR" in
        apt)
          echo "  → Ubuntu/Debian: sudo apt install docker.io docker-compose-plugin"
          echo "  → Or official script: curl -fsSL https://get.docker.com | sh"
          ;;
        dnf|yum)
          echo "  → Fedora/RHEL: sudo $PKG_MGR install docker docker-compose-plugin"
          echo "  → Or official script: curl -fsSL https://get.docker.com | sh"
          ;;
        pacman)
          echo "  → Arch: sudo pacman -S docker docker-compose"
          ;;
        zypper)
          echo "  → openSUSE: sudo zypper install docker docker-compose"
          ;;
        apk)
          echo "  → Alpine: sudo apk add docker docker-cli-compose"
          ;;
        *)
          echo "  → Official script: curl -fsSL https://get.docker.com | sh"
          ;;
      esac
      echo "  → Then: sudo usermod -aG docker \$USER && newgrp docker"
      ;;
    windows-gitbash)
      echo "  → Windows: .\\install.ps1  (or winget install Docker.DockerDesktop)"
      echo "  → WSL2 backend: https://docs.docker.com/desktop/wsl/"
      ;;
  esac
}

print_python_hint() {
  case "$OS" in
    macos)
      echo "  → macOS: brew install python@3.12"
      ;;
    linux)
      case "$PKG_MGR" in
        apt) echo "  → sudo apt install python3 python3-pip python3-venv" ;;
        dnf|yum) echo "  → sudo $PKG_MGR install python3 python3-pip" ;;
        pacman) echo "  → sudo pacman -S python python-pip" ;;
        zypper) echo "  → sudo zypper install python3 python3-pip" ;;
        apk) echo "  → sudo apk add python3 py3-pip" ;;
        *) echo "  → Install Python 3.12+ from your package manager" ;;
      esac
      ;;
    windows-gitbash)
      echo "  → Windows: winget install Python.Python.3.12"
      ;;
  esac
}

print_git_hint() {
  case "$OS" in
    macos) echo "  → macOS: brew install git" ;;
    linux)
      case "$PKG_MGR" in
        apt) echo "  → sudo apt install git" ;;
        dnf|yum) echo "  → sudo $PKG_MGR install git" ;;
        pacman) echo "  → sudo pacman -S git" ;;
        zypper) echo "  → sudo zypper install git" ;;
        apk) echo "  → sudo apk add git" ;;
        *) echo "  → Install git from your package manager" ;;
      esac
      ;;
    windows-gitbash)
      echo "  → Windows: winget install Git.Git"
      ;;
  esac
}

install_system_dependencies() {
  case "$OS" in
    linux) install_linux_deps ;;
    macos) install_macos_deps ;;
    windows-gitbash)
      warn "On Windows, run .\\install.ps1 -InstallDeps from PowerShell instead."
      return 1
      ;;
    *)
      warn "Automatic dependency install not supported on this platform."
      return 1
      ;;
  esac
}

install_linux_deps() {
  log "Installing system dependencies via ${PKG_MGR:-generic} (${DISTRO_ID})…"

  case "$PKG_MGR" in
    apt)
      sudo apt-get update -y
      sudo apt-get install -y git curl python3 python3-pip python3-venv
      if ! command -v docker >/dev/null 2>&1; then
        if command -v apt-get >/dev/null 2>&1 && apt-cache show docker.io >/dev/null 2>&1; then
          sudo apt-get install -y docker.io docker-compose-plugin || true
        else
          curl -fsSL https://get.docker.com | sh
        fi
      fi
      ;;
    dnf)
      sudo dnf install -y git curl python3 python3-pip
      if ! command -v docker >/dev/null 2>&1; then
        sudo dnf install -y docker docker-compose-plugin 2>/dev/null || curl -fsSL https://get.docker.com | sh
      fi
      ;;
    yum)
      sudo yum install -y git curl python3 python3-pip
      if ! command -v docker >/dev/null 2>&1; then
        curl -fsSL https://get.docker.com | sh
      fi
      ;;
    pacman)
      sudo pacman -Sy --noconfirm git curl python python-pip docker docker-compose
      ;;
    zypper)
      sudo zypper --non-interactive install git curl python3 python3-pip docker docker-compose
      ;;
    apk)
      sudo apk add git curl python3 py3-pip docker docker-cli-compose
      ;;
    *)
      warn "Unknown package manager — using Docker official script."
      curl -fsSL https://get.docker.com | sh
      ;;
  esac

  if command -v docker >/dev/null 2>&1; then
    sudo usermod -aG docker "${USER}" 2>/dev/null || true
    ok "Docker installed — you may need to log out/in for group membership."
  fi
}

install_macos_deps() {
  if ! command -v brew >/dev/null 2>&1; then
    warn "Homebrew not found — install from https://brew.sh"
    return 1
  fi
  brew install git python@3.12
  if ! command -v docker >/dev/null 2>&1; then
    warn "Install Docker Desktop: brew install --cask docker"
  fi
}
