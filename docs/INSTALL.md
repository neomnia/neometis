# Installation — all platforms & distributions

NéoMêtis ships two installers that cover **Linux**, **macOS**, and **Windows**.

## Quick install

| Platform | Command |
|----------|---------|
| **Linux / macOS / Git Bash** | `./install.sh` |
| **Windows 10 / 11** | `.\install.ps1` |

```bash
git clone https://github.com/neomnia/neometis.git
cd neometis
./install.sh        # or .\install.ps1 on Windows
neometis run
```

## Supported distributions

### Linux (native or WSL2)

| Family | Examples | Package manager | Installer |
|--------|----------|-----------------|-----------|
| **Debian** | Debian, Ubuntu, Mint, Pop!\_OS, Kali, Raspberry Pi OS | `apt` | `./install.sh` |
| **Red Hat** | Fedora, Nobara | `dnf` | `./install.sh` |
| **Enterprise Linux** | RHEL, CentOS, Rocky, Alma, Amazon Linux, Azure Linux | `dnf` / `yum` | `./install.sh` |
| **Arch** | Arch Linux, Manjaro, EndeavourOS, Garuda | `pacman` | `./install.sh` |
| **SUSE** | openSUSE Tumbleweed / Leap, SLE | `zypper` | `./install.sh` |
| **Alpine** | Alpine Linux (containers, edge) | `apk` | `./install.sh` |

Auto-install missing dependencies:

```bash
./install.sh --install-deps
```

This uses your native package manager (+ Docker official script when needed).

### macOS

| Variant | Installer |
|---------|-----------|
| Intel Mac | `./install.sh` |
| Apple Silicon (M1/M2/M3/M4) | `./install.sh` |

With Homebrew:

```bash
./install.sh --install-deps   # brew install git python@3.12
brew install --cask docker    # Docker Desktop (manual step)
```

### Windows

| Variant | Installer |
|---------|-----------|
| Windows 10 | `.\install.ps1` |
| Windows 11 | `.\install.ps1` |
| Windows + WSL2 (Ubuntu) | `./install.sh` inside WSL |
| Windows + Git Bash | `./install.sh` |

Auto-install via winget:

```powershell
.\install.ps1 -InstallDeps
```

Installs Git, Python 3.12, and Docker Desktop when winget is available.

## Installer options

### Linux / macOS (`install.sh`)

| Flag | Description |
|------|-------------|
| *(default)* | CLI + PATH + prerequisite check |
| `--install-deps` | Install git, python, docker via apt/dnf/pacman/brew |
| `--cli-only` | Install `neometis` command only |
| `--check-only` | Verify Docker, Python, Git |
| `--skip-path` | Do not modify shell profile |

### Windows (`install.ps1`)

| Flag | Description |
|------|-------------|
| *(default)* | CLI + PATH + prerequisite check |
| `-InstallDeps` | Install via winget/choco |
| `-CliOnly` | Install `neometis` command only |
| `-CheckOnly` | Verify prerequisites |
| `-SkipPath` | Do not modify user PATH |

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| **Docker** | Latest Desktop / Engine | Run Hermes + Qdrant + Chainlit |
| **Python** | 3.12+ | `./neometis.sh init`, terminal chat |
| **Git** | Any recent | Clone & updates |

## After install

```bash
neometis run      # start workbench
neometis chat     # terminal TUI
neometis init     # configure LLM
neometis stop
neometis status
```

## Troubleshooting

**Docker permission denied (Linux)**

```bash
sudo usermod -aG docker $USER
newgrp docker
```

**`neometis` command not found**

```bash
source ~/.bashrc   # or ~/.zshrc
# or re-run ./install.sh
```

**Windows: bash not found**

Install [Git for Windows](https://git-scm.com/download/win) or run `.\install.ps1 -InstallDeps`.

See also [QUICKSTART.md](QUICKSTART.md) and [DEPLOYMENT.md](DEPLOYMENT.md).
