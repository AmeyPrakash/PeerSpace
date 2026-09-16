import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import AsyncSessionLocal, engine, Base
from backend.models.models import User, StudentProfile, CounselorProfile, UserRole
from backend.security import hash_passkey

async def seed_database():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    import secrets
    import os

    admin_pass = os.getenv("SEED_ADMIN_PASSWORD", secrets.token_urlsafe(16))
    counselor_pass = os.getenv("SEED_COUNSELOR_PASSWORD", secrets.token_urlsafe(16))
    student_pass = os.getenv("SEED_STUDENT_PASSWORD", secrets.token_urlsafe(16))

    async with AsyncSessionLocal() as session:
        # 1. Create an Admin
        admin_user = User(
            email="admin@peerspace.edu",
            password_hash=hash_passkey(admin_pass),
            role=UserRole.admin,
            email_verified=True
        )
        session.add(admin_user)
        
        # 2. Create a Counselor
        counselor_user = User(
            email="dr.smith@peerspace.edu",
            password_hash=hash_passkey(counselor_pass),
            role=UserRole.counselor,
            email_verified=True
        )
        session.add(counselor_user)
        await session.flush() # flush to get counselor_user.id
        
        counselor_profile = CounselorProfile(
            user_id=counselor_user.id,
            full_name="Dr. Sarah Smith",
            specialization="Anxiety & Stress Management",
            qualification="Ph.D. in Clinical Psychology",
            experience_years=8,
            bio="Dedicated to helping students navigate academic pressure.",
            verification_status="approved"
        )
        session.add(counselor_profile)
        
        # 3. Create a mock anonymous Student
        student_user = User(
            email="student1@anonymous.peerspace",
            password_hash=hash_passkey(student_pass),
            role=UserRole.student,
            email_verified=True
        )
        session.add(student_user)
        await session.flush()
        
        student_profile = StudentProfile(
            user_id=student_user.id,
            anonymous_id="BraveFalcon42",
            college_name="State University",
            academic_year="Sophomore"
        )
        session.add(student_profile)
        
        await session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())
