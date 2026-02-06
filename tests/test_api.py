"""
Basic API tests
Run with: pytest tests/test_api.py
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models import User, Department, Outcome
from app.auth import get_password_hash
from main import app

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    
    # Create test user
    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_staff=True
    )
    db.add(test_user)
    
    # Create departments
    dept1 = Department(code="CSE", name="Computer Science")
    dept2 = Department(code="IT", name="Information Technology")
    db.add_all([dept1, dept2])
    
    # Create outcomes
    outcome1 = Outcome(code="PLACE", name="Placement")
    outcome2 = Outcome(code="INTERN", name="Internship")
    db.add_all([outcome1, outcome2])
    
    db.commit()
    db.close()
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(setup_database):
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"


def test_login(setup_database):
    """Test user login"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_departments(setup_database):
    """Test getting departments"""
    response = client.get("/api/departments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_outcomes(setup_database):
    """Test getting outcomes"""
    response = client.get("/api/outcomes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_create_mou_unauthorized(setup_database):
    """Test creating MOU without authentication"""
    response = client.post(
        "/api/mou/",
        json={
            "title": "Test MOU",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "department_ids": [1],
            "outcome_ids": [1]
        }
    )
    assert response.status_code == 401


def test_create_mou_authenticated(setup_database):
    """Test creating MOU with authentication"""
    # Login first
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Create MOU
    response = client.post(
        "/api/mou/",
        json={
            "title": "Test MOU",
            "organization_name": "Test Organization",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "department_ids": [1],
            "outcome_ids": [1]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test MOU"


def test_get_mous(setup_database):
    """Test getting MOUs list"""
    response = client.get("/api/mou/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_filter_mous(setup_database):
    """Test filtering MOUs"""
    response = client.post(
        "/api/mou/filter",
        json={
            "title": "Test"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
