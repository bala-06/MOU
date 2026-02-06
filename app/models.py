from sqlalchemy import Column, Integer, String, Date, Decimal, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime


# Association tables for many-to-many relationships
mou_department_association = Table(
    'mou_department',
    Base.metadata,
    Column('mou_id', Integer, ForeignKey('mous.id', ondelete='CASCADE')),
    Column('department_id', Integer, ForeignKey('departments.id', ondelete='CASCADE'))
)

mou_outcome_association = Table(
    'mou_outcome',
    Base.metadata,
    Column('mou_id', Integer, ForeignKey('mous.id', ondelete='CASCADE')),
    Column('outcome_id', Integer, ForeignKey('outcomes.id', ondelete='CASCADE'))
)


class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    
    # Relationships
    mous = relationship('MOU', secondary=mou_department_association, back_populates='departments')


class Outcome(Base):
    __tablename__ = 'outcomes'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    
    # Relationships
    mous = relationship('MOU', secondary=mou_outcome_association, back_populates='outcomes')


class MOU(Base):
    __tablename__ = 'mous'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    organization_name = Column(String(255), nullable=True, index=True)
    
    # Date range
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Document upload
    document = Column(String(500), nullable=True)  # File path
    
    # Status
    status = Column(String(20), default='draft', nullable=False)
    
    # MOU Coordinator
    mou_coordinator_name = Column(String(100), nullable=True)
    mou_coordinator_mobile = Column(String(15), nullable=True)
    mou_coordinator_email = Column(String(100), nullable=True, index=True)
    
    # Staff Coordinator
    staff_coordinator_name = Column(String(100), nullable=True)
    staff_coordinator_mobile = Column(String(15), nullable=True)
    staff_coordinator_email = Column(String(100), nullable=True, index=True)
    
    # Payment
    payment_paid = Column(Decimal(10, 2), default=0.00, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    departments = relationship('Department', secondary=mou_department_association, back_populates='mous')
    outcomes = relationship('Outcome', secondary=mou_outcome_association, back_populates='mous')
    events = relationship('Event', back_populates='mou', cascade='all, delete-orphan')


class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, index=True)
    mou_id = Column(Integer, ForeignKey('mous.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    status = Column(String(50), default='Pending', nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    mou = relationship('MOU', back_populates='events')


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    login_attempts = relationship('LoginAttempt', back_populates='user', cascade='all, delete-orphan')


class LoginAttempt(Base):
    __tablename__ = 'login_attempts'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    username = Column(String(150), nullable=False, index=True)
    success = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='login_attempts')


class OrgOTP(Base):
    __tablename__ = 'org_otps'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)


class PasswordResetOTP(Base):
    __tablename__ = 'password_reset_otps'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), nullable=False, index=True)
    email = Column(String(100), nullable=True)
    code = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
