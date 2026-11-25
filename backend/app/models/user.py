from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="student", nullable=False) # "student" or "working_professional"
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    roadmap_enrollments = relationship("RoadmapEnrollment", cascade="all, delete-orphan")
    skills = relationship("UserSkill", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    daily_capacity_minutes = Column(Integer, default=300, nullable=False) # 5.0h default cap
    weekly_capacity_hours = Column(Integer, default=25, nullable=False)
    timezone = Column(String(100), default="UTC", nullable=False)
    focus_domains = Column(Text, default="Software Engineering,AI", nullable=False) # Comma-separated domains
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    preferences_json = Column(JSON().with_variant(postgresql.JSONB, "postgresql"), default=dict, nullable=True)

    user = relationship("User", back_populates="profile")
