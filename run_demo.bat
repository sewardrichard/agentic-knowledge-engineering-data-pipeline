@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================================
echo    AURA KNOWLEDGE PIPELINE - ONE-CLICK DEMO
echo    Automated Setup for Recruiters
echo ========================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Step 1: Clean up previous processed data
echo [1/6] Cleaning up previous data...
if exist "data\processed\aura.duckdb" (
    del /f /q "data\processed\aura.duckdb" 2>nul
    echo       Removed old database file
)
if exist "aura_bronze.duckdb" (
    del /f /q "aura_bronze.duckdb" 2>nul
)
echo       Done!
echo.

REM Step 2: Check Python installation
echo [2/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo       Found Python %PYVER%
echo.

REM Step 3: Create virtual environment
echo [3/6] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    echo       Created new virtual environment
) else (
    echo       Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Step 4: Install dependencies
echo.
echo [4/6] Installing dependencies (this may take 1-2 minutes)...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo       Dependencies installed!
echo.

REM Step 5: Initialize project
echo [5/6] Initializing project and generating mock data...
python scripts/setup_project.py
echo.

REM Step 6: Start API server in background and run pipeline
echo [6/6] Starting demo...
echo.
echo       Starting mock API server...

REM Start uvicorn in a new minimized window
start /min "Aura API Server" cmd /c "call venv\Scripts\activate.bat && uvicorn mock_apis.main:app --port 8000"

REM Wait for server to start
echo       Waiting for API server to initialize...
timeout /t 3 /nobreak >nul

REM Check if server is running
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo       Retrying connection...
    timeout /t 2 /nobreak >nul
)

echo       API server is running!
echo.

REM Run the full pipeline
echo ========================================================
echo    RUNNING DATA PIPELINE
echo ========================================================
echo.
python scripts/run_pipeline.py
echo.

REM Run the demo queries
echo ========================================================
echo    RUNNING AURA AGENT DEMO QUERIES
echo ========================================================
echo.
python scripts/demo_aura_queries.py
echo.

echo ========================================================
echo    DEMO COMPLETE!
echo ========================================================
echo.
echo The Aura Knowledge Pipeline has been successfully demonstrated.
echo.
echo Key outputs:
echo   - Database: data\processed\aura.duckdb
echo   - Mock API: http://localhost:8000 (running in background)
echo.
echo To stop the API server, close the "Aura API Server" window
echo or run: taskkill /FI "WINDOWTITLE eq Aura API Server"
echo.
echo For more details, see README.md or RECRUITER_SETUP.md
echo.
pause
