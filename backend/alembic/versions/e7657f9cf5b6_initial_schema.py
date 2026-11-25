"""initial_schema

Revision ID: e7657f9cf5b6
Revises: 
Create Date: 2026-11-13 17:09:37.640104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e7657f9cf5b6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='student', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('daily_capacity_minutes', sa.Integer(), server_default='300', nullable=False),
        sa.Column('weekly_capacity_hours', sa.Integer(), server_default='25', nullable=False),
        sa.Column('timezone', sa.String(length=100), server_default='UTC', nullable=False),
        sa.Column('focus_domains', sa.Text(), server_default='Software Engineering,AI', nullable=False),
        sa.Column('onboarding_completed', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('preferences_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # 3. goals table
    op.create_table(
        'goals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), server_default='career', nullable=False),
        sa.Column('target_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='in_progress', nullable=False),
        sa.Column('progress_pct', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_goals_user_id', 'goals', ['user_id'], unique=False)

    # 4. milestones table
    op.create_table(
        'milestones',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('goal_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_milestones_goal_id', 'milestones', ['goal_id'], unique=False)

    # 5. tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('goal_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), server_default='30', nullable=False),
        sa.Column('priority', sa.Integer(), server_default='2', nullable=False),
        sa.Column('energy_level', sa.Integer(), server_default='3', nullable=False),
        sa.Column('scheduled_start', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tasks_goal_id', 'tasks', ['goal_id'], unique=False)
    op.create_index('ix_tasks_status', 'tasks', ['status'], unique=False)
    op.create_index('ix_tasks_user_id', 'tasks', ['user_id'], unique=False)

    # 6. opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('organization', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), server_default='Remote', nullable=False),
        sa.Column('url', sa.String(length=512), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('eligibility', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_opportunities_category', 'opportunities', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_opportunities_category', table_name='opportunities')
    op.drop_table('opportunities')
    op.drop_index('ix_tasks_user_id', table_name='tasks')
    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_index('ix_tasks_goal_id', table_name='tasks')
    op.drop_table('tasks')
    op.drop_index('ix_milestones_goal_id', table_name='milestones')
    op.drop_table('milestones')
    op.drop_index('ix_goals_user_id', table_name='goals')
    op.drop_table('goals')
    op.drop_table('user_profiles')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
