import pytest
from datetime import datetime, timedelta, timezone
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.scheduler import KnapsackScheduler, Task, FreeInterval

def test_scheduler_enforces_per_user_per_day_capacity():
    """
    Test that scheduler respects per-user, per-day capacity (e.g. 180 minutes for a working professional)
    without starving subsequent days.
    """
    user_daily_capacity = 180
    scheduler = KnapsackScheduler(daily_capacity_cap_minutes=user_daily_capacity, buffer_minutes=10)
    ref_time = datetime(2026, 11, 13, 8, 0, 0)
    
    # Day 1: 9:00 - 15:00 (360 mins of available intervals)
    # Day 2: 9:00 - 15:00 (360 mins of available intervals)
    intervals = [
        FreeInterval(start=ref_time + timedelta(hours=1), end=ref_time + timedelta(hours=7)), # Day 1: 360m
        FreeInterval(start=ref_time + timedelta(days=1, hours=1), end=ref_time + timedelta(days=1, hours=7)) # Day 2: 360m
    ]
    
    # 10 tasks of 45 mins each (total 450 mins)
    tasks = [
        Task(id=f"task-{i}", title=f"Deep Work #{i}", duration_minutes=45, priority=3)
        for i in range(10)
    ]
    
    result = scheduler.schedule_multi_day(tasks, intervals, ref_time, per_day_capacity_minutes=user_daily_capacity)
    
    # Placements on Day 1 must not exceed 180 minutes (4 tasks * 45 = 180 mins)
    day1_placements = [p for p in result.placements if p.start.date() == ref_time.date()]
    day1_mins = sum(p.duration_minutes for p in day1_placements)
    assert day1_mins <= user_daily_capacity, f"Day 1 exceeded user capacity: {day1_mins} > {user_daily_capacity}"
    assert day1_mins == 180, f"Expected 180 mins on Day 1, got {day1_mins}"
    
    # Placements on Day 2 must also not exceed 180 minutes
    day2_date = (ref_time + timedelta(days=1)).date()
    day2_placements = [p for p in result.placements if p.start.date() == day2_date]
    day2_mins = sum(p.duration_minutes for p in day2_placements)
    assert day2_mins <= user_daily_capacity, f"Day 2 exceeded user capacity: {day2_mins} > {user_daily_capacity}"
    assert day2_mins == 180, f"Expected 180 mins on Day 2, got {day2_mins}"

def test_scheduler_overlapping_intervals_handling():
    """
    Test that overlapping free intervals are sanitized/merged before placement to prevent collision.
    """
    scheduler = KnapsackScheduler(daily_capacity_cap_minutes=300)
    ref_time = datetime(2026, 11, 13, 9, 0, 0)
    
    # Two overlapping intervals: 9:00 - 11:00 and 10:00 - 12:00 -> should merge to 9:00 - 12:00 (180 mins)
    overlapping_intervals = [
        FreeInterval(start=ref_time, end=ref_time + timedelta(hours=2)),
        FreeInterval(start=ref_time + timedelta(hours=1), end=ref_time + timedelta(hours=3))
    ]
    
    tasks = [
        Task(id="task-1", title="Task 1", duration_minutes=60, priority=4),
        Task(id="task-2", title="Task 2", duration_minutes=60, priority=3),
        Task(id="task-3", title="Task 3", duration_minutes=40, priority=2)
    ]
    
    result = scheduler.schedule_multi_day(tasks, overlapping_intervals, ref_time)
    
    # Placements must not overlap with each other
    for i in range(len(result.placements) - 1):
        assert result.placements[i].end <= result.placements[i+1].start, "Placements collided on overlapping interval"

def test_scheduler_unplaceable_tasks_reporting():
    """
    Test that tasks which cannot fit due to duration exceeding available slots or capacity
    are reported explicitly in unplaced_tasks with reason.
    """
    scheduler = KnapsackScheduler(daily_capacity_cap_minutes=60)
    ref_time = datetime(2026, 11, 13, 9, 0, 0)
    
    # Only 1 interval of 60 minutes
    intervals = [FreeInterval(start=ref_time, end=ref_time + timedelta(minutes=60))]
    
    tasks = [
        Task(id="fit-1", title="Fit Task", duration_minutes=60, priority=4),
        Task(id="toolarge-2", title="Too Large Task", duration_minutes=90, priority=3),
        Task(id="overflow-3", title="Overflow Task", duration_minutes=30, priority=1)
    ]
    
    result = scheduler.schedule_multi_day(tasks, intervals, ref_time, per_day_capacity_minutes=60)
    
    assert len(result.placements) == 1
    assert result.placements[0].task_id == "fit-1"
    
    # Must report unplaced tasks
    unplaced_ids = {u.task_id: u.reason for u in result.unplaced_tasks}
    assert "toolarge-2" in unplaced_ids
    assert "overflow-3" in unplaced_ids
    print(f"Unplaced reasons: {unplaced_ids}")

def test_scheduler_timezone_and_deadline_edge_cases():
    """
    Test timezone awareness and prioritization of tasks approaching deadlines.
    """
    scheduler = KnapsackScheduler(daily_capacity_cap_minutes=300)
    ref_time = datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc)
    
    intervals = [FreeInterval(start=ref_time, end=ref_time + timedelta(hours=3))]
    
    # Task with near deadline (in 2 hours) vs far deadline (in 5 days)
    urgent_task = Task(
        id="urgent",
        title="Urgent Submission",
        duration_minutes=60,
        priority=2, # lower priority number
        deadline=ref_time + timedelta(hours=2) # imminent deadline!
    )
    normal_task = Task(
        id="normal",
        title="Regular Study",
        duration_minutes=60,
        priority=3,
        deadline=ref_time + timedelta(days=5)
    )
    
    result = scheduler.schedule_multi_day([normal_task, urgent_task], intervals, ref_time)
    
    # Urgent task must be placed first because urgency density is higher
    assert result.placements[0].task_id == "urgent"
