import pytest
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.imtr import IMTRRecoveryEngine, OverdueTask, IMTRResult

def test_imtr_never_silently_violates_capacity():
    """
    Finding 4 Test: IMTR must never silently place tasks on overloaded days.
    If no day has capacity, it must return an explicit deferred/unscheduled result.
    """
    imtr = IMTRRecoveryEngine(daily_capacity_cap_minutes=300)
    today = date(2026, 11, 13)
    
    # Days D+1, D+2, D+3 already have 270 minutes each (only 30 mins available each)
    existing_workloads = {
        today + timedelta(days=1): 270,
        today + timedelta(days=2): 270,
        today + timedelta(days=3): 270,
    }
    
    # Overdue task of 60 minutes cannot fit in any day without exceeding 300 min cap
    overdue_tasks = [
        OverdueTask(id="heavy-1", title="Heavy Research Paper", duration_minutes=60, priority=4)
    ]
    
    result: IMTRResult = imtr.rebalance_safe(overdue_tasks, today, existing_workloads)
    
    # Must NOT be placed on an overloaded day
    assert len(result.rebalanced_tasks) == 0, "Task was placed on an overloaded day in violation of capacity!"
    
    # Must be explicitly deferred
    assert len(result.deferred_tasks) == 1
    assert result.deferred_tasks[0].task_id == "heavy-1"
    assert "CAPACITY_EXCEEDED" in result.deferred_tasks[0].reason

def test_imtr_partial_rebalance_and_deferred_tasks():
    """
    Test when some tasks fit within the 3-day recovery window and others exceed capacity.
    """
    imtr = IMTRRecoveryEngine(daily_capacity_cap_minutes=300)
    today = date(2026, 11, 13)
    
    # Only Day 1 has room for 45 minutes; Days 2 and 3 are completely full
    existing_workloads = {
        today + timedelta(days=1): 255, # 45m left
        today + timedelta(days=2): 300, # 0m left
        today + timedelta(days=3): 300, # 0m left
    }
    
    overdue_tasks = [
        OverdueTask(id="task-high", title="Urgent High Priority", duration_minutes=45, priority=4),
        OverdueTask(id="task-low", title="Low Priority Extra", duration_minutes=45, priority=1)
    ]
    
    result = imtr.rebalance_safe(overdue_tasks, today, existing_workloads)
    
    # High priority should get the remaining 45 min slot on Day 1
    assert len(result.rebalanced_tasks) == 1
    assert result.rebalanced_tasks[0].task_id == "task-high"
    assert result.rebalanced_tasks[0].target_date == today + timedelta(days=1)
    
    # Low priority must be deferred, not crammed into Day 2 or 3
    assert len(result.deferred_tasks) == 1
    assert result.deferred_tasks[0].task_id == "task-low"
    assert result.deferred_tasks[0].allocated_minutes == 45
