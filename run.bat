@echo off
echo ==========================================
echo   DMQ - Disney Music Quiz
echo   Starting Application...
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)

REM Run the application
echo.
echo [2/2] Starting Flask application...
echo.
echo ==========================================
echo   Server running at: http://localhost:5000
echo   Press Ctrl+C to stop the server
echo ==========================================
echo.

python app.py

REM Deactivate virtual environment on exit
deactivate
