from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# Department Schemas
class DepartmentBase(BaseModel):
    code: str
    name: str


class DepartmentCreate(DepartmentBase):
    pass


class Department(DepartmentBase):
    id: int
    
    class Config:
        from_attributes = True


# Outcome Schemas
class OutcomeBase(BaseModel):
    code: str
    name: str


class OutcomeCreate(OutcomeBase):
    pass


class Outcome(OutcomeBase):
    id: int
    
    class Config:
        from_attributes = True


# Event Schemas
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: date
    status: str = "Pending"


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    status: Optional[str] = None


class Event(EventBase):
    id: int
    mou_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# MOU Schemas
class MOUBase(BaseModel):
    title: str
    organization_name: Optional[str] = None
    start_date: date
    end_date: date
    status: str = "draft"
    mou_coordinator_name: Optional[str] = None
    mou_coordinator_mobile: Optional[str] = None
    mou_coordinator_email: Optional[EmailStr] = None
    staff_coordinator_name: Optional[str] = None
    staff_coordinator_mobile: Optional[str] = None
    staff_coordinator_email: Optional[EmailStr] = None
    payment_paid: Decimal = Decimal("0.00")


class MOUCreate(MOUBase):
    department_ids: List[int]
    outcome_ids: List[int]


class MOUUpdate(BaseModel):
    title: Optional[str] = None
    organization_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    mou_coordinator_name: Optional[str] = None
    mou_coordinator_mobile: Optional[str] = None
    mou_coordinator_email: Optional[EmailStr] = None
    staff_coordinator_name: Optional[str] = None
    staff_coordinator_mobile: Optional[str] = None
    staff_coordinator_email: Optional[EmailStr] = None
    payment_paid: Optional[Decimal] = None
    department_ids: Optional[List[int]] = None
    outcome_ids: Optional[List[int]] = None


class MOU(MOUBase):
    id: int
    document: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    departments: List[Department] = []
    outcomes: List[Outcome] = []
    events: List[Event] = []
    
    class Config:
        from_attributes = True


class MOUList(BaseModel):
    id: int
    title: str
    organization_name: Optional[str] = None
    start_date: date
    end_date: date
    status: str
    departments: List[Department] = []
    
    class Config:
        from_attributes = True


# Filter Schema
class MOUFilter(BaseModel):
    title: Optional[str] = None
    organization_name: Optional[str] = None
    department_id: Optional[int] = None
    outcome_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_staff: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# OTP Schemas
class OrgOTPRequest(BaseModel):
    email: EmailStr


class OrgOTPVerify(BaseModel):
    email: EmailStr
    code: str


class PasswordResetRequest(BaseModel):
    username: str
    email: Optional[EmailStr] = None


class PasswordResetVerify(BaseModel):
    username: str
    code: str
    new_password: str


# Email Schema
class EmailSchema(BaseModel):
    subject: str
    body: str
