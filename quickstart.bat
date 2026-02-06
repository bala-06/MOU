@echo off
REM Quick Start Script for Windows

echo ============================================
echo MOU Management System - FastAPI Quick Start
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/6] Checking Python version...
python --version

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not installed
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo [2/6] Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your settings:
    echo   - DATABASE_URL: PostgreSQL connection string
    echo   - SECRET_KEY: Generate a secure random key
    echo   - EMAIL_*: Email configuration
    echo.
    echo After editing .env, run this script again.
    pause
    exit /b 0
)

echo [2/6] .env file found

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo [3/6] Creating virtual environment...
    python -m venv venv
) else (
    echo [3/6] Virtual environment exists
)

REM Activate virtual environment
echo [4/6] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo [5/6] Installing dependencies...
pip install -r requirements_fastapi.txt

REM Check if PostgreSQL is accessible
echo [6/6] Checking database connection...
python -c "from app.database import engine; engine.connect()" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Could not connect to PostgreSQL database
    echo Please ensure:
    echo   1. PostgreSQL is installed and running
    echo   2. Database 'mou_db' is created
    echo   3. DATABASE_URL in .env is correct
    echo.
    echo To create the database, run in psql:
    echo   CREATE DATABASE mou_db;
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
)

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Run database migrations:
echo      alembic upgrade head
echo.
echo   2. Initialize database with sample data:
echo      python setup.py
echo.
echo   3. Start the server:
echo      uvicorn main:app --reload
echo.
echo   4. Open your browser:
echo      http://localhost:8000/docs
echo.
echo ============================================
pause
