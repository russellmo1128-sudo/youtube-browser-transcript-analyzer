param(
    [int]$Port = 9222,
    [string]$StartUrl = "https://www.youtube.com/",
    [string]$ProfileDir = ""
)

$ErrorActionPreference = "Stop"

if (-not $ProfileDir) {
    $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
    $ProfileDir = Join-Path $RepoRoot ".browser-profile\edge-cdp"
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$edge = Get-Command msedge -ErrorAction SilentlyContinue
if (-not $edge) {
    $candidates = @(
        "$env:ProgramFiles (x86)\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $edge = @{ Source = $candidate }
            break
        }
    }
}

if (-not $edge) {
    throw "Microsoft Edge was not found. Install Edge or launch a Chromium browser manually with --remote-debugging-port=$Port."
}

$args = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=$ProfileDir",
    "--no-first-run",
    "--no-default-browser-check",
    $StartUrl
)

Start-Process -FilePath $edge.Source -ArgumentList $args | Out-Null
Write-Output "Started Edge CDP browser."
Write-Output "Port: $Port"
Write-Output "ProfileDir: $ProfileDir"
Write-Output "StartUrl: $StartUrl"
