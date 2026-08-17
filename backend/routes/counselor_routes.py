"""
Counselor Application Routes
Handles counselor application submissions and admin review.
"""

from fastapi import APIRouter, HTTPException, status, Request, Depends
from backend.models.schemas import CounselorApplicationPayload, CounselorApplicationResponse
from backend.counselor_manager import (
    submit_application,
    get_application,
    get_all_applications,
    update_application_status,
    get_application_stats,
    get_pending_applications,
    get_approved_counselors
)
from backend.verification_manager import send_otp, verify_otp
from pydantic import BaseModel
from backend.rate_limiter import check_rate_limit
from backend.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

router = APIRouter(prefix="/api/counselor", tags=["counselor"])

class OTPRequest(BaseModel):
    target: str
    type: str

class OTPVerify(BaseModel):
    target: str
    otp: str

class VerifyApplicationRequest(BaseModel):
    application_id: str
    email: str
    email_otp: str
    phone: Optional[str] = None
    phone_otp: Optional[str] = None

@router.post("/verify/send")
async def send_verification_otp(req: OTPRequest):
    if req.type not in ["email", "phone"]:
        raise HTTPException(status_code=400, detail="Invalid verification type")
    success, msg = await send_otp(None, req.target, req.type)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}

@router.post("/verify/check")
async def check_verification_otp(req: OTPVerify):
    is_valid, msg, token = await verify_otp(None, req.target, req.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "token": token}


import os

@router.post("/verify-application")
async def verify_application_and_approve(req: VerifyApplicationRequest):
    # Verify email
    is_valid_email, msg_email, _ = await verify_otp(None, req.email, req.email_otp)
    if not is_valid_email:
        raise HTTPException(status_code=400, detail=f"Email Verification Failed: {msg_email}")

    # Verify phone if provided
    if req.phone and req.phone_otp:
        is_valid_phone, msg_phone, _ = await verify_otp(None, req.phone, req.phone_otp)
        if not is_valid_phone:
            raise HTTPException(status_code=400, detail=f"Phone Verification Failed: {msg_phone}")

    # Update application status to approved
    update_success = update_application_status(req.application_id, "approved")
    if not update_success:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Reveal the global passkey
    passkey = os.getenv("COUNSELOR_PASSKEY", "default_secure_passkey")

    return {
        "status": "success",
        "message": "Verification successful! You are now approved.",
        "passkey": passkey
    }


@router.post("/apply", response_model=CounselorApplicationResponse)
async def submit_counselor_application(
    payload: CounselorApplicationPayload,
    request: Request
):
    """Submit application to become a campus counselor."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Rate limit application submissions (1 per 60 seconds per IP)
    check_rate_limit(f"counselor_apply:{client_ip}")
    
    # Validate required field
    if not payload.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms and conditions to apply."
        )
    
    # Submit application
    app_id, message = submit_application(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone or "",
        highest_degree=payload.highest_degree,
        degree_field=payload.degree_field,
        university=payload.university,
        graduation_year=payload.graduation_year,
        certifications=payload.certifications or "",
        years_of_experience=payload.years_of_experience,
        current_role=payload.current_role,
        specializations=payload.specializations,
        motivation=payload.motivation,
        background_info=payload.background_info or ""
    )
    
    return CounselorApplicationResponse(
        status="submitted",
        application_id=app_id,
        message=f"Thank you for applying! Application ID: {app_id}. We will review your qualifications and contact you within 5 business days.",
        estimated_review_days=5
    )


@router.get("/application/{application_id}")
async def get_application_status(application_id: str):
    """Get status of a counselor application."""
    application = get_application(application_id)
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )
    
    # Return non-sensitive fields only (no admin notes for applicant)
    return {
        "application_id": application.get("application_id"),
        "full_name": application.get("full_name"),
        "status": application.get("status"),
        "submitted_at": application.get("submitted_at"),
        "reviewed_at": application.get("reviewed_at"),
        "message": f"Your application status: {application.get('status')}"
    }


@router.get("/stats")
async def get_counselor_stats():
    """Get application statistics (admin only - should require auth token)."""
    # TODO: Add proper authentication check
    return get_application_stats()


@router.get("/pending")
async def list_pending_applications():
    """Get all pending applications (admin only)."""
    # TODO: Add proper authentication check
    pending = get_pending_applications()
    return {
        "count": len(pending),
        "applications": pending
    }


@router.get("/approved")
async def list_approved_counselors():
    """Get all approved counselors."""
    approved = get_approved_counselors()
    return {
        "count": len(approved),
        "counselors": [
            {
                "name": app["full_name"],
                "specializations": app["specializations"],
                "experience_years": app["years_of_experience"],
                "current_role": app["current_role"]
            }
            for app in approved
        ]
    }


@router.post("/review/{application_id}")
async def review_application(
    application_id: str,
    status: str,
    notes: str = ""
):
    """Review and approve/reject an application (admin only)."""
    # TODO: Add proper authentication check with admin token
    
    if status not in ["under_review", "approved", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'under_review', 'approved', or 'rejected'."
        )
    
    success = update_application_status(application_id, status, notes)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )
    
    return {
        "status": "success",
        "message": f"Application {application_id} status updated to {status}",
        "application_id": application_id
    }
