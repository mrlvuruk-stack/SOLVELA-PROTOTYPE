from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

class MilestoneCreate(BaseModel):
    title: str
    due_date: Optional[datetime] = None

class MilestoneResponse(BaseModel):
    id: str
    title: str
    due_date: Optional[datetime] = None
    is_completed: bool

class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "career"
    target_date: Optional[datetime] = None
    milestones: Optional[List[MilestoneCreate]] = None

class GoalResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: str
    target_date: Optional[datetime] = None
    status: str
    progress_pct: int
    created_at: datetime
    milestones: List[MilestoneResponse] = []

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int = 30
    priority: int = 2
    energy_level: int = 3
    goal_id: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    duration_minutes: int
    priority: int
    energy_level: int
    goal_id: Optional[str] = None
    status: str
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    due_date: Optional[datetime] = None

class TopRockItem(BaseModel):
    id: str
    title: str
    duration_minutes: int
    priority: int
    status: str

class CapacityUsage(BaseModel):
    scheduled_minutes: int
    daily_capacity_minutes: int
    utilization_pct: float
    burnout_risk: str # "low", "optimal", "caution", "overloaded"

class TodayDashboardResponse(BaseModel):
    date: str
    top_rocks: List[TopRockItem]
    capacity: CapacityUsage
    pomodoro_sessions_suggested: int
    tasks: List[TaskResponse]

class OpportunityResponse(BaseModel):
    id: str
    title: str
    category: str
    organization: str
    location: str
    url: str
    deadline: Optional[datetime] = None
    eligibility: Optional[str] = None
    description: Optional[str] = None
