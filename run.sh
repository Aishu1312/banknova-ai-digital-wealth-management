#!/bin/bash
echo "=============================================="
echo "      Starting BankNova AI (Local Dev)"
echo "=============================================="
echo ""

echo "[1/2] Starting FastAPI Backend on port 8000..."
uvicorn api:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "Waiting for backend to initialize..."
sleep 3

echo "[2/2] Starting Streamlit Frontend..."
streamlit run app.py

# Cleanup backend when frontend stops
kill $BACKEND_PID
