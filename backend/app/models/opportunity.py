from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects import postgresql
from datetime import datetime, timezone
import uuid
from app.db.session import Base

class OpportunityModel(Base):
    """
    DEC-06A Canonical Opportunity Model across 8 approved categories:
    1. Internships
    2. Jobs
    3. Hackathons
    4. Contests
    5. Scholarships
    6. Grants & Fellowships
    7. Research Posts
    8. Events
    """
    __tablename__ = "opportunities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True) # internship, job, hackathon, contest, scholarship, grant_fellowship, research_post, event
    organization = Column(String(255), nullable=False)
    location = Column(String(255), default="Remote", nullable=False)
    url = Column(String(512), nullable=False)
    deadline = Column(DateTime, nullable=True)
    eligibility = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(JSON().with_variant(postgresql.JSONB, "postgresql"), default=dict, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
