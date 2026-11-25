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
async def test_sprint_1_onboarding_wizard_workflow():
    """
    Test Step 1: User registers and completes the 4-step interactive Onboarding Wizard:
    - Persona / role selection
    - Focus domains
    - Daily capacity cap
    - Initial primary goal generation
    """
    email = f"onboarding_user_{uuid.uuid4().hex[:8]}@sovela.ai"
    password = "SecurePassword2026!"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register base user
        reg_resp = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Priya Nair",
            "role": "student"
        })
        assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Check initial profile shows onboarding_completed == False
        me_resp = await client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["profile"]["onboarding_completed"] is False

        # 3. Complete onboarding
        onboard_payload = {
            "role": "researcher",
            "daily_capacity_hours": 6.5,
            "focus_domains": ["Artificial Intelligence", "Distributed Systems"],
            "primary_goal_title": "Publish Agent Orchestration Paper at ICSE 2026",
            "learning_style": "socratic"
        }
        onboard_resp = await client.post("/api/v1/auth/onboarding", json=onboard_payload, headers=headers)
        assert onboard_resp.status_code == 200, f"Onboarding failed: {onboard_resp.text}"
        onboard_data = onboard_resp.json()

        assert onboard_data["role"] == "researcher"
        assert onboard_data["profile"]["onboarding_completed"] is True
        assert onboard_data["profile"]["daily_capacity_minutes"] == 390  # 6.5 * 60
        assert "Artificial Intelligence" in onboard_data["profile"]["focus_domains"]
        assert onboard_data["profile"]["preferences_json"]["learning_style"] == "socratic"

        # 4. Verify primary goal was automatically seeded
        goals_resp = await client.get("/api/v1/goals", headers=headers)
        assert goals_resp.status_code == 200
        goals = goals_resp.json()
        assert len(goals) >= 1
        assert any("Publish Agent Orchestration Paper" in g["title"] for g in goals)

@pytest.mark.anyio
async def test_sprint_1_profile_management_and_password_change():
    """
    Test Step 2: User Profile Modal Updates and Password Security Verification:
    - Update user full name, daily capacity bounds, timezone, and preferences
    - Test password change validation: failure with bad old password, success with valid password
    - Verify old password is invalidated and new password authenticates
    """
    email = f"profile_user_{uuid.uuid4().hex[:8]}@sovela.ai"
    old_pw = "OriginalPass123!"
    new_pw = "UpdatedSecretPass456!"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": old_pw,
            "full_name": "Dev User",
            "role": "working_professional"
        })
        assert reg.status_code == 200
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Update Profile (capacity, timezone, focus_domains)
        prof_update = {
            "full_name": "Dev User Senior",
            "daily_capacity_minutes": 420,
            "timezone": "Asia/Kolkata",
            "focus_domains": "Machine Learning, Cloud Architecture",
            "preferences": {"theme": "system", "sound_alerts": False}
        }
        update_resp = await client.put("/api/v1/auth/profile", json=prof_update, headers=headers)
        assert update_resp.status_code == 200
        up_data = update_resp.json()
        assert up_data["full_name"] == "Dev User Senior"
        assert up_data["profile"]["daily_capacity_minutes"] == 420
        assert up_data["profile"]["timezone"] == "Asia/Kolkata"
        assert up_data["profile"]["preferences_json"]["sound_alerts"] is False

        # 2. Test change-password with INVALID old password
        bad_pw_resp = await client.put("/api/v1/auth/change-password", json={
            "old_password": "WrongPassword999!",
            "new_password": new_pw
        }, headers=headers)
        assert bad_pw_resp.status_code == 400
        assert "Current password verification failed" in bad_pw_resp.json()["detail"]

        # 3. Test change-password with VALID old password
        good_pw_resp = await client.put("/api/v1/auth/change-password", json={
            "old_password": old_pw,
            "new_password": new_pw
        }, headers=headers)
        assert good_pw_resp.status_code == 200
        assert good_pw_resp.json()["message"] == "Password changed successfully"

        # 4. Old password fails login
        old_login = await client.post("/api/v1/auth/login", json={"email": email, "password": old_pw})
        assert old_login.status_code == 401

        # 5. New password succeeds login
        new_login = await client.post("/api/v1/auth/login", json={"email": email, "password": new_pw})
        assert new_login.status_code == 200
        assert "access_token" in new_login.json()

@pytest.mark.anyio
async def test_sprint_1_ai_goal_decomposition_into_tasks():
    """
    Test Step 3: SMART Goal AI Decomposition:
    - Create a high-level goal
    - Execute POST /api/v1/goals/{id}/decompose
    - Verify 4 actionable sub-tasks generated and linked to goal
    - Verify non-owner cannot decompose or access tasks
    """
    email1 = f"goal_owner_{uuid.uuid4().hex[:8]}@sovela.ai"
    email2 = f"other_user_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register user 1
        reg1 = await client.post("/api/v1/auth/register", json={
            "email": email1, "password": "Password123!", "full_name": "Goal Owner", "role": "student"
        })
        token1 = reg1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Register user 2 (attacker/other user)
        reg2 = await client.post("/api/v1/auth/register", json={
            "email": email2, "password": "Password123!", "full_name": "Attacker", "role": "student"
        })
        token2 = reg2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 1 creates Goal
        create_goal_resp = await client.post("/api/v1/goals", json={
            "title": "Master Distributed Consensus Algorithms (Raft & Paxos)",
            "description": "Deep understanding and implementation of Raft consensus protocol in Go or Rust.",
            "category": "skill",
            "target_date": "2026-12-31T00:00:00"
        }, headers=headers1)
        assert create_goal_resp.status_code == 201
        goal_id = create_goal_resp.json()["id"]

        # User 2 attempts to decompose User 1's goal -> 404 Not Found (auth isolated)
        unauth_decompose = await client.post(f"/api/v1/goals/{goal_id}/decompose", headers=headers2)
        assert unauth_decompose.status_code == 404

        # User 1 decomposes Goal
        decomp_resp = await client.post(f"/api/v1/goals/{goal_id}/decompose", headers=headers1)
        assert decomp_resp.status_code == 200, f"Decompose failed: {decomp_resp.text}"
        decomposed_tasks = decomp_resp.json()
        assert len(decomposed_tasks) == 4

        for task in decomposed_tasks:
            assert task["goal_id"] == goal_id
            assert task["duration_minutes"] in [30, 45, 60]
            assert task["status"] == "pending"
            assert "Phase" in task["title"]

        # Verify tasks are returned in user's task list
        tasks_list_resp = await client.get("/api/v1/tasks", headers=headers1)
        assert tasks_list_resp.status_code == 200
        all_tasks = tasks_list_resp.json()
        goal_task_ids = {t["id"] for t in decomposed_tasks}
        matching = [t for t in all_tasks if t["id"] in goal_task_ids]
        assert len(matching) == 4

@pytest.mark.anyio
async def test_sprint_1_persistent_socratic_chat_sessions():
    """
    Test Step 4: Persistent Multi-turn Socratic Mentor Sessions:
    - Create session
    - List sessions
    - Send message turn and verify AI response with TTFB telemetry
    - Retrieve full message thread history
    - Delete session and verify cleanup
    """
    email = f"mentor_user_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "Password123!", "full_name": "Mentee", "role": "student"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create Socratic chat session
        create_sess = await client.post("/api/v1/intelligence/socratic/sessions", json={
            "title": "Understanding Dynamic Programming Optimizations",
            "domain": "Algorithms"
        }, headers=headers)
        assert create_sess.status_code == 201
        sess_data = create_sess.json()
        session_id = sess_data["id"]
        assert sess_data["title"] == "Understanding Dynamic Programming Optimizations"
        assert sess_data["domain"] == "Algorithms"

        # 2. List sessions
        list_sess = await client.get("/api/v1/intelligence/socratic/sessions", headers=headers)
        assert list_sess.status_code == 200
        sessions = list_sess.json()
        assert len(sessions) >= 1
        assert any(s["id"] == session_id for s in sessions)

        # 3. Send message turn
        msg_resp = await client.post(
            f"/api/v1/intelligence/socratic/sessions/{session_id}/message",
            json={"prompt": "How do I recognize when a problem has overlapping subproblems versus greedy choice property?"},
            headers=headers
        )
        assert msg_resp.status_code == 200, f"Send message failed: {msg_resp.text}"
        assistant_turn = msg_resp.json()
        assert assistant_turn["session_id"] == session_id
        assert assistant_turn["role"] == "assistant"
        assert len(assistant_turn["content"]) > 10
        assert assistant_turn["total_turnaround_ms"] is not None
        assert assistant_turn["model_used"] is not None

        # 4. Fetch session history (should have 2 messages: user + assistant)
        history_resp = await client.get(
            f"/api/v1/intelligence/socratic/sessions/{session_id}",
            headers=headers
        )
        assert history_resp.status_code == 200
        messages = history_resp.json()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

        # 5. Delete session
        del_resp = await client.delete(
            f"/api/v1/intelligence/socratic/sessions/{session_id}",
            headers=headers
        )
        assert del_resp.status_code == 204

        # 6. Verify session messages return 404
        post_del = await client.get(
            f"/api/v1/intelligence/socratic/sessions/{session_id}",
            headers=headers
        )
        assert post_del.status_code == 404
