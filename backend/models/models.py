import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.database import Base

# Enums
class UserRole(str, enum.Enum):
    student = "student"
    counselor = "counselor"
    admin = "admin"

class VerificationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"

class ConversationStatus(str, enum.Enum):
    active = "active"
    closed = "closed"

class AssessmentType(str, enum.Enum):
    stress = "stress"
    anxiety = "anxiety"
    depression = "depression"
    peer_pressure = "peer_pressure"

class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class CrisisSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class CrisisStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    resolved = "resolved"
    false_alarm = "false_alarm"

class ReportStatus(str, enum.Enum):
    pending = "pending"
    reviewed = "reviewed"
    action_taken = "action_taken"
    dismissed = "dismissed"

# Base Mixin for Timestamps
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# Models
class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    anonymous_id = Column(String(50), unique=True, nullable=False, index=True)
    college_name = Column(String(255), nullable=True)
    academic_year = Column(String(50), nullable=True)
    preferred_language = Column(String(50), default="English")
    
    user = relationship("User", backref="student_profile")

class CounselorProfile(Base, TimestampMixin):
    __tablename__ = "counselor_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    specialization = Column(String(255), nullable=True)
    qualification = Column(String(255), nullable=True)
    experience_years = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.pending, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", backref="counselor_profile")

class CounselorVerificationDocument(Base):
    __tablename__ = "counselor_verification_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    counselor_id = Column(UUID(as_uuid=True), ForeignKey("counselor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    document_url = Column(String(500), nullable=False)
    document_type = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    review_notes = Column(Text, nullable=True)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.pending)

class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    counselor_id = Column(UUID(as_uuid=True), ForeignKey("counselor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.pending, index=True)
    session_notes = Column(Text, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('student_id', 'counselor_id', 'appointment_datetime', name='unique_appointment_slot'),
    )

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    counselor_id = Column(UUID(as_uuid=True), ForeignKey("counselor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.active)
    
    __table_args__ = (
        Index('idx_unique_active_conversation', 'student_id', 'counselor_id', unique=True, postgresql_where=(status == 'active')),
    )

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

class MentalHealthAssessment(Base):
    __tablename__ = "mental_health_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_type = Column(Enum(AssessmentType), nullable=False)
    score = Column(Integer, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class CrisisAlert(Base):
    __tablename__ = "crisis_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    counselor_id = Column(UUID(as_uuid=True), ForeignKey("counselor_profiles.id", ondelete="SET NULL"), nullable=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("mental_health_assessments.id", ondelete="SET NULL"), nullable=True)
    severity = Column(Enum(CrisisSeverity), nullable=False, index=True)
    status = Column(Enum(CrisisStatus), default=CrisisStatus.pending, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class CommunityPost(Base, TimestampMixin):
    __tablename__ = "community_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    likes_count = Column(Integer, default=0)

class PostComment(Base):
    __tablename__ = "post_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    reporter_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.pending, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_reports_target', 'target_type', 'target_id'),
    )

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_notifications_is_read', 'user_id', 'is_read'),
    )

class VerificationOTP(Base):
    __tablename__ = "verification_otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    target = Column(String(255), nullable=False, index=True) # Email or Phone
    contact_type = Column(String(50), nullable=False) # "email" or "phone"
    otp_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index('idx_verification_target', 'target'),
    )
