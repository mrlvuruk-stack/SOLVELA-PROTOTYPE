from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ResourceItem(BaseModel):
    title: str
    url: str
    type: str # "article", "documentation", "video", "interactive", "repository"
    est_minutes: int = 30

class RoadmapNodeResponse(BaseModel):
    id: str
    roadmap_id: str
    parent_node_id: Optional[str] = None
    order_index: int
    title: str
    description: str
    estimated_minutes: int
    key_takeaways: List[str] = []
    resources: List[ResourceItem] = []
    is_completed: bool = False
    has_assessment: bool = False

class RoadmapSummaryResponse(BaseModel):
    id: str
    slug: str
    title: str
    domain: str
    description: str
    difficulty_level: str
    estimated_hours: int
    nodes_count: int
    is_enrolled: bool = False
    progress_pct: int = 0

class RoadmapDetailResponse(RoadmapSummaryResponse):
    nodes: List[RoadmapNodeResponse] = []
    enrollment_id: Optional[str] = None
    completed_nodes_count: int = 0

class EnrollRoadmapRequest(BaseModel):
    roadmap_id: str

class CompleteNodeRequest(BaseModel):
    notes: Optional[str] = None

class CompleteNodeResponse(BaseModel):
    node_id: str
    roadmap_id: str
    progress_pct: int
    completed_nodes_count: int
    total_nodes_count: int
    is_roadmap_completed: bool
    skill_points_earned: int = 25

class SkillResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str] = None
    level: str # "beginner", "intermediate", "advanced", "mastery"
    points: int
    last_practiced_at: Optional[datetime] = None

class QuestionItem(BaseModel):
    id: int
    question: str
    options: List[str]
    explanation: Optional[str] = None

class AssessmentResponse(BaseModel):
    id: str
    node_id: str
    title: str
    passing_score_pct: int
    questions: List[QuestionItem]

class SubmitAssessmentRequest(BaseModel):
    answers: Dict[str, int] # "0": selected_index, "1": selected_index, etc.

class AssessmentResultResponse(BaseModel):
    assessment_id: str
    node_id: str
    score_pct: int
    passed: bool
    passing_score_pct: int
    correct_count: int
    total_questions: int
    feedback: str
    skill_awarded: Optional[str] = None
    points_awarded: int = 0
