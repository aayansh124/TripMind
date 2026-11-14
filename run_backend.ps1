# ==========================================
# Run FastAPI Backend Server (Windows PowerShell)
# ==========================================

Write-Host ">>> Starting AI Multi-Agent Travel Planner Backend..." -ForegroundColor Cyan

# 1. Activate Python virtual environment if present
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host ">>> Activating virtual environment: .\venv" -ForegroundColor Green
    & ".\venv\Scripts\Activate.ps1"
} elseif (Test-Path "..\venv\Scripts\Activate.ps1") {
    Write-Host ">>> Activating virtual environment: ..\venv" -ForegroundColor Green
    & "..\venv\Scripts\Activate.ps1"
}

# 2. Check environment configuration
if (-not (Test-Path ".env")) {
    Write-Host ">>> [Notice] .env file not detected. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 3. Launch Uvicorn server with auto-reload
Write-Host ">>> Launching Uvicorn on http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)" -ForegroundColor Cyan
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

