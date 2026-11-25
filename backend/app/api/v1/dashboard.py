from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from typing import List
from app.db.session import get_db
from app.models.user import User, UserProfile
from app.models.task import TaskModel
from app.schemas.domain import TodayDashboardResponse, TopRockItem, CapacityUsage, TaskResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/today", response_model=TodayDashboardResponse)
async def get_today_dashboard(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 1. Fetch user's profile to get configured daily capacity
    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = prof_res.scalar_one_or_none()
    daily_cap = profile.daily_capacity_minutes if profile else 300
    
    # 2. Fetch pending or in-progress tasks ordered by priority descending
    task_res = await db.execute(
        select(TaskModel)
        .where(TaskModel.user_id == user.id)
        .order_by(TaskModel.priority.desc(), TaskModel.created_at.asc())
    )
    all_tasks = task_res.scalars().all()
    
    # Top 3 Rocks: 3 highest priority pending tasks
    pending_tasks = [t for t in all_tasks if t.status != "completed"]
    top_rocks_models = pending_tasks[:3]
    top_rocks = [
        TopRockItem(
            id=t.id,
            title=t.title,
            duration_minutes=t.duration_minutes,
            priority=t.priority,
            status=t.status
        )
        for t in top_rocks_models
    ]
    
    # Compute total scheduled minutes for today
    scheduled_minutes = sum(t.duration_minutes for t in all_tasks if t.status in ("in_progress", "completed"))
    utilization_pct = round((scheduled_minutes / max(1, daily_cap)) * 100.0, 1)
    
    # Burnout risk calculation
    if utilization_pct <= 60.0:
        burnout_risk = "low"
    elif utilization_pct <= 85.0:
        burnout_risk = "optimal"
    elif utilization_pct <= 100.0:
        burnout_risk = "caution"
    else:
        burnout_risk = "overloaded"
        
    capacity_usage = CapacityUsage(
        scheduled_minutes=scheduled_minutes,
        daily_capacity_minutes=daily_cap,
        utilization_pct=utilization_pct,
        burnout_risk=burnout_risk
    )
    
    # Suggested 25-min Pomodoro sessions
    pomodoro_suggested = max(1, scheduled_minutes // 25)
    
    tasks_response = [
        TaskResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            duration_minutes=t.duration_minutes,
            priority=t.priority,
            energy_level=t.energy_level,
            goal_id=t.goal_id,
            status=t.status,
            scheduled_start=t.scheduled_start,
            scheduled_end=t.scheduled_end,
            due_date=t.due_date
        )
        for t in all_tasks
    ]
    
    return TodayDashboardResponse(
        date=date.today().isoformat(),
        top_rocks=top_rocks,
        capacity=capacity_usage,
        pomodoro_sessions_suggested=pomodoro_suggested,
        tasks=tasks_response
    )
