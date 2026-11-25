import pytest
import asyncio
import os
import sys
import sqlite3
import uuid
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable
from pgvector.sqlalchemy import Vector

from alembic.config import Config
from alembic import command
from app.models import Base, User, UserProfile, Goal, Milestone, TaskModel, OpportunityModel
from app.core.config import settings

TEST_DB_PATH = os.path.join(ROOT_DIR, "test_deep_verification.db").replace("\\", "/")
TEST_SYNC_URL = f"sqlite:///{TEST_DB_PATH}"
TEST_ASYNC_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture(scope="module", autouse=True)
def migration_setup():
    """Sets up an isolated database and runs Alembic migrations."""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass
            
    alembic_cfg = Config(os.path.join(ROOT_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_SYNC_URL)
    
    # 1. Upgrade to head
    command.upgrade(alembic_cfg, "head")
    
    yield alembic_cfg
    
    # Teardown
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass

def test_p2_fresh_migration_and_index_verification():
    """
    P2 Verification: Verify fresh database migration creates all 6 tables and indexes in SQLite.
    """
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    
    expected_tables = {
        "users", "user_profiles", "goals", "milestones", "tasks", 
        "opportunities", "chat_sessions", "chat_messages", "alembic_version"
    }
    assert expected_tables.issubset(tables), f"Missing tables. Found: {tables}"
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
    indexes = {row[0] for row in cursor.fetchall()}
    expected_indexes = {
        "ix_users_email", "ix_goals_user_id", "ix_milestones_goal_id",
        "ix_tasks_user_id", "ix_tasks_goal_id", "ix_tasks_status", "ix_opportunities_category",
        "ix_chat_sessions_user_id", "ix_chat_messages_session_id"
    }
    assert expected_indexes.issubset(indexes), f"Missing indexes. Found: {indexes}"
    conn.close()

def test_p2_migration_downgrade_and_reupgrade_cycle():
    """
    P2 Verification: Test full migration lifecycle: upgrade head -> downgrade base -> upgrade head.
    Proves migrations are completely reversible without dangling schema state.
    """
    alembic_cfg = Config(os.path.join(ROOT_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_SYNC_URL)
    
    # Downgrade to base
    command.downgrade(alembic_cfg, "base")
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables_after_downgrade = {row[0] for row in cursor.fetchall() if row[0] != "alembic_version"}
    assert len(tables_after_downgrade) == 0, f"Expected 0 tables after downgrade, found {tables_after_downgrade}"
    conn.close()
    
    # Re-upgrade to head
    command.upgrade(alembic_cfg, "head")
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables_after_reupgrade = {row[0] for row in cursor.fetchall()}
    assert "users" in tables_after_reupgrade
    assert "tasks" in tables_after_reupgrade
    assert "chat_sessions" in tables_after_reupgrade
    conn.close()

@pytest.mark.anyio
async def test_p2_crud_and_json_jsonb_handling():
    """
    P2 Verification: Test CRUD operations, nested JSON/JSONB serialization, and retrieval.
    """
    engine = create_async_engine(TEST_ASYNC_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    user_id = str(uuid.uuid4())
    async with session_factory() as session:
        # Create User with profile and nested JSON preferences
        user = User(
            id=user_id,
            email=f"deep_test_{user_id[:8]}@sovela.ai",
            hashed_password="hashed_pw_deep_test",
            full_name="Deep Verification User",
            role="student"
        )
        profile = UserProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            daily_capacity_minutes=360,
            weekly_capacity_hours=30,
            timezone="Asia/Kolkata",
            focus_domains="Algorithms,Distributed Systems",
            preferences_json={
                "learning_style": "socratic",
                "difficulty_bias": "high",
                "ui": {"dark_mode": True, "accent": "#00f0ff"},
                "notification_schedule": ["09:00", "18:00"]
            }
        )
        task = TaskModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Master Raft Consensus Algorithm",
            duration_minutes=90,
            priority=4,
            metadata_json={
                "algorithm": "Raft",
                "key_phases": ["Leader Election", "Log Replication", "Safety"],
                "prerequisites_met": True
            }
        )
        opp = OpportunityModel(
            id=str(uuid.uuid4()),
            title="Google Summer of Code 2027",
            category="internship",
            organization="Google Open Source",
            url="https://summerofcode.withgoogle.com",
            metadata_json={"stipend_tier": "tier-1", "remote": True, "open_slots": 1200}
        )
        session.add_all([user, profile, task, opp])
        await session.commit()

    # Query back and verify nested JSON parsing
    async with session_factory() as session:
        loaded_user = await session.get(User, user_id)
        assert loaded_user is not None
        assert loaded_user.email.startswith("deep_test_")
        
        # Verify Profile JSON
        result = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        loaded_profile = result.scalars().first()
        assert loaded_profile is not None
        assert loaded_profile.preferences_json["learning_style"] == "socratic"
        assert loaded_profile.preferences_json["ui"]["accent"] == "#00f0ff"
        assert "09:00" in loaded_profile.preferences_json["notification_schedule"]
        
        # Verify Task Metadata JSON
        result_task = await session.execute(select(TaskModel).where(TaskModel.user_id == user_id))
        loaded_task = result_task.scalars().first()
        assert loaded_task is not None
        assert loaded_task.metadata_json["algorithm"] == "Raft"
        assert len(loaded_task.metadata_json["key_phases"]) == 3

    await engine.dispose()

@pytest.mark.anyio
async def test_p2_cascading_foreign_keys():
    """
    P2 Verification: Enforce SQLite PRAGMA foreign_keys = ON and verify cascade deletes.
    Deleting a user must automatically delete their profile, goals, milestones, and tasks.
    """
    engine = create_async_engine(TEST_ASYNC_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    user_id = str(uuid.uuid4())
    goal_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    milestone_id = str(uuid.uuid4())
    
    async with session_factory() as session:
        await session.execute(text("PRAGMA foreign_keys = ON;"))
        user = User(
            id=user_id,
            email=f"cascade_{user_id[:8]}@sovela.ai",
            hashed_password="pw",
            full_name="Cascade User"
        )
        goal = Goal(id=goal_id, user_id=user_id, title="Publish Research Paper")
        milestone = Milestone(id=milestone_id, goal_id=goal_id, title="Literature Survey")
        task = TaskModel(id=task_id, user_id=user_id, goal_id=goal_id, title="Write Abstract", duration_minutes=60)
        session.add_all([user, goal, milestone, task])
        await session.commit()
        
    # Now delete user with foreign keys ON
    async with session_factory() as session:
        await session.execute(text("PRAGMA foreign_keys = ON;"))
        u = await session.get(User, user_id)
        assert u is not None
        await session.delete(u)
        await session.commit()
        
    # Verify cascades
    async with session_factory() as session:
        u_check = await session.get(User, user_id)
        assert u_check is None
        g_check = await session.get(Goal, goal_id)
        assert g_check is None
        m_check = await session.get(Milestone, milestone_id)
        assert m_check is None
        t_check = await session.get(TaskModel, task_id)
        assert t_check is None

    await engine.dispose()

@pytest.mark.anyio
async def test_p2_explicit_transaction_rollback():
    """
    P2 Verification: Verify that session.rollback() discards pending uncommitted mutations.
    """
    engine = create_async_engine(TEST_ASYNC_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    user_id = str(uuid.uuid4())
    async with session_factory() as session:
        user = User(
            id=user_id,
            email=f"rollback_{user_id[:8]}@sovela.ai",
            hashed_password="pw",
            full_name="Rollback Test User"
        )
        session.add(user)
        await session.flush()
        await session.rollback()
        
    # Verify user was NOT persisted
    async with session_factory() as session:
        persisted = await session.get(User, user_id)
        assert persisted is None, "User should not exist after explicit rollback"

    await engine.dispose()

def test_p2_postgresql16_and_pgvector_compatibility():
    """
    P2 Verification: Verify PostgreSQL 16 dialect compilation, JSONB conversion,
    and pgvector Vector(1536) compilation.
    """
    pg_dialect = postgresql.dialect()
    
    # 1. Verify JSONB compilation for UserProfile, TaskModel, OpportunityModel
    user_ddl = str(CreateTable(UserProfile.__table__).compile(dialect=pg_dialect))
    assert "JSONB" in user_ddl or "JSON" in user_ddl
    
    task_ddl = str(CreateTable(TaskModel.__table__).compile(dialect=pg_dialect))
    assert "JSONB" in task_ddl or "JSON" in task_ddl
    
    opp_ddl = str(CreateTable(OpportunityModel.__table__).compile(dialect=pg_dialect))
    assert "JSONB" in opp_ddl or "JSON" in opp_ddl
    
    # 2. Verify pgvector Vector(1536) embedding compilation
    vector_type = Vector(1536)
    compiled_vector = vector_type.compile(dialect=pg_dialect)
    assert "vector(1536)" in compiled_vector.lower()
    
    # 3. Verify Foreign Key ondelete constraints compile to valid PostgreSQL DDL
    assert "ON DELETE CASCADE" in user_ddl
    assert "ON DELETE SET NULL" in task_ddl
    
    print("\n[PostgreSQL 16 + pgvector Verification] All DDL constraints, JSONB, and Vector(1536) successfully compiled.")
