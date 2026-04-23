param(
    [int]$Port = 9222,
    [string]$StartUrl = "https://www.youtube.com/",
    [string]$ProfileDir = "",
    [switch]$ForceNew
)

$ErrorActionPreference = "Stop"

if (-not $ProfileDir) {
    $BaseDir = Join-Path $env:LOCALAPPDATA "youtube-browser-transcript-analyzer"
    $ProfileDir = Join-Path $BaseDir "edge-cdp-profile"
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$versionUrl = "http://127.0.0.1:$Port/json/version"
if ($ForceNew) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        foreach ($connection in $connections) {
            if ($connection.OwningProcess) {
                Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Seconds 2
    } catch {
        Write-Output "ForceNew requested, but no existing listener could be stopped on port $Port."
    }
}

try {
    if (-not $ForceNew) {
        $existing = Invoke-RestMethod -Uri $versionUrl -TimeoutSec 2
        if ($existing) {
        Write-Output "Reusing existing CDP browser."
        Write-Output "Port: $Port"
        Write-Output "ProfileDir: $ProfileDir"
        Write-Output "Browser: $($existing.Browser)"
        exit 0
        }
    }
} catch {
    # No active browser on this port. Start one below.
}

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
    "--disable-sync",
    "--disable-features=msEdgeSignInCta,msEdgeOnRampFRE",
    $StartUrl
)

Start-Process -FilePath $edge.Source -ArgumentList $args | Out-Null
Write-Output "Started Edge CDP browser."
Write-Output "Port: $Port"
Write-Output "ProfileDir: $ProfileDir"
Write-Output "StartUrl: $StartUrl"
