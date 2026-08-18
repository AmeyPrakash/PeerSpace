"""
PeerSpace Counselor Application Manager
Handles counselor applications with review workflow using SQLAlchemy.
"""

import time
import uuid
from typing import Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from backend.models.models import CounselorApplication

async def submit_application(
    db: AsyncSession,
    full_name: str,
    email: str,
    phone: str,
    highest_degree: str,
    degree_field: str,
    university: str,
    graduation_year: int,
    certifications: str,
    years_of_experience: int,
    current_role: str,
    specializations: str,
    motivation: str,
    background_info: str
) -> Tuple[str, str]:
    """
    Submit a new counselor application.
    
    Returns:
        Tuple of (application_id, status_message)
    """
    # Generate unique application ID
    app_id = f"app_{uuid.uuid4().hex[:12]}"
    
    # Create application entry
    application = CounselorApplication(
        application_id=app_id,
        full_name=full_name,
        email=email,
        phone=phone,
        highest_degree=highest_degree,
        degree_field=degree_field,
        university=university,
        graduation_year=graduation_year,
        certifications=certifications or "",
        years_of_experience=years_of_experience,
        current_role=current_role,
        specializations=specializations,
        motivation=motivation,
        background_info=background_info or "",
        status="pending"
    )
    
    db.add(application)
    await db.commit()
    
    return app_id, "Application submitted successfully"


async def get_application(db: AsyncSession, application_id: str) -> Dict:
    """Retrieve application by ID."""
    stmt = select(CounselorApplication).where(CounselorApplication.application_id == application_id)
    result = await db.execute(stmt)
    app = result.scalars().first()
    
    if app:
        return _app_to_dict(app)
    return None


async def get_all_applications(db: AsyncSession, status: str = None) -> List[Dict]:
    """
    Get all applications, optionally filtered by status.
    """
    if status:
        stmt = select(CounselorApplication).where(CounselorApplication.status == status)
    else:
        stmt = select(CounselorApplication)
        
    result = await db.execute(stmt)
    apps = result.scalars().all()
    
    return [_app_to_dict(app) for app in apps]


async def update_application_status(
    db: AsyncSession,
    application_id: str,
    new_status: str,
    reviewer_notes: str = None
) -> bool:
    """
    Update application status (for admin approval workflow).
    """
    stmt = select(CounselorApplication).where(CounselorApplication.application_id == application_id)
    result = await db.execute(stmt)
    app = result.scalars().first()
    
    if not app:
        return False
        
    app.status = new_status
    app.reviewed_at = datetime.now(timezone.utc)
    if reviewer_notes:
        app.reviewer_notes = reviewer_notes
        
    await db.commit()
    return True


async def get_application_stats(db: AsyncSession) -> Dict:
    """Get statistics about applications."""
    stmt = select(CounselorApplication.status, func.count(CounselorApplication.id)).group_by(CounselorApplication.status)
    result = await db.execute(stmt)
    
    stats = {
        "total_applications": 0,
        "pending": 0,
        "under_review": 0,
        "approved": 0,
        "rejected": 0
    }
    
    for status, count in result:
        stats[status] = count
        stats["total_applications"] += count
        
    return stats


async def get_pending_applications(db: AsyncSession) -> List[Dict]:
    """Get all pending applications (not yet reviewed)."""
    return await get_all_applications(db, status="pending")


async def get_approved_counselors(db: AsyncSession) -> List[Dict]:
    """Get all approved counselor applications."""
    return await get_all_applications(db, status="approved")


def _app_to_dict(app: CounselorApplication) -> Dict:
    return {
        "application_id": app.application_id,
        "full_name": app.full_name,
        "email": app.email,
        "phone": app.phone,
        "highest_degree": app.highest_degree,
        "degree_field": app.degree_field,
        "university": app.university,
        "graduation_year": app.graduation_year,
        "certifications": app.certifications,
        "years_of_experience": app.years_of_experience,
        "current_role": app.current_role,
        "specializations": app.specializations,
        "motivation": app.motivation,
        "background_info": app.background_info,
        "status": app.status,
        "reviewed_at": app.reviewed_at.timestamp() if app.reviewed_at else None,
        "reviewer_notes": app.reviewer_notes
    }
