@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo YouTube Browser Transcript Analyzer - first-time setup
echo =====================================================
echo.
echo This will create a local Python environment and install dependencies.
echo It may take several minutes the first time.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_windows.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed. Please copy the error above into Codex.
  echo.
  pause
  exit /b 1
)

echo.
echo Setup finished.
echo.
echo Next:
echo 1. Open this folder in Codex.
echo 2. Ask: Summarize this YouTube video: https://www.youtube.com/watch?v=VIDEO_ID
echo.
echo Optional no-Codex fallback:
echo Double-click ANALYZE_VIDEO.bat and paste a YouTube URL.
echo.
pause
