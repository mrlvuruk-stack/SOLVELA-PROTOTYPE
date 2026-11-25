from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    domain = Column(String(100), index=True, nullable=False) # e.g. "Software Engineering", "AI"
    description = Column(Text, nullable=False)
    difficulty_level = Column(String(50), default="intermediate", nullable=False) # beginner, intermediate, advanced
    estimated_hours = Column(Integer, default=40, nullable=False)
    is_official = Column(Boolean, default=True, nullable=False)
    created_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    nodes = relationship("RoadmapNode", back_populates="roadmap", cascade="all, delete-orphan", order_by="RoadmapNode.order_index")
    enrollments = relationship("RoadmapEnrollment", back_populates="roadmap", cascade="all, delete-orphan")


class RoadmapNode(Base):
    __tablename__ = "roadmap_nodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id = Column(String, ForeignKey("roadmaps.id", ondelete="CASCADE"), index=True, nullable=False)
    parent_node_id = Column(String, ForeignKey("roadmap_nodes.id", ondelete="SET NULL"), nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    estimated_minutes = Column(Integer, default=60, nullable=False)
    key_takeaways_json = Column(JSON().with_variant(postgresql.JSONB, "postgresql"), default=list, nullable=False)
    resources_json = Column(JSON().with_variant(postgresql.JSONB, "postgresql"), default=list, nullable=False) # [{title, url, type, est_min}]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    roadmap = relationship("Roadmap", back_populates="nodes")
    parent = relationship("RoadmapNode", remote_side=[id], backref="children")
    assessments = relationship("Assessment", back_populates="node", cascade="all, delete-orphan")
    user_progress = relationship("UserNodeProgress", back_populates="node", cascade="all, delete-orphan")


class RoadmapEnrollment(Base):
    __tablename__ = "roadmap_enrollments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    roadmap_id = Column(String, ForeignKey("roadmaps.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(String(50), default="in_progress", nullable=False) # "in_progress", "completed", "paused"
    completed_nodes_count = Column(Integer, default=0, nullable=False)
    progress_pct = Column(Integer, default=0, nullable=False) # 0 to 100
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_activity_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    roadmap = relationship("Roadmap", back_populates="enrollments")


class UserNodeProgress(Base):
    __tablename__ = "user_node_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    node_id = Column(String, ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(String(50), default="completed", nullable=False) # "available", "completed"
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    notes = Column(Text, nullable=True)

    node = relationship("RoadmapNode", back_populates="user_progress")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False) # e.g. "Languages", "Backend", "AI & ML", "Architecture"
    description = Column(Text, nullable=True)

    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    level = Column(String(50), default="beginner", nullable=False) # "beginner", "intermediate", "advanced", "mastery"
    points = Column(Integer, default=10, nullable=False)
    last_practiced_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    skill = relationship("Skill", back_populates="user_skills")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    passing_score_pct = Column(Integer, default=70, nullable=False)
    questions_json = Column(JSON().with_variant(postgresql.JSONB, "postgresql"), default=list, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    node = relationship("RoadmapNode", back_populates="assessments")
    attempts = relationship("UserAssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class UserAssessmentAttempt(Base):
    __tablename__ = "user_assessment_attempts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    assessment_id = Column(String, ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False)
    score_pct = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    answers_json = Column(JSON().with_variant(postgresql.JSONB, "postgresql"), default=dict, nullable=False)
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    assessment = relationship("Assessment", back_populates="attempts")
