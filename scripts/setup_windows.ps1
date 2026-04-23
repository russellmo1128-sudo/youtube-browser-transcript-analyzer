param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    & $Python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium

Write-Output "Setup complete."
Write-Output "Start browser:"
Write-Output "powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_edge_cdp.ps1"
Write-Output "Capture video:"
Write-Output ".\.venv\Scripts\python.exe -m yt_browser_analyzer.cli capture `"https://www.youtube.com/watch?v=VIDEO_ID`" --ensure-browser"
