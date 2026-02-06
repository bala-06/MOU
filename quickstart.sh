#!/bin/bash
# Quick Start Script for Linux/Mac

echo "============================================"
echo "MOU Management System - FastAPI Quick Start"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "[1/6] Checking Python version..."
python3 --version

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip is not installed"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[2/6] Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Please edit .env file with your settings:"
    echo "  - DATABASE_URL: PostgreSQL connection string"
    echo "  - SECRET_KEY: Generate a secure random key"
    echo "  - EMAIL_*: Email configuration"
    echo ""
    echo "After editing .env, run this script again."
    exit 0
fi

echo "[2/6] .env file found"

# Create virtual environment if it doesn't exist
if [ ! -d venv ]; then
    echo "[3/6] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[3/6] Virtual environment exists"
fi

# Activate virtual environment
echo "[4/6] Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "[5/6] Installing dependencies..."
pip install -r requirements_fastapi.txt

# Check if PostgreSQL is accessible
echo "[6/6] Checking database connection..."
python -c "from app.database import engine; engine.connect()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "WARNING: Could not connect to PostgreSQL database"
    echo "Please ensure:"
    echo "  1. PostgreSQL is installed and running"
    echo "  2. Database 'mou_db' is created"
    echo "  3. DATABASE_URL in .env is correct"
    echo ""
    echo "To create the database, run in psql:"
    echo "  CREATE DATABASE mou_db;"
    echo ""
    read -p "Continue anyway? (y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Run database migrations:"
echo "     alembic upgrade head"
echo ""
echo "  2. Initialize database with sample data:"
echo "     python setup.py"
echo ""
echo "  3. Start the server:"
echo "     uvicorn main:app --reload"
echo ""
echo "  4. Open your browser:"
echo "     http://localhost:8000/docs"
echo ""
echo "============================================"
