# ==========================================
# Run Streamlit Frontend (Windows PowerShell)
# ==========================================

Write-Host ">>> Starting Streamlit UI for AI Multi-Agent Travel Planner..." -ForegroundColor Cyan

# 1. Activate Python virtual environment if present
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host ">>> Activating virtual environment: .\venv" -ForegroundColor Green
    & ".\venv\Scripts\Activate.ps1"
} elseif (Test-Path "..\venv\Scripts\Activate.ps1") {
    Write-Host ">>> Activating virtual environment: ..\venv" -ForegroundColor Green
    & "..\venv\Scripts\Activate.ps1"
}

# 2. Launch Streamlit app
Write-Host ">>> Launching Streamlit on http://localhost:8501" -ForegroundColor Cyan
python -m streamlit run frontend/app.py --server.port 8501

