@echo off
title DagShield - Full Stack Launcher
echo ========================================================
echo   DagShield - land record conflict screening (synthetic data)
echo ========================================================
echo.

set "PATH=C:\Program Files\nodejs;%PATH%"

echo Starting Backend Server (FastAPI on http://127.0.0.1:8000)...
start "DagShield Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.api.main:app_factory --factory --reload --port 8000"

timeout /t 2 /nobreak >nul

echo Starting Frontend Server (Vite on http://localhost:5173)...
start "DagShield Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are launching!
echo Home:            http://localhost:5173
echo Officer portal:  http://localhost:5173/officer
echo Check land:      http://localhost:5173/check
echo Backend docs:    http://localhost:8000/docs
echo.
pause
