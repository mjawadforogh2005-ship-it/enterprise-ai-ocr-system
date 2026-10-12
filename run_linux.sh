#!/bin/bash
echo "==================================================="
echo "  Starting Enterprise AI Offline OCR System..."
echo "==================================================="

echo "[1/2] Starting FastAPI Backend..."
cd ocr-backend && ./venv/bin/python main.py &

echo "[2/2] Starting Next.js Frontend..."
cd ../ocr-frontend && npm run dev &

echo "==================================================="
echo "  System is running at: http://localhost:3000"
echo "==================================================="