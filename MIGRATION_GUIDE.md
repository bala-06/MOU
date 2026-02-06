# Django to FastAPI Migration Guide

## Migration Summary

Your MOU Management System has been successfully migrated from Django to FastAPI with PostgreSQL and Uvicorn.

## What Changed

### Framework & Architecture

**Before (Django):**
- Django 5.1 with Django ORM
- SQLite database
- Django templates for frontend
- Synchronous request handling
- Django's built-in auth system

**After (FastAPI):**
- FastAPI 0.109 with SQLAlchemy ORM
- PostgreSQL database
- RESTful API (frontend decoupled)
- Asynchronous support
- JWT-based authentication

### File Structure Comparison

```
Django Structure          →    FastAPI Structure
├── mou_manager/          →    ├── app/
│   ├── settings.py       →    │   ├── config.py
│   ├── urls.py           →    │   ├── database.py
│   ├── wsgi.py           →    │   ├── models.py
│   └── asgi.py           →    │   ├── schemas.py
├── mou/                  →    │   ├── auth.py
│   ├── models.py         →    │   ├── utils.py
│   ├── views.py          →    │   └── routers/
│   ├── forms.py          →    │       ├── auth.py
│   ├── urls.py           →    │       ├── mou.py
│   └── templates/        →    │       ├── events.py
├── manage.py             →    │       └── departments.py
├── requirements.txt      →    ├── main.py
└── db.sqlite3            →    ├── alembic/
                          →    │   └── versions/
                          →    ├── requirements_fastapi.txt
                          →    ├── alembic.ini
                          →    ├── setup.py
                          →    ├── Dockerfile
                          →    └── docker-compose.yml
```

### Database Models

All Django models have been converted to SQLAlchemy:

| Django Model | FastAPI Model | Changes |
|-------------|---------------|---------|
| `MOU` | `MOU` | Added timestamps, relationships preserved |
| `Event` | `Event` | Added timestamps |
| `Department` | `Department` | Same structure |
| `Outcome` | `Outcome` | Same structure |
| `User` (Django built-in) | `User` | Custom implementation with JWT |
| `LoginAttempt` | `LoginAttempt` | Added user relationship |
| `OrgOTP` | `OrgOTP` | Same structure |
| `PasswordResetOTP` | `PasswordResetOTP` | Same structure |

### API Endpoints Mapping

| Django View | FastAPI Endpoint | Method | Notes |
|------------|------------------|--------|-------|
| `login_view` | `/api/auth/login` | POST | JWT token response |
| `register` | `/api/auth/register` | POST | Creates user |
| `logout_view` | N/A | - | Client discards token |
| `mou_list` | `/api/mou/` | GET | Returns JSON |
| `create_mou` | `/api/mou/` | POST | Staff only |
| `view_mou` | `/api/mou/{id}` | GET | Returns JSON |
| `edit_mou` | `/api/mou/{id}` | PUT | Permissions enforced |
| `delete_mou` | `/api/mou/{id}` | DELETE | Staff only |
| `filter_mou` | `/api/mou/filter` | POST | Filter criteria in body |
| `add_event` | `/api/events/mou/{id}` | POST | Create event |
| `edit_event` | `/api/events/{id}` | PUT | Update event |
| `delete_event` | `/api/events/{id}` | DELETE | Delete event |
| `org_login_request` | `/api/auth/org/request-otp` | POST | Send OTP email |
| `org_login_verify` | `/api/auth/org/verify-otp` | POST | Returns token |
| `password_reset_request` | `/api/auth/password-reset/request` | POST | Send reset OTP |
| `password_reset_verify` | `/api/auth/password-reset/verify` | POST | Reset password |

### Authentication Changes

**Django Session-Based Auth:**
```python
@login_required
def view_mou(request, mou_id):
    user = request.user
    # ...
```

**FastAPI JWT Auth:**
```python
@router.get("/{mou_id}")
def get_mou(
    mou_id: int,
    current_user: User = Depends(get_current_active_user)
):
    # ...
```

**Usage:**
```bash
# 1. Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=password"

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. Use token in requests
curl http://localhost:8000/api/mou/ \
  -H "Authorization: Bearer eyJ..."
```

## Quick Start

### 1. Install PostgreSQL

**Windows:**
```bash
# Download from: https://www.postgresql.org/download/windows/
# Or use chocolatey:
choco install postgresql
```

**Create Database:**
```bash
psql -U postgres
CREATE DATABASE mou_db;
\q
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Minimum required:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/mou_db
# SECRET_KEY=your-secure-random-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements_fastapi.txt
```

### 4. Initialize Database

```bash
# Run setup script (creates tables and initial data)
python setup.py

# Or manually:
alembic upgrade head
```

### 5. Run Server

```bash
# Development mode
uvicorn main:app --reload

# The API will be available at:
# - Main: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

## Using Docker (Recommended)

```bash
# Start PostgreSQL and API
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Data Migration

To migrate existing data from Django SQLite to PostgreSQL:

### Option 1: Manual Export/Import

```bash
# 1. Export from Django (in old project)
python manage.py dumpdata mou --indent 2 > mou_data.json

# 2. Create migration script (example)
# See: scripts/migrate_data.py
```

### Option 2: Direct Database Copy

```python
# Connect to both databases and copy data
# Example script provided in scripts/migrate_data.py
```

## Testing the API

### Using cURL

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=test123"

# Get MOUs (with token)
curl http://localhost:8000/api/mou/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create MOU
curl -X POST http://localhost:8000/api/mou/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test MOU",
    "organization_name": "Test Org",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "status": "active",
    "department_ids": [1],
    "outcome_ids": [1]
  }'
```

### Using Python requests

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/auth/login",
    data={"username": "admin", "password": "password"}
)
token = response.json()["access_token"]

# Get MOUs
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/mou/", headers=headers)
mous = response.json()
```

### Using the Interactive Docs

1. Open http://localhost:8000/docs
2. Click "Authorize" button
3. Login to get token
4. Click "Authorize" again and paste token
5. Try out endpoints interactively

## Frontend Integration

Since FastAPI provides a RESTful API, you'll need a separate frontend:

### Options:
1. **React/Vue/Angular SPA** - Modern approach
2. **Server-rendered with Jinja2** - Traditional (can add to FastAPI)
3. **Mobile app** - Native or React Native

### Example React Integration:

```javascript
// Login
const login = async (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
};

// Get MOUs
const getMOUs = async () => {
  const token = localStorage.getItem('token');
  const response = await fetch('http://localhost:8000/api/mou/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

## Key Differences to Note

### 1. No More Django Templates
- Frontend is now separate from backend
- API returns JSON instead of HTML
- Need to build frontend separately

### 2. Authentication Flow
- No more sessions/cookies (by default)
- JWT tokens stored on client
- Include token in every request

### 3. File Uploads
- Use `multipart/form-data`
- Files stored in `media/` directory
- Access via `/media/` URL

### 4. Database Migrations
- Use Alembic instead of Django migrations
- Run: `alembic revision --autogenerate -m "message"`
- Apply: `alembic upgrade head`

### 5. Admin Interface
- No Django admin (yet)
- Can add FastAPI Admin: `pip install fastapi-admin`
- Or build custom admin in frontend

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -U postgres -d mou_db
```

### Import Errors
```bash
# Ensure you're in the right directory
cd /path/to/project

# Check Python path
python -c "import sys; print(sys.path)"
```

### Port Already in Use
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Use different port
uvicorn main:app --port 8001
```

## Next Steps

1. **Build Frontend**: Create React/Vue app to consume the API
2. **Add Tests**: Use pytest for API testing
3. **Add Logging**: Configure structured logging
4. **Add Monitoring**: Prometheus/Grafana for metrics
5. **Security Hardening**: 
   - Use HTTPS in production
   - Implement rate limiting
   - Add CORS restrictions
   - Secure environment variables

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

## Support

For issues or questions:
1. Check the logs: `docker-compose logs api`
2. Review API docs: http://localhost:8000/docs
3. Check PostgreSQL logs
4. Verify environment variables in `.env`
