import time
import random
import secrets
import os
import smtplib
from email.message import EmailMessage
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta, timezone
import logging

from backend.models.models import VerificationOTP

logger = logging.getLogger("peerspace.verification")

OTP_EXPIRY_SECONDS = 300  # 5 minutes

def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"

async def send_otp(db: AsyncSession, target: str, contact_type: str) -> Tuple[bool, str]:
    """
    Generate and 'send' an OTP to a target (email or phone) using database persistence.
    """
    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=OTP_EXPIRY_SECONDS)
    
    # Store OTP in Database
    new_otp = VerificationOTP(
        target=target,
        contact_type=contact_type,
        otp_code=otp,
        expires_at=expires_at
    )
    db.add(new_otp)
    await db.commit()
    
    # --- EMAIL DELIVERY ---
    if contact_type == "email":
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT", "587")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM_EMAIL", "noreply@peerspace.app")

        if smtp_server and smtp_user and smtp_password:
            try:
                msg = EmailMessage()
                msg.set_content(f"Your PeerSpace Verification Code is: {otp}\n\nThis code expires in 5 minutes.")
                msg['Subject'] = 'PeerSpace Verification Code'
                msg['From'] = smtp_from
                msg['To'] = target

                with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                
                logger.info(f"OTP sent to {target} via SMTP")
                return True, "OTP sent successfully"
            except Exception as e:
                logger.error(f"Failed to send OTP email via SMTP: {e}")
                return False, "Failed to send verification code."
        else:
            # Fallback for development if SMTP is not configured
            logger.info("=" * 50)
            logger.info(f"MOCK OTP DELIVERY (SMTP not configured)")
            logger.info(f"To: {target} ({contact_type})")
            logger.info(f"Your PeerSpace Verification Code is: {otp}")
            logger.info("=" * 50)
    else:
        # Fallback for phone SMS (Needs Twilio in production)
        logger.info("=" * 50)
        logger.info(f"MOCK OTP DELIVERY (Phone integration pending)")
        logger.info(f"To: {target} ({contact_type})")
        logger.info(f"Your PeerSpace Verification Code is: {otp}")
        logger.info("=" * 50)
    
    return True, "OTP sent successfully"

async def verify_otp(db: AsyncSession, target: str, otp: str) -> Tuple[bool, str, None]:
    """
    Verify an OTP against the database record.
    Returns: (is_valid, message, None)
    """
    stmt = select(VerificationOTP).where(VerificationOTP.target == target).order_by(VerificationOTP.created_at.desc())
    result = await db.execute(stmt)
    record = result.scalars().first()
    
    if not record:
        return False, "No pending verification found for this contact.", None
        
    if record.expires_at.tzinfo is None:
        record.expires_at = record.expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > record.expires_at:
        # Delete expired record
        await db.delete(record)
        await db.commit()
        return False, "OTP has expired. Please request a new one.", None
        
    if record.otp_code != otp:
        return False, "Invalid OTP.", None
        
    # Valid! Clean up used OTP
    await db.delete(record)
    await db.commit()
    
    return True, "Verification successful", None
