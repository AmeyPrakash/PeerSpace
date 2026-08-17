"""
PeerSpace Counselor Application Manager
Handles counselor applications with review workflow.
"""

import time
import uuid
import json
import os
from collections import OrderedDict
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

@dataclass
class CounselorApplicationEntry:
    """Represents a counselor application."""
    application_id: str
    full_name: str
    email: str
    phone: str
    highest_degree: str
    degree_field: str
    university: str
    graduation_year: int
    certifications: str
    years_of_experience: int
    current_role: str
    specializations: str
    motivation: str
    background_info: str
    submitted_at: float
    status: str = "pending"  # pending, under_review, approved, rejected
    reviewed_at: float = None
    reviewer_notes: str = None
    

# In-memory storage for applications
applications: OrderedDict[str, CounselorApplicationEntry] = OrderedDict()
MAX_APPLICATIONS = 1000

DB_FILE = os.path.join(os.path.dirname(__file__), "counselor_applications.json")

def load_applications():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                for item in data:
                    app = CounselorApplicationEntry(**item)
                    applications[app.application_id] = app
        except Exception as e:
            print(f"Error loading applications: {e}")

def save_applications():
    try:
        with open(DB_FILE, "w") as f:
            json.dump([asdict(app) for app in applications.values()], f, indent=2)
    except Exception as e:
        print(f"Error saving applications: {e}")

load_applications()

def submit_application(
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
    
    # Check if max applications reached
    if len(applications) >= MAX_APPLICATIONS:
        # Remove oldest application
        applications.popitem(last=False)
    
    # Create application entry
    application = CounselorApplicationEntry(
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
        submitted_at=time.time()
    )
    
    applications[app_id] = application
    save_applications()
    return app_id, "Application submitted successfully"


def get_application(application_id: str) -> Dict:
    """Retrieve application by ID."""
    if application_id in applications:
        app = applications[application_id]
        return asdict(app)
    return None


def get_all_applications(status: str = None) -> List[Dict]:
    """
    Get all applications, optionally filtered by status.
    
    Args:
        status: Filter by status (pending, under_review, approved, rejected)
        
    Returns:
        List of application dictionaries
    """
    result = []
    for app in applications.values():
        if status is None or app.status == status:
            result.append(asdict(app))
    return result


def update_application_status(
    application_id: str,
    new_status: str,
    reviewer_notes: str = None
) -> bool:
    """
    Update application status (for admin approval workflow).
    
    Args:
        application_id: ID of application to update
        new_status: New status (under_review, approved, rejected)
        reviewer_notes: Notes from reviewer/admin
        
    Returns:
        True if successful, False if not found
    """
    if application_id not in applications:
        return False
    
    app = applications[application_id]
    app.status = new_status
    app.reviewed_at = time.time()
    if reviewer_notes:
        app.reviewer_notes = reviewer_notes
    
    save_applications()
    return True


def get_application_stats() -> Dict:
    """Get statistics about applications."""
    stats = {
        "total_applications": len(applications),
        "pending": 0,
        "under_review": 0,
        "approved": 0,
        "rejected": 0
    }
    
    for app in applications.values():
        stats[app.status] = stats.get(app.status, 0) + 1
    
    return stats


def get_pending_applications() -> List[Dict]:
    """Get all pending applications (not yet reviewed)."""
    return get_all_applications(status="pending")


def get_approved_counselors() -> List[Dict]:
    """Get all approved counselor applications."""
    return get_all_applications(status="approved")
