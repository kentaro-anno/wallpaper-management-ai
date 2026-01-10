@echo off
setlocal
cd /d %~dp0

:: Check if .venv exists and activate it if needed
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

:: Delegate to PowerShell for better process management
powershell -ExecutionPolicy Bypass -File start_app.ps1
