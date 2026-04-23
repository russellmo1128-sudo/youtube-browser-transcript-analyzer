@echo off
chcp 65001 >nul
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_edge_cdp.ps1"

echo.
echo Fixed Edge CDP browser has been started.
echo If one was already running, it was reused.
echo Keep that browser open while Codex analyzes YouTube videos.
echo.
pause
