# MOU Management System - FastAPI Migration

This project has been migrated from Django to FastAPI with PostgreSQL and Uvicorn.

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL (via SQLAlchemy 2.0)
- **ASGI Server**: Uvicorn
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: Bcrypt
- **Database Migrations**: Alembic
- **Email**: aiosmtplib (async)
- **PDF Generation**: ReportLab

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip

## Setup Instructions

### 1. Install PostgreSQL

Download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/)

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE mou_db;

# Create user (optional)
CREATE USER mou_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mou_db TO mou_user;

# Exit
\q
```

### 3. Configure Environment

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` and update:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Generate a secure random key
- `EMAIL_*`: Email server credentials

### 4. Install Python Dependencies

```bash
# Using the new FastAPI requirements
pip install -r requirements_fastapi.txt
```

### 5. Run Database Migrations

```bash
# Initialize database schema
alembic upgrade head
```

### 6. Create Initial Data (Optional)

You can create an admin user and sample departments/outcomes:

```python
# Run Python shell
python

# Create admin user
from app.database import SessionLocal
from app.models import User, Department, Outcome
from app.auth import get_password_hash

db = SessionLocal()

# Create admin user
admin = User(
    username="admin",
    email="admin@example.com",
    hashed_password=get_password_hash("admin123"),
    is_staff=True,
    is_superuser=True
)
db.add(admin)

# Create departments
departments = [
    Department(code="CSE", name="Computer Science and Engineering"),
    Department(code="IT", name="Information Technology"),
    Department(code="ECE", name="Electronics and Communication Engineering"),
    Department(code="MECH", name="Mechanical Engineering"),
    Department(code="CIVIL", name="Civil Engineering"),
]
db.add_all(departments)

# Create outcomes
outcomes = [
    Outcome(code="PLACE", name="Placement"),
    Outcome(code="IV", name="Industrial Visit"),
    Outcome(code="WORK", name="Workshop"),
    Outcome(code="RES", name="Research Collaboration"),
    Outcome(code="INTERN", name="Internship"),
]
db.add_all(outcomes)

db.commit()
db.close()
```

### 7. Run the Application

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with username/password
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/org/request-otp` - Request OTP for org login
- `POST /api/auth/org/verify-otp` - Verify org OTP
- `POST /api/auth/password-reset/request` - Request password reset
- `POST /api/auth/password-reset/verify` - Verify reset and change password

### MOU Management
- `GET /api/mou/` - List all MOUs
- `GET /api/mou/active` - List active MOUs
- `GET /api/mou/expired` - List expired MOUs
- `GET /api/mou/{id}` - Get MOU details
- `POST /api/mou/` - Create new MOU (staff only)
- `PUT /api/mou/{id}` - Update MOU
- `DELETE /api/mou/{id}` - Delete MOU (staff only)
- `POST /api/mou/filter` - Filter MOUs
- `POST /api/mou/{id}/upload-document` - Upload MOU document

### Events
- `GET /api/events/mou/{mou_id}` - List events for MOU
- `GET /api/events/{id}` - Get event details
- `POST /api/events/mou/{mou_id}` - Create event
- `PUT /api/events/{id}` - Update event
- `DELETE /api/events/{id}` - Delete event

### Departments & Outcomes
- `GET /api/departments` - List departments
- `POST /api/departments` - Create department (staff only)
- `GET /api/outcomes` - List outcomes
- `POST /api/outcomes` - Create outcome (staff only)

## Authentication

The API uses JWT Bearer tokens. To authenticate:

1. **Login**: POST to `/api/auth/login` with username and password
2. **Get Token**: Response contains `access_token`
3. **Use Token**: Include in requests as: `Authorization: Bearer <token>`

Example:
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Use token
curl http://localhost:8000/api/mou/ \
  -H "Authorization: Bearer <your-token>"
```

## Migration from Django

### Key Changes

1. **Database**: SQLite → PostgreSQL
2. **ORM**: Django ORM → SQLAlchemy
3. **Server**: Django dev server → Uvicorn
4. **Routing**: Django URLs → FastAPI routes
5. **Validation**: Django forms → Pydantic models
6. **Templates**: Django templates → API responses (frontend separate)
7. **Async**: Synchronous → Async support

### Data Migration

To migrate data from the old Django database:

1. Export data from Django:
```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > data.json
```

2. Create a migration script to import into PostgreSQL (custom script needed)

## Development

### Running Tests
```bash
pytest
```

### Create New Migration
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Code Formatting
```bash
black .
isort .
```

## Deployment

### Using Docker
```bash
# Build image
docker build -t mou-api .

# Run container
docker run -d -p 8000:8000 --env-file .env mou-api
```

### Using systemd (Linux)
Create `/etc/systemd/system/mou-api.service`:
```ini
[Unit]
Description=MOU Management API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiry (default: 30)
- `EMAIL_HOST`: SMTP server
- `EMAIL_PORT`: SMTP port
- `EMAIL_USE_TLS`: Use TLS (true/false)
- `EMAIL_HOST_USER`: SMTP username
- `EMAIL_HOST_PASSWORD`: SMTP password
- `DEFAULT_FROM_EMAIL`: From email address
- `DEBUG`: Debug mode (true/false)

## Support

For issues or questions, please check:
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
