#!/bin/bash
# Common commands for MOU Management System

case "$1" in
    install)
        echo "Installing dependencies..."
        pip install -r requirements_fastapi.txt
        pip install -r requirements_dev.txt
        echo "Done!"
        ;;
    
    run)
        echo "Starting development server..."
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
        ;;
    
    test)
        echo "Running tests..."
        pytest tests/ -v
        ;;
    
    migrate)
        echo "Running database migrations..."
        alembic upgrade head
        echo "Done!"
        ;;
    
    init)
        echo "Initializing database..."
        python setup.py
        ;;
    
    docker-up)
        echo "Starting Docker services..."
        docker-compose up -d
        echo "Services started!"
        echo "API: http://localhost:8000/docs"
        ;;
    
    docker-down)
        echo "Stopping Docker services..."
        docker-compose down
        echo "Services stopped!"
        ;;
    
    clean)
        echo "Cleaning temporary files..."
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
        find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null
        rm -f test.db 2>/dev/null
        echo "Done!"
        ;;
    
    *)
        echo "Usage: ./run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  install       - Install dependencies"
        echo "  run          - Start development server"
        echo "  test         - Run tests"
        echo "  migrate      - Run database migrations"
        echo "  init         - Initialize database with sample data"
        echo "  docker-up    - Start with Docker"
        echo "  docker-down  - Stop Docker services"
        echo "  clean        - Clean temporary files"
        echo ""
        ;;
esac
