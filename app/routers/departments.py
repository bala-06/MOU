from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(tags=["Departments & Outcomes"])


# Department endpoints
@router.get("/api/departments", response_model=List[schemas.Department])
def list_departments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all departments"""
    departments = db.query(models.Department).offset(skip).limit(limit).all()
    return departments


@router.post("/api/departments", response_model=schemas.Department, status_code=status.HTTP_201_CREATED)
def create_department(
    department_data: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_staff_user)
):
    """Create a new department (staff only)"""
    # Check if code already exists
    existing = db.query(models.Department).filter(models.Department.code == department_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists"
        )
    
    new_department = models.Department(**department_data.model_dump())
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    
    return new_department


# Outcome endpoints
@router.get("/api/outcomes", response_model=List[schemas.Outcome])
def list_outcomes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all outcomes"""
    outcomes = db.query(models.Outcome).offset(skip).limit(limit).all()
    return outcomes


@router.post("/api/outcomes", response_model=schemas.Outcome, status_code=status.HTTP_201_CREATED)
def create_outcome(
    outcome_data: schemas.OutcomeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_staff_user)
):
    """Create a new outcome (staff only)"""
    # Check if code already exists
    existing = db.query(models.Outcome).filter(models.Outcome.code == outcome_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Outcome code already exists"
        )
    
    new_outcome = models.Outcome(**outcome_data.model_dump())
    db.add(new_outcome)
    db.commit()
    db.refresh(new_outcome)
    
    return new_outcome
