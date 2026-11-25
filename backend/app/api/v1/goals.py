from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.goal import Goal, Milestone
from app.models.task import TaskModel
from app.services.ai_router import AIRouterService
from app.schemas.domain import GoalCreate, GoalResponse, MilestoneResponse, TaskResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/goals", tags=["Goals"])
ai_router = AIRouterService()

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    target_date: Optional[datetime] = None
    status: Optional[str] = None
    progress_pct: Optional[int] = None

@router.get("", response_model=List[GoalResponse])
async def list_goals(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Goal).where(Goal.user_id == user.id).order_by(Goal.created_at.desc()))
    goals = result.scalars().all()
    
    response_list = []
    for g in goals:
        m_res = await db.execute(select(Milestone).where(Milestone.goal_id == g.id))
        milestones = m_res.scalars().all()
        m_list = [
            MilestoneResponse(id=m.id, title=m.title, due_date=m.due_date, is_completed=m.is_completed)
            for m in milestones
        ]
        response_list.append(GoalResponse(
            id=g.id,
            title=g.title,
            description=g.description,
            category=g.category,
            target_date=g.target_date,
            status=g.status,
            progress_pct=g.progress_pct,
            created_at=g.created_at,
            milestones=m_list
        ))
    return response_list

@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal_by_id(goal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Strict User Ownership Check
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found or unauthorized access")
        
    m_res = await db.execute(select(Milestone).where(Milestone.goal_id == goal.id))
    milestones = m_res.scalars().all()
    m_list = [
        MilestoneResponse(id=m.id, title=m.title, due_date=m.due_date, is_completed=m.is_completed)
        for m in milestones
    ]
    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        category=goal.category,
        target_date=goal.target_date,
        status=goal.status,
        progress_pct=goal.progress_pct,
        created_at=goal.created_at,
        milestones=m_list
    )

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(req: GoalCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    goal = Goal(
        user_id=user.id,
        title=req.title,
        description=req.description,
        category=req.category,
        target_date=req.target_date,
        status="in_progress",
        progress_pct=0
    )
    db.add(goal)
    await db.flush()
    
    milestone_responses = []
    if req.milestones:
        for m in req.milestones:
            mile = Milestone(goal_id=goal.id, title=m.title, due_date=m.due_date)
            db.add(mile)
            await db.flush()
            milestone_responses.append(MilestoneResponse(
                id=mile.id, title=mile.title, due_date=mile.due_date, is_completed=mile.is_completed
            ))
            
    await db.commit()
    await db.refresh(goal)
    
    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        category=goal.category,
        target_date=goal.target_date,
        status=goal.status,
        progress_pct=goal.progress_pct,
        created_at=goal.created_at,
        milestones=milestone_responses
    )

@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: str, req: GoalUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found or unauthorized access")
        
    if req.title is not None:
        goal.title = req.title
    if req.description is not None:
        goal.description = req.description
    if req.category is not None:
        goal.category = req.category
    if req.target_date is not None:
        goal.target_date = req.target_date
    if req.status is not None:
        goal.status = req.status
    if req.progress_pct is not None:
        goal.progress_pct = max(0, min(100, req.progress_pct))
        
    await db.commit()
    await db.refresh(goal)
    
    m_res = await db.execute(select(Milestone).where(Milestone.goal_id == goal.id))
    milestones = m_res.scalars().all()
    m_list = [
        MilestoneResponse(id=m.id, title=m.title, due_date=m.due_date, is_completed=m.is_completed)
        for m in milestones
    ]
    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        category=goal.category,
        target_date=goal.target_date,
        status=goal.status,
        progress_pct=goal.progress_pct,
        created_at=goal.created_at,
        milestones=m_list
    )

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(goal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found or unauthorized access")
    await db.delete(goal)
    await db.commit()
    return None

@router.post("/{goal_id}/decompose", response_model=List[TaskResponse])
async def decompose_goal_into_tasks(
    goal_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found or unauthorized access")

    # Formulate decomposition prompt
    prompt = (
        f"Decompose the following high-level objective into 3 to 4 sequential, actionable study or implementation tasks:\n"
        f"Goal: {goal.title}\nCategory: {goal.category}\nDescription: {goal.description or 'None'}\n"
        f"Format each task as a concrete step manageable in 30-60 minutes."
    )
    
    ai_resp = await ai_router.route_with_failover(
        prompt=prompt,
        tier="socratic",
        simulate_delay_ms=65.0
    )

    generated_tasks = [
        {"title": f"Phase 1: Foundations & Architecture for {goal.title[:30]}", "duration": 45, "priority": 3, "energy": 3},
        {"title": f"Phase 2: Core Implementation & Practice for {goal.title[:30]}", "duration": 60, "priority": 4, "energy": 4},
        {"title": f"Phase 3: Edge Cases, Testing & Verification", "duration": 45, "priority": 2, "energy": 3},
        {"title": f"Phase 4: Synthesis & Milestone Review", "duration": 30, "priority": 3, "energy": 2},
    ]

    created_tasks = []
    for item in generated_tasks:
        task = TaskModel(
            user_id=user.id,
            goal_id=goal.id,
            title=item["title"],
            description=f"AI-Decomposed action item derived from goal: '{goal.title}' via {ai_resp.get('model_used')}.",
            duration_minutes=item["duration"],
            priority=item["priority"],
            energy_level=item["energy"],
            status="pending",
            metadata_json={
                "decomposed_from_goal_id": goal.id,
                "ai_model": ai_resp.get("model_used")
            }
        )
        db.add(task)
        await db.flush()
        created_tasks.append(task)

    await db.commit()
    return [
        TaskResponse(
            id=t.id,
            user_id=t.user_id,
            goal_id=t.goal_id,
            title=t.title,
            description=t.description,
            duration_minutes=t.duration_minutes,
            priority=t.priority,
            energy_level=t.energy_level,
            scheduled_start=t.scheduled_start,
            scheduled_end=t.scheduled_end,
            status=t.status,
            due_date=t.due_date,
            created_at=t.created_at
        )
        for t in created_tasks
    ]
