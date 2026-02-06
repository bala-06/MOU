from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("/mou/{mou_id}", response_model=List[schemas.Event])
def list_mou_events(
    mou_id: int,
    db: Session = Depends(get_db)
):
    """List all events for a specific MOU"""
    # Check if MOU exists
    mou = db.query(models.MOU).filter(models.MOU.id == mou_id).first()
    if not mou:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MOU not found"
        )
    
    events = db.query(models.Event).filter(models.Event.mou_id == mou_id).all()
    return events


@router.get("/{event_id}", response_model=schemas.Event)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get event by ID"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event


@router.post("/mou/{mou_id}", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
def create_event(
    mou_id: int,
    event_data: schemas.EventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Create a new event for a MOU"""
    # Check if MOU exists
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
    
    # Create event
    new_event = models.Event(**event_data.model_dump(), mou_id=mou_id)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return new_event


@router.put("/{event_id}", response_model=schemas.Event)
def update_event(
    event_id: int,
    event_data: schemas.EventUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Update an event"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get MOU for permission check
    mou = event.mou
    
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
    update_data = event_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    
    db.commit()
    db.refresh(event)
    
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Delete an event"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get MOU for permission check
    mou = event.mou
    
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
    
    db.delete(event)
    db.commit()
    
    return None
