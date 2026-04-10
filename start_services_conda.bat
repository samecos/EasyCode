@echo off

echo ========================================
echo   Starting EasyCode Services (Conda)
echo ========================================
echo.

echo [1/2] Starting Backend Service (FastAPI)...
start "EasyCode API (Backend)" powershell -ExecutionPolicy ByPass -NoExit -Command "& 'C:\ProgramData\anaconda3\shell\condabin\conda-hook.ps1'; conda activate easycode; cd backend; echo 'Checking dependencies...'; pip install -r requirements.txt; echo 'Starting FastAPI server...'; python main.py"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Frontend Service (Vue+Vite)...
start "EasyCode Web (Frontend)" powershell -ExecutionPolicy ByPass -NoExit -Command "cd frontend; if (-not (Test-Path node_modules)) { echo 'Installing npm dependencies...'; npm install }; echo 'Starting frontend dev server...'; npm run dev"

echo.
echo ========================================
echo  All services have been started!
echo  Please check the new PowerShell windows.
echo ========================================
pause
