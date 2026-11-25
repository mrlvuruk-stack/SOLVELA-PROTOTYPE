from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.goal import Goal
from app.models.task import TaskModel
from app.schemas.domain import TaskCreate, TaskResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    priority: Optional[int] = None
    energy_level: Optional[int] = None
    goal_id: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None

@router.get("", response_model=List[TaskResponse])
async def list_tasks(status_filter: str = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(TaskModel).where(TaskModel.user_id == user.id)
    if status_filter:
        query = query.where(TaskModel.status == status_filter)
    query = query.order_by(TaskModel.priority.desc(), TaskModel.created_at.asc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [
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
        for t in tasks
    ]

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Strict User Ownership Check
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or unauthorized access")
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        duration_minutes=task.duration_minutes,
        priority=task.priority,
        energy_level=task.energy_level,
        goal_id=task.goal_id,
        status=task.status,
        scheduled_start=task.scheduled_start,
        scheduled_end=task.scheduled_end,
        due_date=task.due_date
    )

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(req: TaskCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # User Ownership & Goal Isolation Check
    if req.goal_id:
        goal_res = await db.execute(select(Goal).where(Goal.id == req.goal_id, Goal.user_id == user.id))
        if not goal_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Referenced goal does not belong to the authenticated user"
            )

    task = TaskModel(
        user_id=user.id,
        goal_id=req.goal_id,
        title=req.title,
        description=req.description,
        duration_minutes=req.duration_minutes,
        priority=req.priority,
        energy_level=req.energy_level,
        due_date=req.due_date,
        status="pending"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        duration_minutes=task.duration_minutes,
        priority=task.priority,
        energy_level=task.energy_level,
        goal_id=task.goal_id,
        status=task.status,
        scheduled_start=task.scheduled_start,
        scheduled_end=task.scheduled_end,
        due_date=task.due_date
    )

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, req: TaskUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or unauthorized access")

    if req.goal_id is not None:
        if req.goal_id:
            goal_res = await db.execute(select(Goal).where(Goal.id == req.goal_id, Goal.user_id == user.id))
            if not goal_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Referenced goal does not belong to the authenticated user"
                )
        task.goal_id = req.goal_id

    if req.title is not None:
        task.title = req.title
    if req.description is not None:
        task.description = req.description
    if req.duration_minutes is not None:
        task.duration_minutes = req.duration_minutes
    if req.priority is not None:
        task.priority = req.priority
    if req.energy_level is not None:
        task.energy_level = req.energy_level
    if req.status is not None:
        task.status = req.status
    if req.due_date is not None:
        task.due_date = req.due_date

    await db.commit()
    await db.refresh(task)
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        duration_minutes=task.duration_minutes,
        priority=task.priority,
        energy_level=task.energy_level,
        goal_id=task.goal_id,
        status=task.status,
        scheduled_start=task.scheduled_start,
        scheduled_end=task.scheduled_end,
        due_date=task.due_date
    )

@router.put("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or unauthorized access")
        
    task.status = "completed"
    await db.commit()
    await db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        duration_minutes=task.duration_minutes,
        priority=task.priority,
        energy_level=task.energy_level,
        goal_id=task.goal_id,
        status=task.status,
        scheduled_start=task.scheduled_start,
        scheduled_end=task.scheduled_end,
        due_date=task.due_date
    )

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or unauthorized access")
    await db.delete(task)
    await db.commit()
    return None
