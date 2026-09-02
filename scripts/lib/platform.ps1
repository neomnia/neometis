# Platform helpers for Windows installer
$script:WindowsVersion = [System.Environment]::OSVersion.Version
$script:WindowsLabel = "Windows $($WindowsVersion.Major).$($WindowsVersion.Minor)"

function Get-WindowsPackageManager {
    if (Get-Command winget -ErrorAction SilentlyContinue) { return "winget" }
    if (Get-Command choco -ErrorAction SilentlyContinue) { return "choco" }
    return ""
}

function Show-SupportedPlatforms {
    Write-Host @"
  Supported platforms:
    • Windows 10 / 11 (PowerShell — this script)
    • Windows + WSL2 (Ubuntu/Debian inside WSL — ./install.sh)
    • Windows + Git Bash (./install.sh)

  Supported Linux (via WSL or native):
    Debian/Ubuntu/Mint, Fedora/RHEL/Rocky, Arch/Manjaro, openSUSE, Alpine
  macOS:
    Intel & Apple Silicon — ./install.sh
"@
}

function Install-WindowsDependencies {
    param([string]$PackageManager)

    Write-Step "Installing dependencies via $PackageManager…"

    switch ($PackageManager) {
        "winget" {
            $packages = @(
                @{ Id = "Git.Git"; Name = "Git" },
                @{ Id = "Python.Python.3.12"; Name = "Python 3.12" },
                @{ Id = "Docker.DockerDesktop"; Name = "Docker Desktop" }
            )
            foreach ($pkg in $packages) {
                Write-Host "  → $($pkg.Name)…"
                winget install --id $pkg.Id -e --accept-source-agreements --accept-package-agreements 2>$null
            }
        }
        "choco" {
            choco install git python docker-desktop -y
        }
        default {
            Write-Warn "No package manager (winget/choco) — install manually:"
            Write-Host "  Git:    https://git-scm.com/download/win"
            Write-Host "  Python: https://www.python.org/downloads/"
            Write-Host "  Docker: https://docs.docker.com/desktop/setup/install/windows-install/"
            return $false
        }
    }
    return $true
}

function Test-WslAvailable {
    return [bool](Get-Command wsl -ErrorAction SilentlyContinue)
}

function Show-WslHint {
    if (Test-WslAvailable) {
        Write-Host "  → WSL2 available — you can also run inside Ubuntu:"
        Write-Host "      wsl"
        Write-Host "      cd ~/neometis && ./install.sh"
    }
}
