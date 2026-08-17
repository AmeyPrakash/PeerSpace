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

class VoiceEscalatePayload(BaseModel):
    session_id: str
    alias: str
    peer_alias: Optional[str] = "Peer"
    reason: Optional[str] = "Student requested counselor intervention during peer voice chat."
