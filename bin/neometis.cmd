@echo off
setlocal
set "ROOT=%~dp0.."
set "ROOT=%ROOT:~0,-1%"

where bash >nul 2>&1
if %ERRORLEVEL%==0 (
  bash "%ROOT%/neometis.sh" %*
  exit /b %ERRORLEVEL%
)

echo neometis: Git Bash is required on Windows.
echo Install Git for Windows: https://git-scm.com/download/win
exit /b 1
