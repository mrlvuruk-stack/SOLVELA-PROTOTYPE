from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from app.db.session import get_db
from app.services.ai_router import AIRouterService
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.goal import Goal
from app.models.task import TaskModel
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/intelligence", tags=["Intelligence & Socratic Mentor"])
ai_router = AIRouterService()

class SocraticPromptRequest(BaseModel):
    prompt: str
    simulated_delay_ms: float = 75.0

class CreateSessionRequest(BaseModel):
    title: Optional[str] = "Socratic Pedagogical Dialogue"
    domain: Optional[str] = "General"

class SendMessageRequest(BaseModel):
    prompt: str
    simulated_delay_ms: Optional[float] = 75.0

class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    model_used: Optional[str] = None
    ttfb_ms: Optional[float] = None
    total_turnaround_ms: Optional[float] = None
    created_at: datetime

class SessionSummaryResponse(BaseModel):
    id: str
    title: str
    domain: str
    created_at: datetime
    updated_at: datetime
    message_count: int

@router.post("/socratic/chat")
async def chat_socratic(
    req: SocraticPromptRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Single-turn Socratic Mentor consultation for quick prompts.
    """
    result = await ai_router.route_with_failover(
        prompt=req.prompt,
        tier="socratic",
        simulate_delay_ms=req.simulated_delay_ms
    )
    return {
        "content": result["content"],
        "model_used": result["model_used"],
        "provider_used": result.get("provider_used", "simulation"),
        "is_simulated": result.get("is_simulated", True),
        "ttfb_ms": result.get("ttfb_ms"),
        "total_turnaround_ms": result["total_turnaround_ms"],
        "failover_triggered": result["failover_triggered"],
        "failover_reason": result.get("failover_reason")
    }

@router.get("/socratic/sessions", response_model=List[SessionSummaryResponse])
async def list_user_chat_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all persistent Socratic mentorship sessions for the authenticated user.
    """
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    
    summaries = []
    for s in sessions:
        msg_count_res = await db.execute(select(ChatMessage).where(ChatMessage.session_id == s.id))
        count = len(msg_count_res.scalars().all())
        summaries.append(SessionSummaryResponse(
            id=s.id,
            title=s.title,
            domain=s.domain,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=count
        ))
    return summaries

@router.post("/socratic/sessions", response_model=SessionSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    req: CreateSessionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new persistent multi-turn Socratic mentorship thread.
    """
    session = ChatSession(
        user_id=user.id,
        title=req.title or "Socratic Guidance Session",
        domain=req.domain or "General"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return SessionSummaryResponse(
        id=session.id,
        title=session.title,
        domain=session.domain,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0
    )

@router.get("/socratic/sessions/{session_id}", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full chronological message history for a specific session.
    """
    s_res = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id))
    session = s_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or unauthorized")
        
    m_res = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc())
    )
    messages = m_res.scalars().all()
    
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            model_used=m.model_used,
            ttfb_ms=m.ttfb_ms,
            total_turnaround_ms=m.total_turnaround_ms,
            created_at=m.created_at
        )
        for m in messages
    ]

@router.post("/socratic/sessions/{session_id}/message", response_model=MessageResponse)
async def send_message_to_session(
    session_id: str,
    req: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends a message in a multi-turn Socratic mentorship session.
    Injects user context (active goals/tasks) into the Socratic scaffolding prompt,
    records exact TTFB/turnaround latency, and persists both user and assistant turns.
    """
    s_res = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id))
    session = s_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or unauthorized")

    # 1. Save user turn
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=req.prompt
    )
    db.add(user_msg)
    await db.flush()

    # 2. Retrieve user context (Active Goals & Tasks)
    goals_res = await db.execute(select(Goal).where(Goal.user_id == user.id, Goal.status == "in_progress").limit(3))
    active_goals = [g.title for g in goals_res.scalars().all()]
    
    context_prefix = ""
    if active_goals:
        context_prefix = f"User is currently pursuing goals: {', '.join(active_goals)}. "

    # 3. Execute through AI Router
    augmented_prompt = f"{context_prefix}Student Question: {req.prompt}"
    ai_resp = await ai_router.route_with_failover(
        prompt=augmented_prompt,
        tier="socratic",
        simulate_delay_ms=req.simulated_delay_ms or 75.0
    )

    # 4. Save assistant turn
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_resp["content"],
        model_used=ai_resp["model_used"],
        ttfb_ms=ai_resp.get("ttfb_ms"),
        total_turnaround_ms=ai_resp["total_turnaround_ms"]
    )
    db.add(assistant_msg)
    
    # Update session timestamp
    session.updated_at = datetime.now(timezone.utc)
    if session.title == "Socratic Guidance Session" or not session.title:
        session.title = req.prompt[:40] + ("..." if len(req.prompt) > 40 else "")

    await db.commit()
    await db.refresh(assistant_msg)

    return MessageResponse(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        model_used=assistant_msg.model_used,
        ttfb_ms=assistant_msg.ttfb_ms,
        total_turnaround_ms=assistant_msg.total_turnaround_ms,
        created_at=assistant_msg.created_at
    )

@router.delete("/socratic/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a chat session and all cascading turns.
    """
    s_res = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id))
    session = s_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or unauthorized")
    await db.delete(session)
    await db.commit()
    return None
