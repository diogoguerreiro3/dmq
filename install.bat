@echo off
setlocal EnableExtensions

echo ==========================================
echo   DMQ - Disney Music Quiz
echo   Windows Installation Script
echo ==========================================
echo.

REM Go to the script directory (ensures correct paths when run from PowerShell/CMD)
cd /d "%~dp0"

REM ------------------------------------------------------------
REM 1) Check for Python
REM ------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found in PATH.
  echo Please install Python 3.14+ and make sure it is added to PATH.
  pause
  exit /b 1
)

echo [1/6] Python detected:
python --version
echo.

REM ------------------------------------------------------------
REM 2) Create virtual environment if it does not exist
REM ------------------------------------------------------------
echo [2/6] Preparing virtual environment...
if exist "venv\Scripts\python.exe" (
  echo Virtual environment already exists. OK.
) else (
  python -m venv venv
  if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
  )
  echo Virtual environment created.
)
echo.

REM ------------------------------------------------------------
REM 3) Force pip to NOT use user-site packages
REM ------------------------------------------------------------
set "PYTHONNOUSERSITE=1"
set "PIP_USER=0"

REM ------------------------------------------------------------
REM 4) Clean corrupted distributions (~ip / ~pip) inside venv
REM ------------------------------------------------------------
echo [3/6] Cleaning corrupted distributions (~ip / ~pip) in venv (if any)...
for /d %%D in ("venv\Lib\site-packages\~ip*") do (
  echo   - removing: %%D
  rmdir /s /q "%%D" >nul 2>&1
)
for /d %%D in ("venv\Lib\site-packages\~pip*") do (
  echo   - removing: %%D
  rmdir /s /q "%%D" >nul 2>&1
)
echo.

REM ------------------------------------------------------------
REM 5) Update pip, setuptools, and wheel inside venv
REM ------------------------------------------------------------
echo [4/6] Updating pip, setuptools, and wheel in the virtual environment...
venv\Scripts\python.exe -m pip install -U pip setuptools wheel
if errorlevel 1 (
  echo [ERROR] Failed to update pip, setuptools, and wheel.
  pause
  exit /b 1
)
echo.

REM ------------------------------------------------------------
REM 6) Install dependencies from requirements.txt
REM ------------------------------------------------------------
if not exist "requirements.txt" (
  echo [ERROR] requirements.txt not found in: %CD%
  pause
  exit /b 1
)

echo [5/6] Installing dependencies from requirements.txt...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Failed to install dependencies.
  pause
  exit /b 1
)
echo.

REM ------------------------------------------------------------
REM 7) Check for FFmpeg
REM ------------------------------------------------------------
echo [6/6] Checking for ffmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo [WARN] ffmpeg was NOT found in PATH.
  echo Install it with winget (recommended):
  echo   winget install Gyan.FFmpeg
  echo Or with Chocolatey:
  echo   choco install ffmpeg
) else (
  echo ffmpeg OK:
  ffmpeg -version | findstr /i "ffmpeg version"
)

echo.
echo ==========================================
echo   Installation completed!
echo ==========================================
echo.
echo To run the application:
echo   run.bat
echo.
pause
endlocal
