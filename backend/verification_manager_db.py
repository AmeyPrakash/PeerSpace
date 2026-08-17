import time
import random
import secrets
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta, timezone

from backend.models.models import VerificationOTP

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
    
    # --- MOCK SENDING ---
    # TODO: Integrate Twilio (for phone) or SendGrid (for email) here.
    # e.g., if contact_type == "email": sendgrid.send(target, otp)
    print("=" * 50)
    print(f"MOCK OTP DELIVERY")
    print(f"To: {target} ({contact_type})")
    print(f"Your PeerSpace Verification Code is: {otp}")
    print("=" * 50)
    # --------------------
    
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
