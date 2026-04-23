@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo YouTube video capture helper
echo ============================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Local environment was not found. Running first-time setup...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_windows.ps1"
  if errorlevel 1 (
    echo.
    echo Setup failed. Please copy the error above into Codex.
    pause
    exit /b 1
  )
)

echo.
set /p YT_URL=Paste YouTube URL, then press Enter: 

if "%YT_URL%"=="" (
  echo No URL entered.
  pause
  exit /b 1
)

echo.
echo Capturing transcript and public metrics...
echo.

".venv\Scripts\python.exe" -m yt_browser_analyzer.cli capture "%YT_URL%" --ensure-browser

if errorlevel 1 (
  echo.
  echo Capture failed. Check the error above.
  pause
  exit /b 1
)

echo.
echo Capture finished. Locating latest output folder...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$latest = Get-ChildItem -Path 'outputs\youtube-browser-transcript' -Recurse -Filter run.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($latest) { $dir = $latest.Directory.FullName; Write-Host ''; Write-Host 'Latest output folder:'; Write-Host $dir; Write-Host ''; Write-Host 'Paste this into Codex if you want a summary:'; Write-Host ('Read this folder and summarize the video: ' + $dir); Start-Process explorer.exe $dir } else { Write-Host 'No output folder found.' }"

echo.
pause
