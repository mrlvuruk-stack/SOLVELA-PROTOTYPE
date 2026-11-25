from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Tuple
import time

@dataclass
class OverdueTask:
    id: str
    title: str
    duration_minutes: int
    priority: int

@dataclass
class RebalancedTask:
    task_id: str
    target_date: date
    allocated_minutes: int

@dataclass
class DeferredTask:
    task_id: str
    title: str
    allocated_minutes: int
    reason: str

@dataclass
class IMTRResult:
    rebalanced_tasks: List[RebalancedTask] = field(default_factory=list)
    deferred_tasks: List[DeferredTask] = field(default_factory=list)
    final_daily_workloads: Dict[date, int] = field(default_factory=dict)
    execution_time_ms: float = 0.0

class IMTRRecoveryEngine:
    """
    Intelligent Missed-Task Recovery (IMTR) 3-Day Redistribution Engine.
    Hardened to enforce strict daily capacity caps without guilt badges or silent capacity violation.
    Target: Rebalances overdue tasks across D+1, D+2, D+3 in <200ms.
    """
    def __init__(self, daily_capacity_cap_minutes: int = 300):
        self.capacity_cap = daily_capacity_cap_minutes

    def rebalance_safe(
        self, 
        overdue_tasks: List[OverdueTask], 
        current_date: date, 
        existing_daily_workloads: Dict[date, int],
        recovery_days: int = 3
    ) -> IMTRResult:
        """
        Production IMTR Recovery:
        Greedy load-smoothing across recovery days (default 3 days: D+1, D+2, D+3).
        NEVER silently places a task on an overloaded day.
        Returns explicit deferred tasks when capacity cannot accommodate them.
        """
        start_time = time.perf_counter()
        
        target_dates = [current_date + timedelta(days=d) for d in range(1, recovery_days + 1)]
        workloads = {d: existing_daily_workloads.get(d, 0) for d in target_dates}
        
        # Sort overdue tasks descending by priority, then descending by duration
        sorted_tasks = sorted(overdue_tasks, key=lambda t: (t.priority, t.duration_minutes), reverse=True)
        
        rebalanced: List[RebalancedTask] = []
        deferred: List[DeferredTask] = []
        
        for task in sorted_tasks:
            # Find eligible dates where adding this task will NOT exceed capacity
            eligible_dates = [
                d for d in target_dates 
                if workloads[d] + task.duration_minutes <= self.capacity_cap
            ]
            
            if eligible_dates:
                # Greedy load smoothing: choose the eligible day with minimum current workload
                best_date = min(eligible_dates, key=lambda d: workloads[d])
                workloads[best_date] += task.duration_minutes
                rebalanced.append(RebalancedTask(
                    task_id=task.id,
                    target_date=best_date,
                    allocated_minutes=task.duration_minutes
                ))
            else:
                # Capacity cannot accommodate task in this window without violating safety caps!
                deferred.append(DeferredTask(
                    task_id=task.id,
                    title=task.title,
                    allocated_minutes=task.duration_minutes,
                    reason=f"CAPACITY_EXCEEDED_ACROSS_RECOVERY_WINDOW ({task.duration_minutes}m required, all days at or near {self.capacity_cap}m cap)"
                ))
                
        execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        return IMTRResult(
            rebalanced_tasks=rebalanced,
            deferred_tasks=deferred,
            final_daily_workloads=workloads,
            execution_time_ms=execution_time_ms
        )

    def rebalance(
        self, 
        overdue_tasks: List[OverdueTask], 
        current_date: date, 
        existing_daily_workloads: Dict[date, int]
    ) -> Tuple[List[RebalancedTask], float]:
        """
        Legacy benchmark-compatible method.
        Preserves original (rebalanced_tasks, exec_ms) return signature.
        """
        res = self.rebalance_safe(overdue_tasks, current_date, existing_daily_workloads)
        return res.rebalanced_tasks, res.execution_time_ms
