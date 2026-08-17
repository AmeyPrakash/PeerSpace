"""
Authentication & Anonymous Identity Routes
"""

import uuid
from fastapi import APIRouter, Request, HTTPException, status
from backend.models.schemas import StudentAuthPayload, AdminAuthPayload
from backend.rate_limiter import check_rate_limit, check_admin_rate_limit, record_admin_auth_failure, reset_admin_auth_attempts
from backend.session_manager import get_or_create_agent
from backend.config import COUNSELOR_PASSKEY_HASH
from backend.security import verify_passkey

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/student")
async def student_auth_api(payload: StudentAuthPayload, request: Request):
    """Initializes, resumes, or randomizes an anonymous student session."""
    client_ip = request.client.host if request.client else "unknown"
    client_key = f"{client_ip}:{payload.session_id or 'anon'}"
    check_rate_limit(client_key)

    _, sid, student_alias = get_or_create_agent(
        session_id=payload.session_id,
        alias=payload.alias,
        randomize_alias=bool(payload.randomize)
    )
    return {
        "status": "authenticated",
        "session_id": sid,
        "alias": student_alias
    }

@router.post("/admin")
async def admin_auth_api(payload: AdminAuthPayload, request: Request):
    """Authenticates campus mental health staff with secure passkey."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Apply enhanced rate limiting with brute force protection
    check_admin_rate_limit(client_ip)

    # Use constant-time comparison to prevent timing attacks
    is_valid = verify_passkey(payload.passkey, COUNSELOR_PASSKEY_HASH)
    
    if not is_valid:
        # Record failed attempt for exponential backoff
        try:
            record_admin_auth_failure(client_ip)
        except HTTPException:
            # Re-raise if max attempts exceeded
            raise
        
        # Return generic error message to avoid info leakage
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid counselor access passkey."
        )
    
    # Reset failed attempts on successful authentication
    reset_admin_auth_attempts(client_ip)
    
    return {
        "status": "authenticated",
        "role": "counselor",
        "token": f"counselor_auth_{uuid.uuid4().hex[:12]}"
    }
