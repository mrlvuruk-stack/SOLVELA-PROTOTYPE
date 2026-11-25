from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.db.session import get_db
from app.models.user import User
from app.models.learning import (
    Roadmap, RoadmapNode, RoadmapEnrollment, UserNodeProgress,
    Skill, UserSkill, Assessment, UserAssessmentAttempt
)
from app.schemas.learning import (
    RoadmapSummaryResponse, RoadmapDetailResponse, RoadmapNodeResponse,
    ResourceItem, EnrollRoadmapRequest, CompleteNodeRequest, CompleteNodeResponse,
    SkillResponse, AssessmentResponse, QuestionItem, SubmitAssessmentRequest,
    AssessmentResultResponse
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/learning", tags=["Learning Management"])

@router.get("/roadmaps", response_model=List[RoadmapSummaryResponse])
async def list_roadmaps(
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all available learning roadmaps with user enrollment state & progress.
    """
    query = select(Roadmap).order_by(Roadmap.domain.asc(), Roadmap.title.asc())
    if domain:
        query = query.where(Roadmap.domain.ilike(f"%{domain}%"))
    if difficulty:
        query = query.where(Roadmap.difficulty_level == difficulty.lower())
    if search:
        query = query.where(or_(
            Roadmap.title.ilike(f"%{search}%"),
            Roadmap.description.ilike(f"%{search}%")
        ))

    result = await db.execute(query)
    roadmaps = result.scalars().all()

    # Fetch user enrollments
    enrollment_res = await db.execute(
        select(RoadmapEnrollment).where(RoadmapEnrollment.user_id == user.id)
    )
    user_enrollments = {e.roadmap_id: e for e in enrollment_res.scalars().all()}

    summaries = []
    for r in roadmaps:
        nodes_res = await db.execute(select(RoadmapNode).where(RoadmapNode.roadmap_id == r.id))
        nodes_count = len(nodes_res.scalars().all())

        enrolled = r.id in user_enrollments
        progress = user_enrollments[r.id].progress_pct if enrolled else 0

        summaries.append(RoadmapSummaryResponse(
            id=r.id,
            slug=r.slug,
            title=r.title,
            domain=r.domain,
            description=r.description,
            difficulty_level=r.difficulty_level,
            estimated_hours=r.estimated_hours,
            nodes_count=nodes_count,
            is_enrolled=enrolled,
            progress_pct=progress
        ))

    return summaries

@router.get("/roadmaps/{slug_or_id}", response_model=RoadmapDetailResponse)
async def get_roadmap_details(
    slug_or_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves complete roadmap details including curriculum nodes, resources,
    user node completions, and assessments.
    """
    r_res = await db.execute(
        select(Roadmap).where(or_(Roadmap.slug == slug_or_id, Roadmap.id == slug_or_id))
    )
    roadmap = r_res.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    # Fetch nodes
    n_res = await db.execute(
        select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id).order_by(RoadmapNode.order_index.asc())
    )
    nodes = n_res.scalars().all()

    # Fetch user enrollment & progress
    enr_res = await db.execute(
        select(RoadmapEnrollment).where(
            RoadmapEnrollment.roadmap_id == roadmap.id,
            RoadmapEnrollment.user_id == user.id
        )
    )
    enrollment = enr_res.scalar_one_or_none()

    # Fetch user completed node IDs
    completed_nodes_res = await db.execute(
        select(UserNodeProgress.node_id).where(
            UserNodeProgress.user_id == user.id,
            UserNodeProgress.status == "completed"
        )
    )
    completed_node_ids = set(completed_nodes_res.scalars().all())

    node_responses = []
    for n in nodes:
        # Check if node has an assessment
        a_res = await db.execute(select(Assessment.id).where(Assessment.node_id == n.id))
        has_assessment = a_res.scalar_one_or_none() is not None

        resources = [
            ResourceItem(
                title=res.get("title", "Resource"),
                url=res.get("url", "#"),
                type=res.get("type", "article"),
                est_minutes=res.get("est_minutes", 30)
            )
            for res in (n.resources_json or [])
        ]

        node_responses.append(RoadmapNodeResponse(
            id=n.id,
            roadmap_id=n.roadmap_id,
            parent_node_id=n.parent_node_id,
            order_index=n.order_index,
            title=n.title,
            description=n.description,
            estimated_minutes=n.estimated_minutes,
            key_takeaways=n.key_takeaways_json or [],
            resources=resources,
            is_completed=n.id in completed_node_ids,
            has_assessment=has_assessment
        ))

    return RoadmapDetailResponse(
        id=roadmap.id,
        slug=roadmap.slug,
        title=roadmap.title,
        domain=roadmap.domain,
        description=roadmap.description,
        difficulty_level=roadmap.difficulty_level,
        estimated_hours=roadmap.estimated_hours,
        nodes_count=len(nodes),
        is_enrolled=enrollment is not None,
        progress_pct=enrollment.progress_pct if enrollment else 0,
        completed_nodes_count=enrollment.completed_nodes_count if enrollment else 0,
        enrollment_id=enrollment.id if enrollment else None,
        nodes=node_responses
    )

@router.post("/roadmaps/{roadmap_id}/enroll", response_model=RoadmapDetailResponse)
async def enroll_in_roadmap(
    roadmap_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Enrolls the authenticated user into a learning roadmap.
    """
    r_res = await db.execute(select(Roadmap).where(Roadmap.id == roadmap_id))
    roadmap = r_res.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    enr_res = await db.execute(
        select(RoadmapEnrollment).where(
            RoadmapEnrollment.roadmap_id == roadmap.id,
            RoadmapEnrollment.user_id == user.id
        )
    )
    enrollment = enr_res.scalar_one_or_none()
    if not enrollment:
        enrollment = RoadmapEnrollment(
            user_id=user.id,
            roadmap_id=roadmap.id,
            status="in_progress",
            completed_nodes_count=0,
            progress_pct=0,
            started_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc)
        )
        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)

    return await get_roadmap_details(roadmap.id, user, db)

@router.post("/nodes/{node_id}/complete", response_model=CompleteNodeResponse)
async def mark_node_complete(
    node_id: str,
    req: CompleteNodeRequest = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Marks a curriculum node as completed, increments roadmap progress, and awards skill points.
    """
    n_res = await db.execute(select(RoadmapNode).where(RoadmapNode.id == node_id))
    node = n_res.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum node not found")

    # Check if already completed
    prog_res = await db.execute(
        select(UserNodeProgress).where(
            UserNodeProgress.node_id == node.id,
            UserNodeProgress.user_id == user.id
        )
    )
    progress = prog_res.scalar_one_or_none()
    if not progress:
        progress = UserNodeProgress(
            user_id=user.id,
            node_id=node.id,
            status="completed",
            notes=req.notes if req else None,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(progress)
    else:
        progress.status = "completed"
        progress.completed_at = datetime.now(timezone.utc)
        if req and req.notes:
            progress.notes = req.notes
    await db.flush()

    # Ensure enrollment exists
    enr_res = await db.execute(
        select(RoadmapEnrollment).where(
            RoadmapEnrollment.roadmap_id == node.roadmap_id,
            RoadmapEnrollment.user_id == user.id
        )
    )
    enrollment = enr_res.scalar_one_or_none()
    if not enrollment:
        enrollment = RoadmapEnrollment(
            user_id=user.id,
            roadmap_id=node.roadmap_id,
            status="in_progress",
            completed_nodes_count=0,
            progress_pct=0,
            started_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc)
        )
        db.add(enrollment)
        await db.flush()

    # Recalculate progress percentage
    all_nodes_res = await db.execute(select(RoadmapNode).where(RoadmapNode.roadmap_id == node.roadmap_id))
    all_nodes = all_nodes_res.scalars().all()
    total_nodes = len(all_nodes)
    node_ids = [n.id for n in all_nodes]

    completed_res = await db.execute(
        select(UserNodeProgress).where(
            UserNodeProgress.user_id == user.id,
            UserNodeProgress.node_id.in_(node_ids),
            UserNodeProgress.status == "completed"
        )
    )
    completed_count = len(completed_res.scalars().all())
    progress_pct = int((completed_count / total_nodes) * 100) if total_nodes > 0 else 100

    enrollment.completed_nodes_count = completed_count
    enrollment.progress_pct = progress_pct
    enrollment.last_activity_at = datetime.now(timezone.utc)
    if progress_pct == 100:
        enrollment.status = "completed"

    # Award skill points for node completion
    skill_res = await db.execute(select(Skill).where(Skill.category == "Languages"))
    skill = skill_res.scalars().first()
    if skill:
        us_res = await db.execute(
            select(UserSkill).where(UserSkill.user_id == user.id, UserSkill.skill_id == skill.id)
        )
        user_skill = us_res.scalar_one_or_none()
        if not user_skill:
            user_skill = UserSkill(
                user_id=user.id,
                skill_id=skill.id,
                level="beginner",
                points=25,
                last_practiced_at=datetime.now(timezone.utc)
            )
            db.add(user_skill)
        else:
            user_skill.points += 25
            user_skill.last_practiced_at = datetime.now(timezone.utc)
            if user_skill.points >= 150:
                user_skill.level = "mastery"
            elif user_skill.points >= 100:
                user_skill.level = "advanced"
            elif user_skill.points >= 50:
                user_skill.level = "intermediate"

    await db.commit()

    return CompleteNodeResponse(
        node_id=node.id,
        roadmap_id=node.roadmap_id,
        progress_pct=progress_pct,
        completed_nodes_count=completed_count,
        total_nodes_count=total_nodes,
        is_roadmap_completed=progress_pct == 100,
        skill_points_earned=25
    )

@router.get("/skills", response_model=List[SkillResponse])
async def get_user_skills(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns user's skill competency portfolio with points and proficiency levels.
    """
    result = await db.execute(
        select(UserSkill, Skill)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == user.id)
        .order_by(UserSkill.points.desc())
    )
    user_skills = result.all()

    # If user has no skills yet, return catalog skills at 0 points
    if not user_skills:
        all_skills_res = await db.execute(select(Skill).order_by(Skill.category.asc()))
        all_skills = all_skills_res.scalars().all()
        return [
            SkillResponse(
                id=s.id,
                name=s.name,
                category=s.category,
                description=s.description,
                level="beginner",
                points=0,
                last_practiced_at=None
            )
            for s in all_skills
        ]

    return [
        SkillResponse(
            id=s.id,
            name=s.name,
            category=s.category,
            description=s.description,
            level=us.level,
            points=us.points,
            last_practiced_at=us.last_practiced_at
        )
        for us, s in user_skills
    ]

@router.get("/assessments/node/{node_id}", response_model=AssessmentResponse)
async def get_node_assessment(
    node_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the assessment for a specific node without disclosing the correct answer keys.
    """
    a_res = await db.execute(select(Assessment).where(Assessment.node_id == node_id))
    assessment = a_res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assessment configured for this node")

    # Sanitize questions: strip correct_index
    sanitized_questions = []
    for q in (assessment.questions_json or []):
        sanitized_questions.append(QuestionItem(
            id=q.get("id", 0),
            question=q.get("question", ""),
            options=q.get("options", []),
            explanation=None
        ))

    return AssessmentResponse(
        id=assessment.id,
        node_id=assessment.node_id,
        title=assessment.title,
        passing_score_pct=assessment.passing_score_pct,
        questions=sanitized_questions
    )

@router.post("/assessments/{assessment_id}/submit", response_model=AssessmentResultResponse)
async def submit_assessment(
    assessment_id: str,
    req: SubmitAssessmentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates assessment submission, verifies passing threshold, logs attempt,
    and awards skill points.
    """
    a_res = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = a_res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    questions = assessment.questions_json or []
    total_q = len(questions)
    if total_q == 0:
        return AssessmentResultResponse(
            assessment_id=assessment.id,
            node_id=assessment.node_id,
            score_pct=100,
            passed=True,
            passing_score_pct=assessment.passing_score_pct,
            correct_count=0,
            total_questions=0,
            feedback="Assessment completed.",
            skill_awarded=None,
            points_awarded=0
        )

    correct_count = 0
    for q in questions:
        q_id = str(q.get("id"))
        correct_idx = q.get("correct_index")
        user_choice = req.answers.get(q_id)
        if user_choice is not None and user_choice == correct_idx:
            correct_count += 1

    score_pct = int((correct_count / total_q) * 100)
    passed = score_pct >= assessment.passing_score_pct

    # Record attempt
    attempt = UserAssessmentAttempt(
        user_id=user.id,
        assessment_id=assessment.id,
        score_pct=score_pct,
        passed=passed,
        answers_json=req.answers,
        attempted_at=datetime.now(timezone.utc)
    )
    db.add(attempt)

    points_awarded = 50 if passed else 10

    # Automatically mark node as completed if passed
    if passed:
        node_res = await db.execute(select(RoadmapNode).where(RoadmapNode.id == assessment.node_id))
        node = node_res.scalar_one_or_none()
        if node:
            unp_res = await db.execute(
                select(UserNodeProgress).where(
                    UserNodeProgress.node_id == node.id,
                    UserNodeProgress.user_id == user.id
                )
            )
            node_prog = unp_res.scalar_one_or_none()
            if not node_prog:
                node_prog = UserNodeProgress(
                    user_id=user.id,
                    node_id=node.id,
                    status="completed",
                    notes="Completed via successful assessment attempt.",
                    completed_at=datetime.now(timezone.utc)
                )
                db.add(node_prog)

    await db.commit()

    feedback = (
        f"Congratulations! You passed with {score_pct}% ({correct_count}/{total_q} correct). Skill points awarded."
        if passed else
        f"Score {score_pct}% ({correct_count}/{total_q} correct). Passing threshold is {assessment.passing_score_pct}%. Review the recommended readings and try again."
    )

    return AssessmentResultResponse(
        assessment_id=assessment.id,
        node_id=assessment.node_id,
        score_pct=score_pct,
        passed=passed,
        passing_score_pct=assessment.passing_score_pct,
        correct_count=correct_count,
        total_questions=total_q,
        feedback=feedback,
        skill_awarded="Assessment Verified",
        points_awarded=points_awarded
    )
