#!/usr/bin/env python3
"""
Setup script to initialize the FastAPI MOU Management System
"""
import sys
from getpass import getpass
from app.database import SessionLocal, engine, Base
from app.models import User, Department, Outcome
from app.auth import get_password_hash


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")


def create_admin_user(db):
    """Create an admin user"""
    print("\n=== Create Admin User ===")
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email: ").strip()
    password = getpass("Enter admin password: ")
    password_confirm = getpass("Confirm password: ")
    
    if password != password_confirm:
        print("✗ Passwords do not match")
        return False
    
    # Check if user exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"✗ User '{username}' already exists")
        return False
    
    admin = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print(f"✓ Admin user '{username}' created successfully")
    return True


def create_departments(db):
    """Create default departments"""
    print("\n=== Creating Departments ===")
    departments_data = [
        {"code": "CSE", "name": "Computer Science and Engineering"},
        {"code": "IT", "name": "Information Technology"},
        {"code": "ECE", "name": "Electronics and Communication Engineering"},
        {"code": "MECH", "name": "Mechanical Engineering"},
        {"code": "CIVIL", "name": "Civil Engineering"},
        {"code": "EEE", "name": "Electrical and Electronics Engineering"},
    ]
    
    created = 0
    for dept_data in departments_data:
        existing = db.query(Department).filter(Department.code == dept_data["code"]).first()
        if not existing:
            dept = Department(**dept_data)
            db.add(dept)
            created += 1
    
    db.commit()
    print(f"✓ Created {created} departments")


def create_outcomes(db):
    """Create default outcomes"""
    print("\n=== Creating Outcomes ===")
    outcomes_data = [
        {"code": "PLACE", "name": "Placement"},
        {"code": "IV", "name": "Industrial Visit"},
        {"code": "WORK", "name": "Workshop"},
        {"code": "RES", "name": "Research Collaboration"},
        {"code": "INTERN", "name": "Internship"},
        {"code": "CONSULT", "name": "Consultancy"},
        {"code": "TRAINING", "name": "Training Program"},
    ]
    
    created = 0
    for outcome_data in outcomes_data:
        existing = db.query(Outcome).filter(Outcome.code == outcome_data["code"]).first()
        if not existing:
            outcome = Outcome(**outcome_data)
            db.add(outcome)
            created += 1
    
    db.commit()
    print(f"✓ Created {created} outcomes")


def main():
    """Main setup function"""
    print("=" * 60)
    print("MOU Management System - FastAPI Setup")
    print("=" * 60)
    
    try:
        # Create tables
        create_tables()
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Create admin user
            create_admin = input("\nCreate admin user? (y/n): ").strip().lower()
            if create_admin == 'y':
                create_admin_user(db)
            
            # Create departments
            create_deps = input("\nCreate default departments? (y/n): ").strip().lower()
            if create_deps == 'y':
                create_departments(db)
            
            # Create outcomes
            create_outs = input("\nCreate default outcomes? (y/n): ").strip().lower()
            if create_outs == 'y':
                create_outcomes(db)
            
            print("\n" + "=" * 60)
            print("Setup completed successfully!")
            print("=" * 60)
            print("\nYou can now start the server with:")
            print("  uvicorn main:app --reload")
            print("\nAPI documentation will be available at:")
            print("  http://localhost:8000/docs")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
