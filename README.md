# 🚀 Enterprise AI-Powered Offline OCR System (Farsi/English)

An enterprise-grade, highly performant, completely offline Optical Character Recognition (OCR) system designed for mixed Farsi/English documents and identification cards.

## 🌟 Key Features
- **100% Offline & CPU Optimized:** Runs smoothly on CPU (4GB-8GB RAM) without requiring a GPU.
- **Ultra-Fast Processing:** Optimized image resizing (`max_dimension=600`) and canvas configuration for multi-second execution.
- **Smart Box Sorting:** Custom geometric algorithm (`sort_and_merge_lines`) for strict right-to-left line ordering and Farsi text structure preservation.
- **Interactive Feedback Loop:** Enables users to edit extracted text, saving real corrections in PostgreSQL with real-time **CER** and **WER** metrics calculation.

## 🛠️ Architecture & Tech Stack
- **Backend:** Python 3.12, FastAPI, EasyOCR, SQLAlchemy, PostgreSQL, JiWER, OpenVINO
- **Frontend:** Next.js 14, React, Lucide Icons, Axios

## 🚀 One-Click Execution Guide

### Windows
1. Double-click **`run_win.bat`** in the root directory.
2. Open your browser at `http://localhost:3000`.

### Linux
1. Make the script executable: `chmod +x run_linux.sh`
2. Run the launcher: `./run_linux.sh`
3. Open your browser at `http://localhost:3000`.

## 🗄️ Database Setup (PostgreSQL)
Ensure PostgreSQL is running and database `ocr_db` is created. Update `DATABASE_URL` in `ocr-backend/database.py` with your database credentials.