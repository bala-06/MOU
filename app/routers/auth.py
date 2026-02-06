from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app import models, schemas, auth, utils
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username exists
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    if user_data.email:
        existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with username and password"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    
    # Get client IP
    client_ip = request.client.host if request.client else None
    
    if not user:
        # Log failed attempt
        auth.log_login_attempt(db, form_data.username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful attempt
    auth.log_login_attempt(db, form_data.username, True, client_ip, user.id)
    
    # Update last login
    user.last_login = auth.datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_active_user)):
    """Get current user information"""
    return current_user


@router.post("/org/request-otp")
async def org_request_otp(otp_request: schemas.OrgOTPRequest, db: Session = Depends(get_db)):
    """Request OTP for organization email login"""
    code = utils.create_org_otp(db, otp_request.email)
    
    # Send OTP via email
    subject = "Your Login OTP"
    body = f"Your OTP code is: {code}\n\nThis code will expire in 10 minutes."
    
    email_sent = await utils.send_email(otp_request.email, subject, body)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )
    
    return {"message": "OTP sent to your email"}


@router.post("/org/verify-otp", response_model=schemas.Token)
def org_verify_otp(otp_verify: schemas.OrgOTPVerify, db: Session = Depends(get_db)):
    """Verify OTP for organization email login"""
    if not utils.verify_org_otp(db, otp_verify.email, otp_verify.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )
    
    # Create a temporary token for organization user
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": f"org:{otp_verify.email}", "type": "org"}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/password-reset/request")
async def password_reset_request(
    reset_request: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset OTP"""
    user = db.query(models.User).filter(models.User.username == reset_request.username).first()
    if not user:
        # Don't reveal that user doesn't exist
        return {"message": "If the account exists, a reset code has been sent"}
    
    email = reset_request.email or user.email
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email associated with this account"
        )
    
    code = utils.create_password_reset_otp(db, user.username, email)
    
    # Send OTP via email
    subject = "Password Reset OTP"
    body = f"Your password reset code is: {code}\n\nThis code will expire in 10 minutes."
    
    email_sent = await utils.send_email(email, subject, body)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset code"
        )
    
    return {"message": "If the account exists, a reset code has been sent"}


@router.post("/password-reset/verify")
def password_reset_verify(
    reset_verify: schemas.PasswordResetVerify,
    db: Session = Depends(get_db)
):
    """Verify OTP and reset password"""
    if not utils.verify_password_reset_otp(db, reset_verify.username, reset_verify.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset code"
        )
    
    user = db.query(models.User).filter(models.User.username == reset_verify.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = auth.get_password_hash(reset_verify.new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}
