param(
    [string]$Python = "python",
    [switch]$InstallPlaywrightBrowsers
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

$LocalTemp = Join-Path $RepoRoot ".tmp"
New-Item -ItemType Directory -Force -Path $LocalTemp | Out-Null
$env:TEMP = $LocalTemp
$env:TMP = $LocalTemp
$env:TMPDIR = $LocalTemp
$env:PIP_CACHE_DIR = Join-Path $LocalTemp "pip-cache"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$BootstrapPath = Join-Path $RepoRoot "scripts\python_bootstrap"
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$BootstrapPath;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $BootstrapPath
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Invoke-Native $Python @("-m", "venv", "--without-pip", ".venv")
}

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
Invoke-Native $VenvPython @("-m", "ensurepip", "--upgrade", "--default-pip")
Invoke-Native $VenvPython @("-m", "pip", "install", "--no-cache-dir", "-r", "requirements.txt")

$SitePackages = & $VenvPython -c "import site; print(site.getsitepackages()[0])"
if ($LASTEXITCODE -ne 0 -or -not $SitePackages) {
    throw "Could not locate the virtual environment site-packages directory."
}
$SourcePath = Join-Path $RepoRoot "src"
Set-Content -LiteralPath (Join-Path $SitePackages "yt_browser_analyzer_local.pth") -Value $SourcePath -Encoding ASCII

if ($InstallPlaywrightBrowsers) {
    Invoke-Native $VenvPython @("-m", "playwright", "install", "chromium")
}

Invoke-Native $VenvPython @(
    "-c",
    "import playwright, yt_browser_analyzer; print('Environment check passed.')"
)

Write-Output "Setup complete."
Write-Output "Python environment: $VenvPython"
Write-Output "Start browser:"
Write-Output "powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_edge_cdp.ps1"
Write-Output "Capture video:"
Write-Output ".\.venv\Scripts\python.exe -m yt_browser_analyzer.cli capture `"https://www.youtube.com/watch?v=VIDEO_ID`" --ensure-browser"
