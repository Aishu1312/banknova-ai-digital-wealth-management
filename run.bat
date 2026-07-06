@echo off
echo ==============================================
echo       Starting BankNova AI (Local Dev)
echo ==============================================
echo.

echo [1/2] Starting FastAPI Backend on port 8000...
start /b uvicorn api:app --host 127.0.0.1 --port 8000 --reload

echo Waiting for backend to initialize...
timeout /t 4 /nobreak >nul

echo [2/2] Starting Streamlit Frontend...
streamlit run app.py

echo.
echo Both services are running.
echo Close this window to stop all services.
