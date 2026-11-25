from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from app.db.session import get_db
from app.models.user import User, UserProfile
from app.models.goal import Goal
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse, ProfileResponse,
    ProfileUpdateRequest, OnboardingRequest, ChangePasswordRequest
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & Profile"])

@router.post("/register", response_model=TokenResponse)
async def register_user(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == req.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )
        
    hashed_pwd = hash_password(req.password)
    user = User(
        email=req.email.lower(),
        hashed_password=hashed_pwd,
        full_name=req.full_name,
        role=req.role
    )
    db.add(user)
    await db.flush()
    
    profile = UserProfile(
        user_id=user.id,
        daily_capacity_minutes=req.daily_capacity_minutes,
        focus_domains=req.focus_domains or "Software Engineering,AI",
        onboarding_completed=False,
        preferences_json={
            "learning_style": "socratic",
            "ui": {"dark_mode": True}
        }
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)
    
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    
    profile_resp = ProfileResponse(
        daily_capacity_minutes=profile.daily_capacity_minutes,
        weekly_capacity_hours=profile.weekly_capacity_hours,
        timezone=profile.timezone,
        focus_domains=profile.focus_domains,
        onboarding_completed=profile.onboarding_completed,
        preferences_json=profile.preferences_json
    )
    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        profile=profile_resp
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)

@router.post("/login", response_model=TokenResponse)
async def login_user(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()
    
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    
    profile_resp = None
    if profile:
        profile_resp = ProfileResponse(
            daily_capacity_minutes=profile.daily_capacity_minutes,
            weekly_capacity_hours=profile.weekly_capacity_hours,
            timezone=profile.timezone,
            focus_domains=profile.focus_domains,
            onboarding_completed=profile.onboarding_completed,
            preferences_json=profile.preferences_json
        )
        
    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        profile=profile_resp
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()
    
    profile_resp = None
    if profile:
        profile_resp = ProfileResponse(
            daily_capacity_minutes=profile.daily_capacity_minutes,
            weekly_capacity_hours=profile.weekly_capacity_hours,
            timezone=profile.timezone,
            focus_domains=profile.focus_domains,
            onboarding_completed=profile.onboarding_completed,
            preferences_json=profile.preferences_json
        )
        
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        profile=profile_resp
    )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    req: ProfileUpdateRequest, 
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Update core user fields
    if req.full_name is not None:
        user.full_name = req.full_name.strip()
    if req.role is not None:
        user.role = req.role

    # Update profile fields
    profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    if req.daily_capacity_minutes is not None:
        profile.daily_capacity_minutes = max(30, min(req.daily_capacity_minutes, 960))
    if req.weekly_capacity_hours is not None:
        profile.weekly_capacity_hours = max(5, min(req.weekly_capacity_hours, 100))
    if req.timezone is not None:
        profile.timezone = req.timezone
    if req.focus_domains is not None:
        profile.focus_domains = req.focus_domains
    if req.preferences is not None:
        curr = dict(profile.preferences_json or {})
        curr.update(req.preferences)
        profile.preferences_json = curr
        flag_modified(profile, "preferences_json")

    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)

    profile_resp = ProfileResponse(
        daily_capacity_minutes=profile.daily_capacity_minutes,
        weekly_capacity_hours=profile.weekly_capacity_hours,
        timezone=profile.timezone,
        focus_domains=profile.focus_domains,
        onboarding_completed=profile.onboarding_completed,
        preferences_json=profile.preferences_json
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        profile=profile_resp
    )

@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    req: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    user.role = req.role
    profile.daily_capacity_minutes = int(req.daily_capacity_hours * 60)
    profile.focus_domains = ", ".join(req.focus_domains)
    profile.onboarding_completed = True
    
    prefs = dict(profile.preferences_json or {})
    prefs["learning_style"] = req.learning_style or "socratic"
    profile.preferences_json = prefs
    flag_modified(profile, "preferences_json")

    # Optionally seed initial high-impact goal if specified
    if req.primary_goal_title and req.primary_goal_title.strip():
        primary_goal = Goal(
            user_id=user.id,
            title=req.primary_goal_title.strip(),
            category="skill" if req.role == "student" else "career",
            description=f"Primary objective established during onboarding in {profile.focus_domains}."
        )
        db.add(primary_goal)

    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)

    profile_resp = ProfileResponse(
        daily_capacity_minutes=profile.daily_capacity_minutes,
        weekly_capacity_hours=profile.weekly_capacity_hours,
        timezone=profile.timezone,
        focus_domains=profile.focus_domains,
        onboarding_completed=profile.onboarding_completed,
        preferences_json=profile.preferences_json
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        profile=profile_resp
    )

@router.put("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not verify_password(req.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed"
        )
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    user.hashed_password = hash_password(req.new_password)
    await db.commit()
    return {"status": "success", "message": "Password changed successfully"}
