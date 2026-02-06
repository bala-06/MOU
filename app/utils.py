import random
import string
from datetime import datetime, timedelta
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.config import settings
from app import models


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code"""
    return ''.join(random.choices(string.digits, k=length))


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html: bool = False
) -> bool:
    """Send an email using SMTP"""
    try:
        message = MIMEMultipart('alternative')
        message['From'] = settings.DEFAULT_FROM_EMAIL
        message['To'] = to_email
        message['Subject'] = subject
        
        if html:
            message.attach(MIMEText(body, 'html'))
        else:
            message.attach(MIMEText(body, 'plain'))
        
        await aiosmtplib.send(
            message,
            hostname=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            start_tls=settings.EMAIL_USE_TLS,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def create_org_otp(db: Session, email: str) -> str:
    """Create OTP for organization email login"""
    # Clean up expired OTPs
    db.query(models.OrgOTP).filter(
        models.OrgOTP.email == email,
        models.OrgOTP.expires_at < datetime.utcnow()
    ).delete()
    
    # Generate new OTP
    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp = models.OrgOTP(
        email=email,
        code=code,
        expires_at=expires_at
    )
    db.add(otp)
    db.commit()
    
    return code


def verify_org_otp(db: Session, email: str, code: str) -> bool:
    """Verify organization OTP"""
    otp = db.query(models.OrgOTP).filter(
        models.OrgOTP.email == email,
        models.OrgOTP.code == code,
        models.OrgOTP.used == False,
        models.OrgOTP.expires_at > datetime.utcnow()
    ).first()
    
    if not otp:
        return False
    
    otp.used = True
    db.commit()
    return True


def create_password_reset_otp(db: Session, username: str, email: Optional[str] = None) -> str:
    """Create OTP for password reset"""
    # Clean up expired OTPs
    db.query(models.PasswordResetOTP).filter(
        models.PasswordResetOTP.username == username,
        models.PasswordResetOTP.expires_at < datetime.utcnow()
    ).delete()
    
    # Generate new OTP
    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp = models.PasswordResetOTP(
        username=username,
        email=email,
        code=code,
        expires_at=expires_at
    )
    db.add(otp)
    db.commit()
    
    return code


def verify_password_reset_otp(db: Session, username: str, code: str) -> bool:
    """Verify password reset OTP"""
    otp = db.query(models.PasswordResetOTP).filter(
        models.PasswordResetOTP.username == username,
        models.PasswordResetOTP.code == code,
        models.PasswordResetOTP.used == False,
        models.PasswordResetOTP.expires_at > datetime.utcnow()
    ).first()
    
    if not otp:
        return False
    
    otp.used = True
    db.commit()
    return True
