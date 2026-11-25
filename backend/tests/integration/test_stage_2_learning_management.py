import pytest
import os
import sys
import uuid
from httpx import AsyncClient, ASGITransport

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.db.session import init_db, AsyncSessionLocal
from app.db.seed_learning import seed_learning_data

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_learning_data(db)

@pytest.mark.anyio
async def test_stage_2_list_and_filter_roadmaps():
    """
    Test Step 1: Browse Roadmaps catalog with filtering by domain, difficulty, and search.
    """
    email = f"learner_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "Password123!", "full_name": "Aarav Gupta", "role": "student"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Fetch all roadmaps
        resp = await client.get("/api/v1/learning/roadmaps", headers=headers)
        assert resp.status_code == 200, f"List roadmaps failed: {resp.text}"
        roadmaps = resp.json()
        assert len(roadmaps) >= 2
        slugs = [r["slug"] for r in roadmaps]
        assert "full-stack-ai-engineering" in slugs
        assert "distributed-systems-cloud-architecture" in slugs

        # 2. Filter by domain: "Artificial Intelligence"
        ai_resp = await client.get("/api/v1/learning/roadmaps?domain=Artificial Intelligence", headers=headers)
        assert ai_resp.status_code == 200
        ai_roadmaps = ai_resp.json()
        assert all(r["domain"] == "Artificial Intelligence" for r in ai_roadmaps)

        # 3. Filter by difficulty: "advanced"
        adv_resp = await client.get("/api/v1/learning/roadmaps?difficulty=advanced", headers=headers)
        assert adv_resp.status_code == 200
        adv_roadmaps = adv_resp.json()
        assert all(r["difficulty_level"] == "advanced" for r in adv_roadmaps)

@pytest.mark.anyio
async def test_stage_2_roadmap_detail_nodes_and_enrollment():
    """
    Test Step 2: Retrieve full roadmap curriculum, enroll user, and verify enrollment state.
    """
    email = f"learner_enr_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "Password123!", "full_name": "Rohan Mehra", "role": "student"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Get roadmap detail by slug
        detail_resp = await client.get("/api/v1/learning/roadmaps/full-stack-ai-engineering", headers=headers)
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert data["slug"] == "full-stack-ai-engineering"
        assert len(data["nodes"]) >= 3
        assert data["is_enrolled"] is False

        # Verify node resources and takeaways
        node0 = data["nodes"][0]
        assert len(node0["key_takeaways"]) > 0
        assert len(node0["resources"]) > 0
        assert node0["has_assessment"] is True
        roadmap_id = data["id"]

        # 2. Enroll in roadmap
        enroll_resp = await client.post(f"/api/v1/learning/roadmaps/{roadmap_id}/enroll", headers=headers)
        assert enroll_resp.status_code == 200
        enrolled_data = enroll_resp.json()
        assert enrolled_data["is_enrolled"] is True
        assert enrolled_data["progress_pct"] == 0
        assert enrolled_data["enrollment_id"] is not None

@pytest.mark.anyio
async def test_stage_2_node_completion_and_skill_progression():
    """
    Test Step 3: Complete curriculum nodes, track progress percentage, and verify skill point awards.
    """
    email = f"learner_prog_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "Password123!", "full_name": "Sneha Roy", "role": "working_professional"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get roadmap nodes
        detail_resp = await client.get("/api/v1/learning/roadmaps/full-stack-ai-engineering", headers=headers)
        nodes = detail_resp.json()["nodes"]
        node0_id = nodes[0]["id"]
        node1_id = nodes[1]["id"]

        # Complete Node 0
        comp0 = await client.post(f"/api/v1/learning/nodes/{node0_id}/complete", json={
            "notes": "Reviewed attention mechanisms and verified provider fallback probes."
        }, headers=headers)
        assert comp0.status_code == 200
        res0 = comp0.json()
        assert res0["completed_nodes_count"] == 1
        assert res0["progress_pct"] > 0
        assert res0["is_roadmap_completed"] is False

        # Complete Node 1
        comp1 = await client.post(f"/api/v1/learning/nodes/{node1_id}/complete", headers=headers)
        assert comp1.status_code == 200
        res1 = comp1.json()
        assert res1["completed_nodes_count"] == 2
        assert res1["progress_pct"] > res0["progress_pct"]

        # Verify Skills Portfolio
        skills_resp = await client.get("/api/v1/learning/skills", headers=headers)
        assert skills_resp.status_code == 200
        skills = skills_resp.json()
        assert len(skills) >= 1
        # User gained 50 skill points from 2 node completions
        earned_skills = [s for s in skills if s["points"] > 0]
        assert len(earned_skills) >= 1
        assert earned_skills[0]["points"] >= 50

@pytest.mark.anyio
async def test_stage_2_node_assessment_evaluation():
    """
    Test Step 4: Assessment retrieval (sanitized) and submission evaluation:
    - Verifies correct answers score 100% and pass threshold.
    - Verifies failing submission yields helpful feedback and low score.
    - Verifies passing automatically marks node complete.
    """
    email = f"learner_eval_{uuid.uuid4().hex[:8]}@sovela.ai"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "Password123!", "full_name": "Dev Evaluator", "role": "student"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get node with assessment
        detail_resp = await client.get("/api/v1/learning/roadmaps/full-stack-ai-engineering", headers=headers)
        node0 = detail_resp.json()["nodes"][0]
        node0_id = node0["id"]

        # Fetch assessment questions
        assess_resp = await client.get(f"/api/v1/learning/assessments/node/{node0_id}", headers=headers)
        assert assess_resp.status_code == 200
        assess_data = assess_resp.json()
        assessment_id = assess_data["id"]
        questions = assess_data["questions"]
        assert len(questions) == 2
        # Ensure answers / correct_index are NOT leaked in response
        for q in questions:
            assert "correct_index" not in q
            assert len(q["options"]) == 4

        # 1. Submit FAILING answers (all choice 0: wrong)
        fail_submit = await client.post(
            f"/api/v1/learning/assessments/{assessment_id}/submit",
            json={"answers": {"0": 0, "1": 0}},
            headers=headers
        )
        assert fail_submit.status_code == 200
        fail_data = fail_submit.json()
        assert fail_data["passed"] is False
        assert fail_data["score_pct"] < 75
        assert "Passing threshold is" in fail_data["feedback"]

        # 2. Submit PASSING answers (Q0: choice 1, Q1: choice 1)
        pass_submit = await client.post(
            f"/api/v1/learning/assessments/{assessment_id}/submit",
            json={"answers": {"0": 1, "1": 1}},
            headers=headers
        )
        assert pass_submit.status_code == 200
        pass_data = pass_submit.json()
        assert pass_data["passed"] is True
        assert pass_data["score_pct"] == 100
        assert pass_data["correct_count"] == 2
        assert "Congratulations" in pass_data["feedback"]
        assert pass_data["points_awarded"] == 50

        # 3. Verify node was automatically marked complete as result of passing
        detail_after = await client.get("/api/v1/learning/roadmaps/full-stack-ai-engineering", headers=headers)
        node0_after = detail_after.json()["nodes"][0]
        assert node0_after["is_completed"] is True
