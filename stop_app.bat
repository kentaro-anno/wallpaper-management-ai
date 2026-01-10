@echo off
setlocal
cd /d %~dp0

echo [Wallpaper Management] Stopping all processes on ports 8000 and 5173...

:: Kill backend
powershell -Command "$p = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"

:: Kill frontend
powershell -Command "$p = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"

echo [Done] Servers stopped.
pause
