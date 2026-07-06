@echo off
echo ==============================================
echo       Starting BankNova AI (Local Dev)
echo ==============================================
echo.

echo [1/3] Installing/verifying dependencies...
python -m pip install -r requirements.txt >nul

echo [2/3] Starting FastAPI Backend on port 8000...
:: Opens the backend in a new visible window so you can see if it crashes
start "FastAPI Backend" cmd /k "python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo [3/3] Starting Streamlit Frontend...
streamlit run app.py

echo.
echo Both services are running.
echo Close both windows to stop all services.
