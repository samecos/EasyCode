@echo off
setlocal

echo ========================================
echo   Initializing EasyCode Services (Venv)
echo ========================================
echo.

echo [1/2] Checking Backend Dependencies...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment! Make sure Python is in PATH.
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Installing/Updating Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies!
    pause
    exit /b 1
)
cd ..

echo.
echo [2/2] Checking Frontend Dependencies...
cd frontend
if not exist node_modules (
    echo Installing npm dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install npm dependencies!
        pause
        exit /b 1
    )
)
cd ..

echo.
echo ========================================
echo  Ready! Starting services in new windows...
echo ========================================

rem Both dependencies are satisfied, starting servers
start "EasyCode API (Backend - Venv)" powershell -ExecutionPolicy ByPass -NoExit -Command "cd backend; . .\venv\Scripts\Activate.ps1; echo 'Starting FastAPI server...'; python main.py"

start "EasyCode Web (Frontend)" powershell -ExecutionPolicy ByPass -NoExit -Command "cd frontend; echo 'Starting frontend dev server...'; npm run dev"

echo All services have been started.
pause
