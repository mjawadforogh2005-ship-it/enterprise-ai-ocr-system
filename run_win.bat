@echo off
title AI Offline OCR System Launcher
echo ===================================================
echo   Starting Enterprise AI Offline OCR System...
echo ===================================================

echo [1/2] Launching FastAPI Backend Server...
start "OCR Backend" cmd /k "cd ocr-backend && .\venv\Scripts\python.exe main.py"

echo [2/2] Launching Next.js Frontend Server...
start "OCR Frontend" cmd /k "cd ocr-frontend && npm run dev"

echo ===================================================
echo   System launched successfully!
echo   Open your browser at: http://localhost:3000
echo ===================================================