from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from app.db.session import get_db
from app.models.user import User, UserProfile
from app.models.task import TaskModel
from app.services.scheduler import KnapsackScheduler, Task as AlgoTask, FreeInterval, ScheduleResult
from app.services.imtr import IMTRRecoveryEngine, OverdueTask as AlgoOverdueTask, IMTRResult
from app.api.deps import get_current_user_optional

router = APIRouter(prefix="/temporal", tags=["Temporal & Scheduling"])

scheduler_service = KnapsackScheduler(daily_capacity_cap_minutes=300)
imtr_service = IMTRRecoveryEngine(daily_capacity_cap_minutes=300)

class AutoScheduleRequest(BaseModel):
    task_count: Optional[int] = None
    use_persistent_tasks: bool = True
    available_hours_per_day: Optional[int] = None

@router.post("/auto-schedule")
async def run_auto_schedule(
    req: AutoScheduleRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    ref_time = datetime.now()
    daily_cap = 300
    
    # 1. Gather tasks
    tasks_to_schedule = []
    if user and req.use_persistent_tasks:
        # Fetch user's profile capacity
        prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
        prof = prof_res.scalar_one_or_none()
        if prof:
            daily_cap = prof.daily_capacity_minutes
            
        # Fetch user's real pending tasks
        task_res = await db.execute(
            select(TaskModel)
            .where(TaskModel.user_id == user.id, TaskModel.status == "pending")
            .order_by(TaskModel.priority.desc())
        )
        db_tasks = task_res.scalars().all()
        for t in db_tasks:
            tasks_to_schedule.append(AlgoTask(
                id=t.id,
                title=t.title,
                duration_minutes=t.duration_minutes,
                priority=t.priority,
                deadline=t.due_date,
                required_energy_level=t.energy_level
            ))
            
    # Fallback/Demo if no persistent tasks or unauthenticated
    if not tasks_to_schedule:
        count = req.task_count or 10
        tasks_to_schedule = [
            AlgoTask(id=f"task-{i}", title=f"Study Module Block #{i}", duration_minutes=45, priority=(i % 4) + 1)
            for i in range(count)
        ]
        
    # Standard free intervals across next 3 days
    intervals = []
    for d in range(3):
        day_base = ref_time + timedelta(days=d)
        intervals.extend([
            FreeInterval(start=day_base.replace(hour=9, minute=0, second=0), end=day_base.replace(hour=12, minute=0, second=0)),
            FreeInterval(start=day_base.replace(hour=14, minute=0, second=0), end=day_base.replace(hour=17, minute=0, second=0)),
        ])
        
    result: ScheduleResult = scheduler_service.schedule_multi_day(
        tasks=tasks_to_schedule,
        free_intervals=intervals,
        reference_time=ref_time,
        per_day_capacity_minutes=daily_cap
    )
    
    # Update persistent tasks status if real user
    if user and req.use_persistent_tasks:
        for p in result.placements:
            t_res = await db.execute(
                select(TaskModel).where(TaskModel.id == p.task_id, TaskModel.user_id == user.id)
            )
            t_obj = t_res.scalar_one_or_none()
            if t_obj:
                t_obj.scheduled_start = p.start
                t_obj.scheduled_end = p.end
                t_obj.status = "in_progress"
        await db.commit()
        
    return {
        "placements_count": len(result.placements),
        "unplaced_count": len(result.unplaced_tasks),
        "execution_time_ms": round(result.execution_time_ms, 2),
        "target_met": result.execution_time_ms < 350.0,
        "daily_allocated_minutes": {str(k): v for k, v in result.daily_allocated_minutes.items()},
        "placements": [
            {"id": p.task_id, "title": p.title, "start": p.start.isoformat(), "end": p.end.isoformat(), "duration_minutes": p.duration_minutes}
            for p in result.placements
        ],
        "unplaced_tasks": [
            {"id": u.task_id, "title": u.title, "duration_minutes": u.duration_minutes, "reason": u.reason}
            for u in result.unplaced_tasks
        ]
    }

class IMTRRequest(BaseModel):
    overdue_task_count: Optional[int] = None
    use_persistent_missed: bool = True

@router.post("/imtr/rebalance")
async def run_imtr_rebalance(
    req: IMTRRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    overdue_algo_tasks = []
    
    if user and req.use_persistent_missed:
        task_res = await db.execute(
            select(TaskModel)
            .where(TaskModel.user_id == user.id, TaskModel.status == "missed")
            .order_by(TaskModel.priority.desc())
        )
        db_tasks = task_res.scalars().all()
        for t in db_tasks:
            overdue_algo_tasks.append(AlgoOverdueTask(
                id=t.id,
                title=t.title,
                duration_minutes=t.duration_minutes,
                priority=t.priority
            ))
            
    if not overdue_algo_tasks:
        count = req.overdue_task_count or 5
        overdue_algo_tasks = [
            AlgoOverdueTask(id=f"overdue-{i}", title=f"Missed Assignment #{i}", duration_minutes=45, priority=(i % 4) + 1)
            for i in range(count)
        ]
        
    result: IMTRResult = imtr_service.rebalance_safe(
        overdue_tasks=overdue_algo_tasks,
        current_date=today,
        existing_daily_workloads={}
    )
    
    # Update persistent tasks status if real user
    if user and req.use_persistent_missed:
        for r in result.rebalanced_tasks:
            t_res = await db.execute(
                select(TaskModel).where(TaskModel.id == r.task_id, TaskModel.user_id == user.id)
            )
            t_obj = t_res.scalar_one_or_none()
            if t_obj:
                t_obj.due_date = datetime.combine(r.target_date, datetime.min.time())
                t_obj.status = "pending"
        for d in result.deferred_tasks:
            t_res = await db.execute(
                select(TaskModel).where(TaskModel.id == d.task_id, TaskModel.user_id == user.id)
            )
            t_obj = t_res.scalar_one_or_none()
            if t_obj:
                t_obj.status = "deferred"
        await db.commit()
        
    return {
        "rebalanced_count": len(result.rebalanced_tasks),
        "deferred_count": len(result.deferred_tasks),
        "execution_time_ms": round(result.execution_time_ms, 2),
        "target_met": result.execution_time_ms < 200.0,
        "rebalanced_tasks": [
            {"task_id": r.task_id, "target_date": r.target_date.isoformat(), "allocated_minutes": r.allocated_minutes}
            for r in result.rebalanced_tasks
        ],
        "deferred_tasks": [
            {"task_id": d.task_id, "title": d.title, "allocated_minutes": d.allocated_minutes, "reason": d.reason}
            for d in result.deferred_tasks
        ]
    }
