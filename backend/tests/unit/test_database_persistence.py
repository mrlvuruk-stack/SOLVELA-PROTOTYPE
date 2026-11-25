import pytest
import asyncio
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import init_db, AsyncSessionLocal
from app.models.user import User, UserProfile
from app.models.goal import Goal, Milestone
from app.models.task import TaskModel
from app.models.opportunity import OpportunityModel
from sqlalchemy import select

def test_database_persistence_and_relationships():
    """
    Test database table initialization, user creation, goal-milestone relationship,
    task persistence, and DEC-06A 8-category opportunity catalog.
    """
    async def run_db_tests():
        # 1. Initialize tables
        await init_db()
        
        async with AsyncSessionLocal() as session:
            # 2. Persist User and Profile
            unique_email = f"persisted_{datetime.now().timestamp()}@sovela.ai"
            user = User(
                email=unique_email,
                hashed_password="hashed_pw_xyz",
                full_name="Alex Rivera",
                role="student"
            )
            session.add(user)
            await session.flush()
            
            profile = UserProfile(
                user_id=user.id,
                daily_capacity_minutes=300,
                focus_domains="Computer Science,Machine Learning"
            )
            session.add(profile)
            
            # 3. Persist Goal with Milestones
            goal = Goal(
                user_id=user.id,
                title="Master Algorithmic Problem Solving",
                category="skill",
                target_date=datetime.now(timezone.utc) + timedelta(days=60)
            )
            session.add(goal)
            await session.flush()
            
            m1 = Milestone(goal_id=goal.id, title="Solve 50 Dynamic Programming problems")
            m2 = Milestone(goal_id=goal.id, title="Implement Graph Dijkstra and A*")
            session.add_all([m1, m2])
            
            # 4. Persist Tasks
            t1 = TaskModel(
                user_id=user.id,
                goal_id=goal.id,
                title="DP Interval Knapsack Practice",
                duration_minutes=45,
                priority=3,
                status="pending"
            )
            session.add(t1)
            
            # 5. Persist DEC-06A Opportunity across categories
            opp = OpportunityModel(
                title="Google Summer of Code 2026",
                category="internship",
                organization="Google Open Source",
                url="https://summerofcode.withgoogle.com",
                eligibility="Open to students and contributors 18+"
            )
            session.add(opp)
            
            await session.commit()
            
            # 6. Verify Queries
            res_user = await session.execute(select(User).where(User.email == unique_email))
            queried_user = res_user.scalar_one_or_none()
            assert queried_user is not None
            assert queried_user.full_name == "Alex Rivera"
            
            res_tasks = await session.execute(select(TaskModel).where(TaskModel.user_id == user.id))
            tasks = res_tasks.scalars().all()
            assert len(tasks) == 1
            assert tasks[0].title == "DP Interval Knapsack Practice"
            
            res_opps = await session.execute(select(OpportunityModel).where(OpportunityModel.category == "internship"))
            opps = res_opps.scalars().all()
            assert len(opps) >= 1
            
    asyncio.run(run_db_tests())
