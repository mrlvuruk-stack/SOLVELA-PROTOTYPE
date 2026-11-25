import pytest
import os
import sys
import uuid
from httpx import AsyncClient, ASGITransport

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.db.session import init_db

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()

@pytest.mark.anyio
async def test_p3_frontend_workflow_1_registration():
    """
    Workflow 1: User Registration
    Simulates frontend AuthModal registration form submission.
    """
    unique_email = f"student_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/register", json={
            "email": unique_email,
            "password": "StrongPassword123!",
            "full_name": "Siddharth Verma",
            "role": "student"
        })
        assert resp.status_code == 200, f"Registration failed: {resp.text}"
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == unique_email
        assert data["user"]["role"] == "student"
        assert data["user"]["profile"]["daily_capacity_minutes"] == 300

@pytest.mark.anyio
async def test_p3_frontend_workflow_2_login_and_auth_state():
    """
    Workflow 2: Login & Authentication State Verification
    Simulates frontend login flow, valid bearer token access, and 401 unauthorized rejection.
    """
    email = f"prof_{uuid.uuid4().hex[:8]}@sovela.ai"
    password = "WorkingProfessional2026!"
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register user
        reg_resp = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Aarav Sharma",
            "role": "working_professional"
        })
        assert reg_resp.status_code == 200
        
        # 2. Login via JSON (matching frontend apiFetch("/auth/login", { body: JSON.stringify(...) }))
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # 3. Authenticated /me endpoint
        me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == email
        assert me_data["role"] == "working_professional"
        
        # 4. Unauthenticated check (no header) -> 401 Unauthorized
        unauth_resp = await client.get("/api/v1/auth/me")
        assert unauth_resp.status_code == 401

@pytest.mark.anyio
async def test_p3_frontend_workflow_3_dashboard_today_data():
    """
    Workflow 3: Dashboard Today Data Retrieval
    Simulates TodayView fetching capacity, utilization, and assigned tasks.
    """
    email = f"dash_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Dash User",
            "role": "student"
        })
        token = reg.json()["access_token"]
        
        # Fetch today dashboard
        dash_resp = await client.get("/api/v1/dashboard/today", headers={"Authorization": f"Bearer {token}"})
        assert dash_resp.status_code == 200
        dash = dash_resp.json()
        assert "capacity" in dash
        assert dash["capacity"]["daily_capacity_minutes"] == 300
        assert "utilization_pct" in dash["capacity"]
        assert "tasks" in dash

@pytest.mark.anyio
async def test_p3_frontend_workflow_4_goal_creation_and_milestones():
    """
    Workflow 4: Goal Creation and Milestones
    Simulates GoalManager creating a SMART goal with nested milestones.
    """
    email = f"goal_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Goal Achiever",
            "role": "student"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create Goal (returns 201 Created)
        create_resp = await client.post("/api/v1/goals", headers=headers, json={
            "title": "Build Distributed Key-Value Store",
            "category": "skill",
            "description": "Implement consensus-backed LSM-tree storage engine",
            "target_date": "2027-06-30T00:00:00Z",
            "milestones": [
                {"title": "Design WAL and MemTable architecture"},
                {"title": "Implement SSTable compaction and Bloom filters"}
            ]
        })
        assert create_resp.status_code in [200, 201]
        goal_data = create_resp.json()
        assert goal_data["title"] == "Build Distributed Key-Value Store"
        assert len(goal_data["milestones"]) == 2
        
        # List Goals
        list_resp = await client.get("/api/v1/goals", headers=headers)
        assert list_resp.status_code == 200
        goals = list_resp.json()
        assert any(g["id"] == goal_data["id"] for g in goals)

@pytest.mark.anyio
async def test_p3_frontend_workflow_5_task_lifecycle_creation_and_completion():
    """
    Workflow 5: Task Lifecycle
    Simulates TodayView creating a quick task and marking it completed.
    """
    email = f"task_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Task Operator",
            "role": "student"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create Task (returns 201 Created)
        task_resp = await client.post("/api/v1/tasks", headers=headers, json={
            "title": "Study Raft Leader Election State Transitions",
            "duration_minutes": 45,
            "priority": 3,
            "energy_level": 4
        })
        assert task_resp.status_code in [200, 201]
        task_id = task_resp.json()["id"]
        assert task_resp.json()["status"] == "pending"
        
        # Mark Task Complete
        comp_resp = await client.put(f"/api/v1/tasks/{task_id}/complete", headers=headers)
        assert comp_resp.status_code == 200
        assert comp_resp.json()["status"] == "completed"
        
        # Verify in Dashboard
        dash_resp = await client.get("/api/v1/dashboard/today", headers=headers)
        assert dash_resp.status_code == 200
        dash_tasks = dash_resp.json()["tasks"]
        target = next((t for t in dash_tasks if t["id"] == task_id), None)
        assert target is not None
        assert target["status"] == "completed"

@pytest.mark.anyio
async def test_p3_frontend_workflow_6_socratic_mentor_chat():
    """
    Workflow 6: Socratic AI Mentor Chat
    Simulates SocraticChat submitting user queries and receiving pedagogical guidance
    with verified active model and TTFB telemetry.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        chat_resp = await client.post("/api/v1/intelligence/socratic/chat", json={
            "prompt": "How does Raft maintain log safety during leader crashes?",
            "simulated_delay_ms": 70.0
        })
        assert chat_resp.status_code == 200
        data = chat_resp.json()
        assert "content" in data
        assert "Socratic" in data["content"] or "guidance" in data["content"]
        assert data["model_used"] in ["claude-haiku-5-5", "gpt-4o-mini-2024-07-18", "gemini-3.5-flash-lite"]
        assert data["ttfb_ms"] is not None
        assert data["total_turnaround_ms"] >= data["ttfb_ms"]
        assert data["failover_triggered"] is False
        assert data["is_simulated"] is True

@pytest.mark.anyio
async def test_p3_frontend_workflow_7_opportunity_hub():
    """
    Workflow 7: Opportunity Hub Exploration across 8 DEC-06A Categories
    Simulates OpportunityHub browsing and category filtering.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # All opportunities
        all_resp = await client.get("/api/v1/opportunities")
        assert all_resp.status_code == 200
        opps = all_resp.json()
        assert len(opps) >= 8  # Seeds cover all 8 categories
        
        # Category filter: hackathons
        hack_resp = await client.get("/api/v1/opportunities?category=hackathon")
        assert hack_resp.status_code == 200
        hackathons = hack_resp.json()
        assert len(hackathons) >= 1
        assert all(h["category"] == "hackathon" for h in hackathons)
