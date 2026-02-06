@echo off
REM Common commands for MOU Management System

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="run" goto run
if "%1"=="test" goto test
if "%1"=="migrate" goto migrate
if "%1"=="init" goto init
if "%1"=="docker-up" goto docker_up
if "%1"=="docker-down" goto docker_down
if "%1"=="clean" goto clean
goto help

:help
echo Usage: run.bat [command]
echo.
echo Commands:
echo   install       - Install dependencies
echo   run          - Start development server
echo   test         - Run tests
echo   migrate      - Run database migrations
echo   init         - Initialize database with sample data
echo   docker-up    - Start with Docker
echo   docker-down  - Stop Docker services
echo   clean        - Clean temporary files
echo.
goto end

:install
echo Installing dependencies...
pip install -r requirements_fastapi.txt
pip install -r requirements_dev.txt
echo Done!
goto end

:run
echo Starting development server...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
goto end

:test
echo Running tests...
pytest tests/ -v
goto end

:migrate
echo Running database migrations...
alembic upgrade head
echo Done!
goto end

:init
echo Initializing database...
python setup.py
goto end

:docker_up
echo Starting Docker services...
docker-compose up -d
echo Services started!
echo API: http://localhost:8000/docs
goto end

:docker_down
echo Stopping Docker services...
docker-compose down
echo Services stopped!
goto end

:clean
echo Cleaning temporary files...
if exist __pycache__ rmdir /s /q __pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist app\__pycache__ rmdir /s /q app\__pycache__
if exist app\routers\__pycache__ rmdir /s /q app\routers\__pycache__
if exist tests\__pycache__ rmdir /s /q tests\__pycache__
if exist test.db del test.db
echo Done!
goto end

:end
