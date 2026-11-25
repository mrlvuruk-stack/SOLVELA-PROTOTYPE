from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "student" # "student" or "working_professional"
    daily_capacity_minutes: int = 300
    focus_domains: Optional[str] = "Software Engineering,AI"

class LoginRequest(BaseModel):
    email: str
    password: str

class ProfileResponse(BaseModel):
    daily_capacity_minutes: int
    weekly_capacity_hours: int
    timezone: str
    focus_domains: str
    onboarding_completed: bool
    preferences_json: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    profile: Optional[ProfileResponse] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    daily_capacity_minutes: Optional[int] = None
    weekly_capacity_hours: Optional[int] = None
    timezone: Optional[str] = None
    focus_domains: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class OnboardingRequest(BaseModel):
    role: str
    daily_capacity_hours: float = 5.0
    focus_domains: List[str] = ["Software Engineering"]
    primary_goal_title: Optional[str] = None
    learning_style: Optional[str] = "socratic"

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
