import pytest
from datetime import datetime, timedelta
import sys
import os

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.scheduler import KnapsackScheduler, Task, FreeInterval

def test_knapsack_scheduler_performance_and_constraints():
    """
    POC-1 Benchmark Test:
    - 50 unscheduled tasks with varying priorities and deadlines.
    - 15 open calendar intervals.
    - Acceptance: Solves in <350ms, zero overlapping appointments, enforces 5h capacity cap.
    """
    scheduler = KnapsackScheduler(daily_capacity_cap_minutes=300, buffer_minutes=10)
    ref_time = datetime(2026, 11, 13, 8, 0, 0)
    
    # Generate 50 synthetic tasks
    tasks = [
        Task(
            id=f"task-{i}",
            title=f"Study Subject Block #{i}",
            duration_minutes=30 if i % 2 == 0 else 45,
            priority=(i % 4) + 1,
            deadline=ref_time + timedelta(days=(i % 5) + 1)
        )
        for i in range(50)
    ]
    
    # Generate 15 free calendar intervals across 3 days
    intervals = []
    current_day = ref_time
    for d in range(3):
        day_base = current_day + timedelta(days=d)
        intervals.extend([
            FreeInterval(start=day_base + timedelta(hours=9), end=day_base + timedelta(hours=11)),
            FreeInterval(start=day_base + timedelta(hours=12), end=day_base + timedelta(hours=14)),
            FreeInterval(start=day_base + timedelta(hours=15), end=day_base + timedelta(hours=17)),
            FreeInterval(start=day_base + timedelta(hours=18), end=day_base + timedelta(hours=20)),
            FreeInterval(start=day_base + timedelta(hours=21), end=day_base + timedelta(hours=22, minutes=30)),
        ])
        
    placements, exec_ms = scheduler.schedule(tasks, intervals, ref_time)
    
    print(f"\n[POC-1 Knapsack Scheduler] Execution Time: {exec_ms:.2f} ms | Placed Tasks: {len(placements)}")
    
    # 1. Performance budget check
    assert exec_ms < 350.0, f"Scheduler took {exec_ms:.2f}ms, exceeding 350ms budget!"
    
    # 2. Capacity cap check (max 300 minutes scheduled for Day 1)
    total_minutes = sum(p.duration_minutes for p in placements)
    assert total_minutes <= 300, f"Scheduled {total_minutes}m, exceeding 300m capacity cap!"
    
    # 3. Non-overlapping intervals check
    for i in range(len(placements) - 1):
        assert placements[i].end <= placements[i+1].start, (
            f"Overlapping intervals detected between {placements[i]} and {placements[i+1]}"
        )
        
    assert len(placements) > 0, "Scheduler failed to place any tasks!"
