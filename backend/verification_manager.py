import time
import random
from typing import Tuple, Optional

# In-memory storage for OTPs
# Structure: { target: { "otp": "123456", "expires_at": 1234567890, "type": "email|phone" } }
pending_otps: dict = {}

OTP_EXPIRY_SECONDS = 300  # 5 minutes

def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"

async def send_otp(db, target: str, contact_type: str) -> Tuple[bool, str]:
    """
    Generate and 'send' an OTP to a target (email or phone) using in-memory dict for quick demo.
    """
    otp = generate_otp()
    
    # Store OTP in memory
    pending_otps[target] = {
        "otp": otp,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "type": contact_type
    }
    
    # --- MOCK SENDING ---
    print("=" * 50)
    print(f"MOCK OTP DELIVERY")
    print(f"To: {target} ({contact_type})")
    print(f"Your PeerSpace Verification Code is: {otp}")
    print("=" * 50)
    # --------------------
    
    return True, "OTP sent successfully"

async def verify_otp(db, target: str, otp: str) -> Tuple[bool, str, None]:
    """
    Verify an OTP against the in-memory dict.
    Returns: (is_valid, message, None)
    """
    record = pending_otps.get(target)
    
    if not record:
        return False, "No pending verification found for this contact.", None
        
    if time.time() > record["expires_at"]:
        del pending_otps[target]
        return False, "OTP has expired. Please request a new one.", None
        
    if record["otp"] != otp:
        return False, "Invalid OTP.", None
        
    # Valid! Clean up used OTP
    del pending_otps[target]
    
    return True, "Verification successful", None
