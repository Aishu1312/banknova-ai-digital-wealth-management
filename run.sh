#!/bin/bash
echo "=============================================="
echo "      Starting BankNova AI (Local Dev)"
echo "=============================================="
echo ""

echo "[1/3] Installing/verifying dependencies..."
python3 -m pip install -r requirements.txt > /dev/null

echo "[2/3] Starting FastAPI Backend on port 8000..."
python3 -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "Waiting for backend to initialize..."
sleep 5

echo "[3/3] Starting Streamlit Frontend..."
streamlit run app.py

# Cleanup backend when frontend stops
kill $BACKEND_PID
