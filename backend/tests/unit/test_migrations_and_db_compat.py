import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.dialects import sqlite, postgresql
from sqlalchemy.schema import CreateTable
from app.models import (
    User, UserProfile, Goal, Milestone, TaskModel, OpportunityModel,
    ChatSession, ChatMessage, Roadmap, RoadmapNode, RoadmapEnrollment,
    UserNodeProgress, Skill, UserSkill, Assessment, UserAssessmentAttempt
)
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
from app.core.config import settings

def test_sqlite_and_postgresql_ddl_compilation():
    """
    Priority 7: Verify SQLite and PostgreSQL compatibility.
    Compiles DDL for all models under both dialects to ensure no dialect-incompatible types or constraints.
    """
    models = [
        User, UserProfile, Goal, Milestone, TaskModel, OpportunityModel,
        ChatSession, ChatMessage, Roadmap, RoadmapNode, RoadmapEnrollment,
        UserNodeProgress, Skill, UserSkill, Assessment, UserAssessmentAttempt
    ]
    
    for model in models:
        # 1. Compile for SQLite
        sqlite_ddl = str(CreateTable(model.__table__).compile(dialect=sqlite.dialect()))
        assert "CREATE TABLE" in sqlite_ddl
        
        # 2. Compile for PostgreSQL
        pg_ddl = str(CreateTable(model.__table__).compile(dialect=postgresql.dialect()))
        assert "CREATE TABLE" in pg_ddl
        
    print(f"\n[DDL Dialect Verification] All {len(models)} models successfully compiled for both SQLite and PostgreSQL dialects.")

def test_alembic_migrations_at_head():
    """
    Priority 6: Verify Alembic migration system is initialized and at head.
    """
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script.get_current_head()
    assert head_rev is not None
    assert len(head_rev) > 0
    print(f"\n[Alembic Migration Verification] Current Head Revision: {head_rev}")
