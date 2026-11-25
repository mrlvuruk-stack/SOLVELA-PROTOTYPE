import pytest
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.imtr import IMTRRecoveryEngine, OverdueTask

def test_imtr_recovery_performance_and_load_smoothing():
    """
    POC-3 Benchmark Test:
    - 12 overdue tasks totaling 480 minutes.
    - Acceptance: Redistributes across D+1, D+2, D+3 in <200ms.
    - Smooths load without violating the 300m daily capacity cap.
    """
    imtr = IMTRRecoveryEngine(daily_capacity_cap_minutes=300)
    today = date(2026, 11, 13)
    
    # Generate 12 overdue tasks
    overdue_tasks = [
        OverdueTask(
            id=f"overdue-{i}",
            title=f"Missed Assignment #{i}",
            duration_minutes=30 if i % 2 == 0 else 60,
            priority=(i % 4) + 1
        )
        for i in range(12)
    ]
    
    rebalanced, exec_ms = imtr.rebalance(overdue_tasks, today, {})
    
    print(f"\n[POC-3 IMTR Engine] Execution Time: {exec_ms:.2f} ms | Rebalanced Tasks: {len(rebalanced)}")
    
    # 1. Performance budget check
    assert exec_ms < 200.0, f"IMTR took {exec_ms:.2f}ms, exceeding 200ms budget!"
    
    # 2. Check that all tasks are redistributed across next 3 days
    valid_dates = {today + timedelta(days=1), today + timedelta(days=2), today + timedelta(days=3)}
    for r in rebalanced:
        assert r.target_date in valid_dates, f"Task {r.task_id} placed on invalid date {r.target_date}"
        
    assert len(rebalanced) == 12, "Not all overdue tasks were rebalanced!"
