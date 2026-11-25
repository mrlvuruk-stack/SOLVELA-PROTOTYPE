import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.main import app

client = TestClient(app)

def test_user_ownership_and_data_isolation():
    """
    Priority 5: Audit user ownership and API authorisation.
    Verifies that User B cannot view, modify, delete, or reference User A's goals and tasks.
    """
    # 1. Register User A
    email_a = f"usera_{os.urandom(4).hex()}@sovela.ai"
    resp_a = client.post("/api/v1/auth/register", json={
        "email": email_a, "password": "PasswordA123!", "full_name": "User Alpha", "role": "student"
    })
    token_a = resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    email_b = f"userb_{os.urandom(4).hex()}@sovela.ai"
    resp_b = client.post("/api/v1/auth/register", json={
        "email": email_b, "password": "PasswordB123!", "full_name": "User Beta", "role": "working_professional"
    })
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates Goal A
    goal_resp = client.post("/api/v1/goals", headers=headers_a, json={
        "title": "Alpha Confidential Master Thesis",
        "category": "academic"
    })
    goal_a_id = goal_resp.json()["id"]

    # 4. User A creates Task A
    task_resp = client.post("/api/v1/tasks", headers=headers_a, json={
        "title": "Alpha Research Synthesis",
        "duration_minutes": 60,
        "priority": 4,
        "goal_id": goal_a_id
    })
    task_a_id = task_resp.json()["id"]

    # 5. TEST: User B attempts to GET User A's goal -> MUST FAIL (404)
    res_b_goal = client.get(f"/api/v1/goals/{goal_a_id}", headers=headers_b)
    assert res_b_goal.status_code == 404, "User B was able to view User A's goal!"

    # 6. TEST: User B attempts to attach their task to User A's goal -> MUST FAIL (403 Forbidden)
    res_b_task_inject = client.post("/api/v1/tasks", headers=headers_b, json={
        "title": "Malicious Task Attachment",
        "duration_minutes": 30,
        "priority": 2,
        "goal_id": goal_a_id
    })
    assert res_b_task_inject.status_code == 403, "User B was able to attach a task to User A's goal!"

    # 7. TEST: User B attempts to complete User A's task -> MUST FAIL (404)
    res_b_comp = client.put(f"/api/v1/tasks/{task_a_id}/complete", headers=headers_b)
    assert res_b_comp.status_code == 404, "User B was able to complete User A's task!"

    # 8. TEST: User B attempts to delete User A's task -> MUST FAIL (404)
    res_b_del = client.delete(f"/api/v1/tasks/{task_a_id}", headers=headers_b)
    assert res_b_del.status_code == 404, "User B was able to delete User A's task!"

    # 9. TEST: Unauthenticated request to /api/v1/goals -> MUST FAIL (401)
    res_unauth = client.get("/api/v1/goals")
    assert res_unauth.status_code == 401, "Unauthenticated request was allowed to list goals!"
