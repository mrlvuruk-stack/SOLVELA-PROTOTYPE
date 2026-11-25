from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.models.opportunity import OpportunityModel
from app.schemas.domain import OpportunityResponse

router = APIRouter(prefix="/opportunities", tags=["Opportunity Hub (DEC-06A)"])

INITIAL_SEED_OPPORTUNITIES = [
    {
        "title": "Google Summer of Code 2026",
        "category": "internship",
        "organization": "Google Open Source",
        "location": "Global Remote",
        "url": "https://summerofcode.withgoogle.com",
        "eligibility": "Open to post-secondary students and open-source beginners 18+",
        "description": "Global program focused on bringing new contributors into open source software development."
    },
    {
        "title": "Junior Full-Stack Engineer (AI Tooling)",
        "category": "job",
        "organization": "Veritas Applied AI Labs",
        "location": "Bengaluru / Remote",
        "url": "https://careers.veritaslabs.ai/junior-dev",
        "eligibility": "B.Tech/MCA/BS in CS or related field; proficiency in Python and TypeScript",
        "description": "Full-time position building high-throughput asynchronous inference pipelines and React interfaces."
    },
    {
        "title": "Smart India Hackathon 2026",
        "category": "hackathon",
        "organization": "Ministry of Education & AICTE",
        "location": "New Delhi / Hybrid",
        "url": "https://www.sih.gov.in",
        "eligibility": "Teams of 6 undergraduate/graduate college students",
        "description": "Nationwide initiative to provide students with a platform to solve pressing problems of society and industry."
    },
    {
        "title": "ICPC Regional Programming Contest",
        "category": "contest",
        "organization": "International Collegiate Programming Contest",
        "location": "Amritapuri / Kanpur",
        "url": "https://icpc.global",
        "eligibility": "Enrolled college students in eligible cohorts",
        "description": "Premier global algorithmic programming contest for university students."
    },
    {
        "title": "Reliance Foundation Undergraduate Scholarship",
        "category": "scholarship",
        "organization": "Reliance Foundation",
        "location": "India",
        "url": "https://www.scholarships.reliancefoundation.org",
        "eligibility": "First-year full-time undergraduate students across all streams",
        "description": "Up to ₹2,00,000 grant supporting scholars throughout their undergraduate studies."
    },
    {
        "title": "Mozilla Technology & Society Fellowship",
        "category": "grant_fellowship",
        "organization": "Mozilla Foundation",
        "location": "Remote",
        "url": "https://foundation.mozilla.org/fellowships",
        "eligibility": "Independent researchers, technologists, and open-web advocates",
        "description": "12-month fellowship with $60,000 stipend to investigate ethical AI and algorithmic transparency."
    },
    {
        "title": "IISc Summer Research Internship in AI & Robotics",
        "category": "research_post",
        "organization": "Indian Institute of Science",
        "location": "Bengaluru",
        "url": "https://iisc.ac.in/admissions/research-fellowships",
        "eligibility": "3rd or 4th year undergraduate engineering and science students",
        "description": "2-month funded research residency working alongside leading faculty in autonomous systems."
    },
    {
        "title": "DevFest National Technology Summit 2026",
        "category": "event",
        "organization": "Google Developer Groups",
        "location": "Hyderabad / Hybrid",
        "url": "https://devfest.gdg.community",
        "eligibility": "Developers, students, founders, and tech enthusiasts",
        "description": "Community-led technical conference featuring keynotes, codelabs, and career networking."
    }
]

@router.get("", response_model=List[OpportunityResponse])
async def list_opportunities(
    category: Optional[str] = Query(None, description="One of 8 approved categories: internship, job, hackathon, contest, scholarship, grant_fellowship, research_post, event"),
    db: AsyncSession = Depends(get_db)
):
    # Ensure canonical categories exist in the catalog only if empty
    count_check = await db.execute(select(func.count(OpportunityModel.id)))
    if (count_check.scalar() or 0) == 0:
        for item in INITIAL_SEED_OPPORTUNITIES:
            opp = OpportunityModel(
                title=item["title"],
                category=item["category"],
                organization=item["organization"],
                location=item["location"],
                url=item["url"],
                deadline=datetime.now(timezone.utc) + timedelta(days=45),
                eligibility=item["eligibility"],
                description=item["description"]
            )
            db.add(opp)
        await db.commit()
        
    query = select(OpportunityModel)
    if category:
        query = query.where(OpportunityModel.category == category.lower())
    query = query.order_by(OpportunityModel.created_at.desc())
    
    result = await db.execute(query)
    opps = result.scalars().all()
    
    return [
        OpportunityResponse(
            id=o.id,
            title=o.title,
            category=o.category,
            organization=o.organization,
            location=o.location,
            url=o.url,
            deadline=o.deadline,
            eligibility=o.eligibility,
            description=o.description
        )
        for o in opps
    ]

@router.post("/seed", status_code=201)
async def seed_opportunities(db: AsyncSession = Depends(get_db)):
    for item in INITIAL_SEED_OPPORTUNITIES:
        opp = OpportunityModel(
            title=item["title"],
            category=item["category"],
            organization=item["organization"],
            location=item["location"],
            url=item["url"],
            deadline=datetime.now(timezone.utc) + timedelta(days=45),
            eligibility=item["eligibility"],
            description=item["description"]
        )
        db.add(opp)
    await db.commit()
    return {"status": "seeded", "count": len(INITIAL_SEED_OPPORTUNITIES)}
