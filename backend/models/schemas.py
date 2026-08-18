"""
PeerSpace Data Models & Request/Response Schemas
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class StudentAuthPayload(BaseModel):
    session_id: Optional[str] = None
    alias: Optional[str] = None
    randomize: Optional[bool] = False

class AdminAuthPayload(BaseModel):
    passkey: str = Field(
        ..., 
        min_length=6,
        max_length=256,
        description="Campus counselor passkey (6-256 characters)"
    )
    
    @field_validator('passkey')
    @classmethod
    def validate_passkey(cls, v: str) -> str:
        """Ensure passkey contains only safe characters."""
        if not v or not v.strip():
            raise ValueError("Passkey cannot be empty or whitespace only")
        return v.strip()

class ChatPayload(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    alias: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty or whitespace only.")
        return cleaned

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[a-zA-Z0-9_-]{1,64}$", v):
            raise ValueError("Invalid session_id format.")
        return v

class ResetPayload(BaseModel):
    session_id: Optional[str] = None

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[a-zA-Z0-9_-]{1,64}$", v):
            raise ValueError("Invalid session_id format.")
        return v

class AlertActionPayload(BaseModel):
    action: str = Field(..., min_length=1)

class ChatInterventionPayload(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)

class VoiceEscalatePayload(BaseModel):
    session_id: str
    alias: str
    peer_alias: Optional[str] = "Peer"
    reason: Optional[str] = "Student requested counselor intervention during peer voice chat."

class ChatEscalatePayload(BaseModel):
    session_id: str
    alias: str
    reason: str
    mode: Optional[str] = "chat"

class CounselorApplicationPayload(BaseModel):
    """Counselor application form with educational and background details."""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    
    # Educational Qualifications
    highest_degree: str = Field(..., description="e.g., Bachelor's, Master's, PhD")
    degree_field: str = Field(..., description="e.g., Psychology, Counseling, Social Work")
    university: str = Field(..., description="Name of institution")
    graduation_year: int = Field(..., ge=1950, le=2026)
    
    # Certifications & Licenses
    certifications: Optional[str] = Field(None, max_length=500, description="Professional certifications/licenses")
    
    # Experience
    years_of_experience: int = Field(..., ge=0, le=100, description="Years of counseling/mental health experience")
    current_role: str = Field(..., max_length=100, description="Current professional position")
    
    # Specializations
    specializations: str = Field(..., max_length=500, description="Areas of expertise/specialization")
    
    # Background & Motivation
    motivation: str = Field(..., min_length=50, max_length=1000, description="Why you want to become a counselor")
    background_info: Optional[str] = Field(None, max_length=500, description="Additional background information")
    
    # Agreement
    terms_accepted: bool = Field(..., description="Accept terms and conditions")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.lower().strip()
    
    @field_validator('full_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

class CounselorApplicationResponse(BaseModel):
    """Response after counselor application submission."""
    status: str
    application_id: str
    message: str
    estimated_review_days: int = 5
