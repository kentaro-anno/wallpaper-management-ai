$ErrorActionPreference = "SilentlyContinue"

function Stop-All {
    Write-Host "`n[Wallpaper Management] Stopping servers..." -ForegroundColor Yellow
    if ($backend) { Stop-Process -Id $backend.Id -Force }
    if ($frontend) { Stop-Process -Id $frontend.Id -Force }
    
    # Double check ports
    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
    Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
    Write-Host "[Done] All processes stopped." -ForegroundColor Green
}

# Cleanup first
Write-Host "[Wallpaper Management] Cleaning up ports..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

Write-Host "[Wallpaper Management] Starting servers..." -ForegroundColor Cyan
Write-Host "NOTE: Press Ctrl+C once to stop everything." -ForegroundColor Gray

# Start Backend
Write-Host "Starting backend..." -ForegroundColor Gray
$backend = Start-Process python -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --log-level warning" -NoNewWindow -PassThru

# Wait a moment and check if backend is still running
Start-Sleep -Seconds 2
if ($backend.HasExited) {
    Write-Host "ERROR: Backend failed to start. Check if .env is set or port 8000 is in use." -ForegroundColor Red
    Stop-All
    exit 1
}

# Start Frontend
Write-Host "Starting frontend..." -ForegroundColor Gray
cd frontend
# Use 'cmd /c' to ensure npm runs correctly on Windows
$frontend = Start-Process cmd -ArgumentList "/c npm run dev -- --host --port 5173 --open" -NoNewWindow -PassThru
cd ..

Write-Host "`nWaiting for servers to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Start-Process "http://localhost:5173"

try {
    # Keep the script alive while processes are running
    while ($backend.HasExited -eq $false -or $frontend.HasExited -eq $false) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Stop-All
}
