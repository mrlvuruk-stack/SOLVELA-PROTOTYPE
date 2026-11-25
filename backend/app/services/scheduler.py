from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Tuple
import time

@dataclass
class Task:
    id: str
    title: str
    duration_minutes: int
    priority: int  # 1 (Low) to 4 (Urgent)
    deadline: Optional[datetime] = None
    required_energy_level: int = 3  # 1 to 5

@dataclass
class FreeInterval:
    start: datetime
    end: datetime

@dataclass
class Placement:
    task_id: str
    title: str
    start: datetime
    end: datetime
    duration_minutes: int

@dataclass
class UnplacedTask:
    task_id: str
    title: str
    duration_minutes: int
    reason: str

@dataclass
class ScheduleResult:
    placements: List[Placement] = field(default_factory=list)
    unplaced_tasks: List[UnplacedTask] = field(default_factory=list)
    daily_allocated_minutes: Dict[date, int] = field(default_factory=dict)
    execution_time_ms: float = 0.0

class KnapsackScheduler:
    """
    Heuristic Knapsack Interval Placement Solver with Per-User Per-Day Capacity Enforcement.
    Solves 50 tasks across calendar intervals in <350ms.
    """
    def __init__(self, daily_capacity_cap_minutes: int = 300, buffer_minutes: int = 10):
        self.capacity_cap = daily_capacity_cap_minutes
        self.buffer = buffer_minutes

    def sanitize_intervals(self, intervals: List[FreeInterval]) -> List[FreeInterval]:
        """
        Sorts and merges overlapping free intervals to eliminate scheduling collisions.
        """
        if not intervals:
            return []
        sorted_intervals = sorted(intervals, key=lambda i: i.start)
        merged: List[FreeInterval] = [sorted_intervals[0]]
        
        for current in sorted_intervals[1:]:
            prev = merged[-1]
            if current.start < prev.end:
                # Overlap detected - merge intervals
                merged[-1] = FreeInterval(start=prev.start, end=max(prev.end, current.end))
            else:
                merged.append(current)
        return merged

    def calculate_efficiency(self, task: Task, reference_time: datetime) -> float:
        """
        Computes dynamic efficiency density: Value / Duration.
        Priority weight: 2.0, Urgency weight: 1.5.
        """
        urgency = 1.0
        if task.deadline:
            # Handle timezone-aware vs naive comparisons safely
            if reference_time.tzinfo is not None and task.deadline.tzinfo is None:
                deadline_normalized = task.deadline.replace(tzinfo=reference_time.tzinfo)
            elif reference_time.tzinfo is None and task.deadline.tzinfo is not None:
                deadline_normalized = task.deadline.replace(tzinfo=None)
            else:
                deadline_normalized = task.deadline
                
            seconds_left = (deadline_normalized - reference_time).total_seconds()
            days_left = max(0.01, seconds_left / 86400.0)
            urgency = max(1.0, 2.0 / days_left)
            
        value = (task.priority * 2.0) + (urgency * 1.5)
        return value / max(15, task.duration_minutes)

    def schedule(self, tasks: List[Task], free_intervals: List[FreeInterval], reference_time: datetime) -> Tuple[List[Placement], float]:
        """
        Legacy benchmark-compatible scheduling interface.
        Enforces global capacity cap for POC-1 benchmark.
        """
        start_time = time.perf_counter()
        sorted_tasks = sorted(
            tasks, 
            key=lambda t: self.calculate_efficiency(t, reference_time), 
            reverse=True
        )
        
        placements: List[Placement] = []
        total_scheduled = 0
        
        sanitized = self.sanitize_intervals(free_intervals)
        
        for interval in sanitized:
            current_time = interval.start
            while current_time < interval.end and sorted_tasks:
                available_mins = (interval.end - current_time).total_seconds() / 60.0
                
                candidate = None
                for t in sorted_tasks:
                    if t.duration_minutes <= available_mins:
                        candidate = t
                        break
                        
                if not candidate:
                    break
                    
                if total_scheduled + candidate.duration_minutes > self.capacity_cap:
                    break
                    
                end_time = current_time + timedelta(minutes=candidate.duration_minutes)
                placements.append(Placement(
                    task_id=candidate.id,
                    title=candidate.title,
                    start=current_time,
                    end=end_time,
                    duration_minutes=candidate.duration_minutes
                ))
                
                total_scheduled += candidate.duration_minutes
                current_time = end_time + timedelta(minutes=self.buffer)
                sorted_tasks.remove(candidate)
                
            if total_scheduled >= self.capacity_cap:
                break
                
        execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        return placements, execution_time_ms

    def schedule_multi_day(
        self, 
        tasks: List[Task], 
        free_intervals: List[FreeInterval], 
        reference_time: datetime,
        per_day_capacity_minutes: Optional[int] = None
    ) -> ScheduleResult:
        """
        Production Multi-Day Knapsack Scheduler.
        Enforces per-user, per-day capacity constraints.
        Returns explicit unplaced tasks and daily allocations.
        """
        start_time = time.perf_counter()
        daily_cap = per_day_capacity_minutes if per_day_capacity_minutes is not None else self.capacity_cap
        
        sanitized_intervals = self.sanitize_intervals(free_intervals)
        
        # Sort tasks descending by efficiency density
        sorted_tasks = sorted(
            tasks, 
            key=lambda t: self.calculate_efficiency(t, reference_time), 
            reverse=True
        )
        
        placements: List[Placement] = []
        daily_allocations: Dict[date, int] = {}
        placed_task_ids = set()
        
        for interval in sanitized_intervals:
            interval_date = interval.start.date()
            if interval_date not in daily_allocations:
                daily_allocations[interval_date] = 0
                
            current_time = interval.start
            
            while current_time < interval.end:
                current_day_used = daily_allocations[interval_date]
                if current_day_used >= daily_cap:
                    break # Day capacity cap reached
                    
                available_mins = (interval.end - current_time).total_seconds() / 60.0
                remaining_day_cap = daily_cap - current_day_used
                
                candidate = None
                for t in sorted_tasks:
                    if t.id not in placed_task_ids:
                        if t.duration_minutes <= available_mins and t.duration_minutes <= remaining_day_cap:
                            candidate = t
                            break
                            
                if not candidate:
                    break # No remaining task fits into this interval or remaining day capacity
                    
                end_time = current_time + timedelta(minutes=candidate.duration_minutes)
                placements.append(Placement(
                    task_id=candidate.id,
                    title=candidate.title,
                    start=current_time,
                    end=end_time,
                    duration_minutes=candidate.duration_minutes
                ))
                
                daily_allocations[interval_date] += candidate.duration_minutes
                placed_task_ids.add(candidate.id)
                current_time = end_time + timedelta(minutes=self.buffer)
                
        # Determine unplaced tasks and why
        unplaced_tasks: List[UnplacedTask] = []
        for t in sorted_tasks:
            if t.id not in placed_task_ids:
                if t.duration_minutes > daily_cap:
                    reason = f"EXCEEDS_DAILY_CAPACITY ({t.duration_minutes}m > {daily_cap}m cap)"
                else:
                    reason = "NO_FITTING_FREE_INTERVAL_OR_CAPACITY_EXHAUSTED"
                unplaced_tasks.append(UnplacedTask(
                    task_id=t.id,
                    title=t.title,
                    duration_minutes=t.duration_minutes,
                    reason=reason
                ))
                
        exec_ms = (time.perf_counter() - start_time) * 1000.0
        return ScheduleResult(
            placements=placements,
            unplaced_tasks=unplaced_tasks,
            daily_allocated_minutes=daily_allocations,
            execution_time_ms=exec_ms
        )
