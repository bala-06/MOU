from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import date
import os
from pathlib import Path
from app.database import get_db
from app import models, schemas, auth
from app.config import settings

router = APIRouter(prefix="/api/mou", tags=["MOU"])


@router.get("/", response_model=List[schemas.MOUList])
def list_mous(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all MOUs"""
    mous = db.query(models.MOU).offset(skip).limit(limit).all()
    return mous


@router.get("/active", response_model=List[schemas.MOUList])
def list_active_mous(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List active MOUs"""
    today = date.today()
    mous = db.query(models.MOU).filter(models.MOU.end_date >= today).offset(skip).limit(limit).all()
    return mous


@router.get("/expired", response_model=List[schemas.MOUList])
def list_expired_mous(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List expired MOUs"""
    today = date.today()
    mous = db.query(models.MOU).filter(models.MOU.end_date < today).offset(skip).limit(limit).all()
    return mous


@router.get("/{mou_id}", response_model=schemas.MOU)
def get_mou(mou_id: int, db: Session = Depends(get_db)):
    """Get MOU by ID"""
    mou = db.query(models.MOU).filter(models.MOU.id == mou_id).first()
    if not mou:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MOU not found"
        )
    return mou


@router.post("/", response_model=schemas.MOU, status_code=status.HTTP_201_CREATED)
def create_mou(
    mou_data: schemas.MOUCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_staff_user)
):
    """Create a new MOU (staff only)"""
    # Get departments
    departments = db.query(models.Department).filter(
        models.Department.id.in_(mou_data.department_ids)
    ).all()
    
    if len(departments) != len(mou_data.department_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more departments not found"
        )
    
    # Get outcomes
    outcomes = db.query(models.Outcome).filter(
        models.Outcome.id.in_(mou_data.outcome_ids)
    ).all()
    
    if len(outcomes) != len(mou_data.outcome_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more outcomes not found"
        )
    
    # Create MOU
    mou_dict = mou_data.model_dump(exclude={'department_ids', 'outcome_ids'})
    new_mou = models.MOU(**mou_dict)
    new_mou.departments = departments
    new_mou.outcomes = outcomes
    
    db.add(new_mou)
    db.commit()
    db.refresh(new_mou)
    
    return new_mou


@router.put("/{mou_id}", response_model=schemas.MOU)
def update_mou(
    mou_id: int,
    mou_data: schemas.MOUUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Update MOU"""
    mou = db.query(models.MOU).filter(models.MOU.id == mou_id).first()
    if not mou:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MOU not found"
        )
    
    # Check permissions (staff or coordinator)
    is_coordinator = False
    if mou.mou_coordinator_email and current_user.email:
        is_coordinator = mou.mou_coordinator_email.lower() == current_user.email.lower()
    if mou.staff_coordinator_email and current_user.email:
        is_coordinator = is_coordinator or (mou.staff_coordinator_email.lower() == current_user.email.lower())
    
    if not (current_user.is_staff or is_coordinator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields
    update_data = mou_data.model_dump(exclude_unset=True)
    
    # Handle departments
    if 'department_ids' in update_data:
        departments = db.query(models.Department).filter(
            models.Department.id.in_(update_data['department_ids'])
        ).all()
        mou.departments = departments
        del update_data['department_ids']
    
    # Handle outcomes
    if 'outcome_ids' in update_data:
        outcomes = db.query(models.Outcome).filter(
            models.Outcome.id.in_(update_data['outcome_ids'])
        ).all()
        mou.outcomes = outcomes
        del update_data['outcome_ids']
    
    # Update other fields
    for key, value in update_data.items():
        setattr(mou, key, value)
    
    db.commit()
    db.refresh(mou)
    
    return mou


@router.delete("/{mou_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mou(
    mou_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_staff_user)
):
    """Delete MOU (staff only)"""
    mou = db.query(models.MOU).filter(models.MOU.id == mou_id).first()
    if not mou:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MOU not found"
        )
    
    db.delete(mou)
    db.commit()
    
    return None


@router.post("/filter", response_model=List[schemas.MOUList])
def filter_mous(
    filter_data: schemas.MOUFilter,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Filter MOUs based on criteria"""
    query = db.query(models.MOU)
    
    if filter_data.title:
        query = query.filter(models.MOU.title.ilike(f"%{filter_data.title}%"))
    
    if filter_data.organization_name:
        query = query.filter(models.MOU.organization_name.ilike(f"%{filter_data.organization_name}%"))
    
    if filter_data.department_id:
        query = query.join(models.MOU.departments).filter(models.Department.id == filter_data.department_id)
    
    if filter_data.outcome_id:
        query = query.join(models.MOU.outcomes).filter(models.Outcome.id == filter_data.outcome_id)
    
    if filter_data.status:
        query = query.filter(models.MOU.status == filter_data.status)
    
    if filter_data.start_date:
        query = query.filter(models.MOU.start_date >= filter_data.start_date)
    
    if filter_data.end_date:
        query = query.filter(models.MOU.end_date <= filter_data.end_date)
    
    mous = query.offset(skip).limit(limit).all()
    return mous


@router.post("/{mou_id}/upload-document")
async def upload_document(
    mou_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Upload document for MOU"""
    mou = db.query(models.MOU).filter(models.MOU.id == mou_id).first()
    if not mou:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MOU not found"
        )
    
    # Create media directory if it doesn't exist
    media_dir = Path(settings.MEDIA_ROOT) / "mou_documents"
    media_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = media_dir / f"{mou_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Update MOU
    mou.document = str(file_path.relative_to(settings.MEDIA_ROOT))
    db.commit()
    
    return {"filename": file.filename, "path": mou.document}
