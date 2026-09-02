# Windows PowerShell wrapper — delegates to neometis.sh via Git Bash when available.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$Root = Split-Path $PSScriptRoot -Parent
$Script = Join-Path $Root "neometis.sh"

if (Get-Command bash -ErrorAction SilentlyContinue) {
    & bash $Script @Args
    exit $LASTEXITCODE
}

Write-Error "Git Bash (bash.exe) is required. Install Git for Windows: https://git-scm.com/download/win"
exit 1
