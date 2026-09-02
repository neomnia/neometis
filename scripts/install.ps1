# NéoMêtis installer for Windows 10 / 11 (PowerShell 5.1+ / PowerShell Core)
#
# Usage:
#   .\install.ps1
#   .\install.ps1 -InstallDeps    # winget/choco: Git, Python, Docker Desktop
#   .\install.ps1 -CheckOnly
param(
    [switch]$CliOnly,
    [switch]$CheckOnly,
    [switch]$SkipPath,
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Lib = Join-Path $PSScriptRoot "lib\platform.ps1"
if (Test-Path $Lib) { . $Lib }

$BinDir = if ($env:NEOMETIS_BIN_DIR) { $env:NEOMETIS_BIN_DIR } else { Join-Path $env:USERPROFILE ".local\bin" }
$LauncherCmd = Join-Path $Root "bin\neometis.cmd"
$Target = Join-Path $BinDir "neometis.cmd"

function Write-Step($Message) { Write-Host "`n▸ $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "`n! $Message" -ForegroundColor Yellow }
function Write-Ok($Message) { Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Fail($Message) { Write-Host "`n✗ $Message" -ForegroundColor Red; exit 1 }

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-DockerRunning {
    if (-not (Test-Command "docker")) { return $false }
    try {
        docker info *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-Prerequisites {
    $missing = $false

    if (Test-Command "git") {
        Write-Ok "git $(git --version)"
    } else {
        Write-Warn "git not found"
        Write-Host "  → winget install Git.Git"
        $missing = $true
    }

    if (Test-Command "python") {
        Write-Ok "python $(python --version 2>&1)"
    } elseif (Test-Command "python3") {
        Write-Ok "python3 $(python3 --version 2>&1)"
    } else {
        Write-Warn "Python not found"
        Write-Host "  → winget install Python.Python.3.12"
        $missing = $true
    }

    if (Test-DockerRunning) {
        Write-Ok "docker $(docker --version)"
    } else {
        Write-Warn "Docker Desktop is not running or not installed"
        Write-Host "  → winget install Docker.DockerDesktop"
        Write-Host "  → WSL2 backend: https://docs.docker.com/desktop/wsl/"
        Show-WslHint
        $missing = $true
    }

    if (-not (Test-Command "bash")) {
        Write-Warn "Git Bash not found — required for neometis CLI"
        Write-Host "  → winget install Git.Git"
    } else {
        Write-Ok "bash (Git Bash)"
    }

    return -not $missing
}

function Install-Cli {
    if (-not (Test-Path $LauncherCmd)) {
        Write-Fail "Missing launcher: $LauncherCmd"
    }
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    Copy-Item -Force $LauncherCmd $Target
    Write-Ok "Global command: $Target"
}

function Ensure-Path {
    if ($SkipPath) { return }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -split ';' | Where-Object { $_ -eq $BinDir }) {
        Write-Ok "PATH already contains $BinDir"
        return
    }

    $newPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $BinDir } else { "$BinDir;$userPath" }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$BinDir;$env:Path"
    Write-Ok "Added $BinDir to user PATH (restart terminal if needed)"
}

function Install-PythonExtras {
    if (Test-Command "python") {
        Write-Step "Installing Python CLI dependencies (httpx, rich)…"
        python -m pip install -q --user httpx rich 2>$null
    } elseif (Test-Command "python3") {
        python3 -m pip install -q --user httpx rich 2>$null
    }
}

function Show-NextSteps {
    Write-Host @"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NéoMêtis is ready on $WindowsLabel

  Open a new PowerShell or Git Bash window, then:
    neometis run      Start workbench (browser + Docker)
    neometis chat     Terminal chat (Rich TUI)
    neometis init     Configure LLM provider

  Repo: $Root
  Docs: $(Join-Path $Root 'workspace\docs')
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"@ -ForegroundColor White
}

Write-Step "NéoMêtis installer — $WindowsLabel"
Show-SupportedPlatforms

if ($InstallDeps) {
    $pm = Get-WindowsPackageManager
    if ($pm) {
        Install-WindowsDependencies -PackageManager $pm
    } else {
        Write-Warn "Install winget (App Installer) from Microsoft Store, then re-run."
    }
}

if ($CheckOnly) {
    if (Test-Prerequisites) {
        Write-Ok "All prerequisites look good."
    } else {
        Write-Fail "Some prerequisites are missing. Try: .\install.ps1 -InstallDeps"
    }
    exit 0
}

Install-Cli

if (-not $CliOnly) {
    Ensure-Path
    if (-not (Test-Prerequisites)) {
        Write-Warn "Fix prerequisites above, or run: .\install.ps1 -InstallDeps"
    }
    Install-PythonExtras
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "workspace\docs") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "workspace\specs") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "workspace\.neometis") | Out-Null
    Show-NextSteps
} else {
    Write-Ok "Run: neometis run"
}
