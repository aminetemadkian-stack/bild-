@echo off
if not exist .venv\Scripts\python.exe (
  echo Please run scripts\setup.ps1 first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
