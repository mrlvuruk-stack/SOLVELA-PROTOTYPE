import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "active_models" in data
    assert data["governance"]["dec_06a_opportunity_hub"] == "LOCKED_APPROVED"
    assert "http://localhost:3000" in data["cors_origins"]

def test_end_to_end_user_journey():
    # 1. Register User
    unique_email = f"e2e_{os.urandom(4).hex()}@sovela.ai"
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Jordan Lee",
        "role": "student",
        "daily_capacity_minutes": 240,
        "focus_domains": "Computer Science,Algorithms"
    })
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    token = reg_data["access_token"]
    assert token is not None
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    
    # 3. Create Goal with Milestones
    goal_resp = client.post("/api/v1/goals", headers=auth_headers, json={
        "title": "Pass Advanced Data Structures",
        "category": "academic",
        "milestones": [
            {"title": "Implement AVL Tree"},
            {"title": "Master Segment Tree"}
        ]
    })
    assert goal_resp.status_code == 201
    goal_data = goal_resp.json()
    goal_id = goal_data["id"]
    assert len(goal_data["milestones"]) == 2
    
    # 4. Create Task
    task_resp = client.post("/api/v1/tasks", headers=auth_headers, json={
        "title": "Practice AVL rotations",
        "duration_minutes": 60,
        "priority": 4,
        "goal_id": goal_id
    })
    assert task_resp.status_code == 201
    task_data = task_resp.json()
    task_id = task_data["id"]
    
    # 5. Get Today Dashboard (Top Rocks & Capacity Gauge)
    dash_resp = client.get("/api/v1/dashboard/today", headers=auth_headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert len(dash_data["top_rocks"]) >= 1
    assert dash_data["top_rocks"][0]["id"] == task_id
    assert dash_data["capacity"]["daily_capacity_minutes"] == 240
    
    # 6. Run Persistent Auto-Schedule
    sched_resp = client.post("/api/v1/temporal/auto-schedule", headers=auth_headers, json={
        "use_persistent_tasks": True
    })
    assert sched_resp.status_code == 200
    sched_data = sched_resp.json()
    assert sched_data["target_met"] is True
    assert sched_data["placements_count"] >= 1
    
    # 7. Complete Task
    comp_resp = client.put(f"/api/v1/tasks/{task_id}/complete", headers=auth_headers)
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "completed"
    
    # 8. Query Opportunities across 8 categories (DEC-06A)
    opps_resp = client.get("/api/v1/opportunities")
    assert opps_resp.status_code == 200
    opps = opps_resp.json()
    assert len(opps) >= 8
    categories = {o["category"] for o in opps}
    assert "internship" in categories
    assert "hackathon" in categories
    assert "scholarship" in categories
    
    # 9. Socratic AI Mentor
    chat_resp = client.post("/api/v1/intelligence/socratic/chat", json={
        "prompt": "How does dynamic programming handle overlapping subproblems?",
        "simulated_delay_ms": 75.0
    })
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "Socratic" in chat_data["content"]
