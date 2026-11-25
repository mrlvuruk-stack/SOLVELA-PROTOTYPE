"use client";

import React, { useState, useEffect } from "react";
import { 
  Sparkles, CheckCircle2, Circle, Clock, Flame, 
  Play, Pause, RotateCcw, AlertTriangle, ArrowRight, Plus 
} from "lucide-react";
import { apiFetch, UserSession } from "../../lib/api";

interface TodayViewProps {
  session: UserSession | null;
  onOpenAuth: () => void;
}

export function TodayView({ session, onOpenAuth }: TodayViewProps) {
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  // Quick Task Form
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDuration, setNewTaskDuration] = useState(45);
  const [newTaskPriority, setNewTaskPriority] = useState(3);

  // Pomodoro State
  const [pomoSeconds, setPomoSeconds] = useState(25 * 60);
  const [pomoActive, setPomoActive] = useState(false);

  useEffect(() => {
    let interval: any = null;
    if (pomoActive && pomoSeconds > 0) {
      interval = setInterval(() => setPomoSeconds((s) => s - 1), 1000);
    } else if (pomoSeconds === 0) {
      setPomoActive(false);
    }
    return () => clearInterval(interval);
  }, [pomoActive, pomoSeconds]);

  function formatPomoTime(secs: number) {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }

  async function loadDashboard() {
    if (!session) return;
    setLoading(true);
    try {
      const data = await apiFetch<any>("/dashboard/today");
      setDashboard(data);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, [session]);

  async function handleCreateTask(e: React.FormEvent) {
    e.preventDefault();
    if (!newTaskTitle.trim() || !session) return;
    try {
      await apiFetch("/tasks", {
        method: "POST",
        body: JSON.stringify({
          title: newTaskTitle,
          duration_minutes: newTaskDuration,
          priority: newTaskPriority,
        }),
      });
      setNewTaskTitle("");
      setActionMsg("Task added successfully");
      loadDashboard();
    } catch (err: any) {
      setActionMsg(`Failed to add task: ${err.message}`);
    }
  }

  async function handleCompleteTask(taskId: string) {
    if (!session) return;
    try {
      await apiFetch(`/tasks/${taskId}/complete`, { method: "PUT" });
      loadDashboard();
    } catch (err: any) {
      console.error(err);
    }
  }

  async function handleRunAutoSchedule() {
    if (!session) return;
    setActionMsg("Running Knapsack Heuristic Scheduler...");
    try {
      const res: any = await apiFetch("/temporal/auto-schedule", {
        method: "POST",
        body: JSON.stringify({ use_persistent_tasks: true }),
      });
      setActionMsg(`Scheduled ${res.placements_count} tasks in ${res.execution_time_ms} ms (Target Met: ${res.target_met})`);
      loadDashboard();
    } catch (err: any) {
      setActionMsg(`Scheduler error: ${err.message}`);
    }
  }

  async function handleRunIMTR() {
    if (!session) return;
    setActionMsg("Executing IMTR 3-Day Load Smoothing...");
    try {
      const res: any = await apiFetch("/temporal/imtr/rebalance", {
        method: "POST",
        body: JSON.stringify({ use_persistent_missed: true }),
      });
      setActionMsg(`Rebalanced ${res.rebalanced_count} missed tasks across 3 days in ${res.execution_time_ms} ms`);
      loadDashboard();
    } catch (err: any) {
      setActionMsg(`IMTR error: ${err.message}`);
    }
  }

  if (!session) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-center">
        <div className="bg-sovela-card border border-sovela-border rounded-2xl p-8 max-w-xl mx-auto shadow-2xl">
          <div className="h-12 w-12 rounded-2xl bg-sovela-teal/15 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="h-6 w-6 text-sovela-teal" />
          </div>
          <h2 className="text-xl font-bold text-white">Experience Sovela Today View</h2>
          <p className="text-sm text-sovela-text-muted mt-2 mb-6">
            Sign in or create your student/professional profile to see your Top 3 Rocks, 
            burnout-safe cognitive capacity progress, and AI-scheduled timeline.
          </p>
          <button
            onClick={onOpenAuth}
            className="px-6 py-2.5 rounded-xl bg-sovela-teal hover:bg-sky-400 text-white font-medium text-sm transition shadow-lg shadow-sovela-teal/20"
          >
            Sign In or Register
          </button>
        </div>
      </div>
    );
  }

  const capacity = dashboard?.capacity || {
    scheduled_minutes: 0,
    daily_capacity_minutes: session.user.profile?.daily_capacity_minutes || 300,
    utilization_pct: 0,
    burnout_risk: "low",
  };

  const topRocks = dashboard?.top_rocks || [];
  const tasks = dashboard?.tasks || [];

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 lg:px-8 space-y-6">
      {/* Action Notification Banner */}
      {actionMsg && (
        <div className="p-3.5 rounded-xl bg-sovela-card border border-sovela-teal/40 text-xs font-mono text-sovela-teal flex items-center justify-between shadow-lg">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-4 w-4 animate-spin" />
            <span>{actionMsg}</span>
          </div>
          <button onClick={() => setActionMsg(null)} className="text-sovela-text-muted hover:text-white">✕</button>
        </div>
      )}

      {/* Hero Strip: Top 3 Rocks & Capacity Meter */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top 3 Rocks (2 Cols) */}
        <div className="lg:col-span-2 bg-sovela-card border border-sovela-border rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2.5">
              <Flame className="h-5 w-5 text-sovela-amber" />
              <h2 className="font-bold text-white text-base tracking-tight">Today's Top 3 Rocks</h2>
            </div>
            <span className="text-xs text-sovela-text-muted">High cognitive impact</span>
          </div>

          {topRocks.length === 0 ? (
            <div className="p-6 text-center border border-dashed border-sovela-border rounded-xl">
              <p className="text-xs text-sovela-text-muted">No high-priority tasks yet. Create a task below to focus your day.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {topRocks.map((rock: any, idx: number) => (
                <div
                  key={rock.id}
                  className="p-4 rounded-xl bg-slate-900/60 border border-sovela-border flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between text-xs text-sovela-text-muted mb-2">
                      <span className="font-mono text-sovela-teal font-semibold">Rock #{idx + 1}</span>
                      <span className="flex items-center space-x-1">
                        <Clock className="h-3 w-3" />
                        <span>{rock.duration_minutes}m</span>
                      </span>
                    </div>
                    <div className="font-semibold text-white text-sm line-clamp-2">{rock.title}</div>
                  </div>
                  <button
                    onClick={() => handleCompleteTask(rock.id)}
                    className="mt-3 flex items-center space-x-1.5 text-xs text-sovela-teal hover:text-sky-300 font-medium"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Complete</span>
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* AI Orchestration Actions */}
          <div className="mt-5 pt-4 border-t border-sovela-border flex flex-wrap items-center gap-3">
            <button
              onClick={handleRunAutoSchedule}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-sovela-teal/15 hover:bg-sovela-teal/25 border border-sovela-teal text-white text-xs font-semibold transition"
            >
              <Sparkles className="h-3.5 w-3.5 text-sovela-teal" />
              <span>Auto-Schedule Plan (Knapsack AI)</span>
            </button>
            <button
              onClick={handleRunIMTR}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-sovela-border text-slate-200 text-xs font-medium transition"
            >
              <Clock className="h-3.5 w-3.5 text-blue-400" />
              <span>IMTR 3-Day Load Smoothing</span>
            </button>
          </div>
        </div>

        {/* Cognitive Capacity Gauge & Pomodoro (1 Col) */}
        <div className="bg-sovela-card border border-sovela-border rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-white text-sm">Cognitive Capacity Meter</h3>
              <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                capacity.burnout_risk === "optimal" ? "bg-sovela-green/20 text-sovela-green" :
                capacity.burnout_risk === "caution" ? "bg-sovela-amber/20 text-sovela-amber" :
                capacity.burnout_risk === "overloaded" ? "bg-sovela-rose/20 text-sovela-rose" :
                "bg-slate-800 text-slate-400"
              }`}>
                {capacity.burnout_risk} risk
              </span>
            </div>
            
            <div className="flex items-baseline space-x-1.5 mt-2">
              <span className="text-2xl font-bold text-white">{capacity.scheduled_minutes}m</span>
              <span className="text-xs text-sovela-text-muted">/ {capacity.daily_capacity_minutes}m cap (5.0h)</span>
            </div>

            {/* Capacity Progress Bar */}
            <div className="w-full bg-slate-900 rounded-full h-3 mt-3 overflow-hidden border border-sovela-border">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  capacity.utilization_pct > 90 ? "bg-sovela-rose" :
                  capacity.utilization_pct > 75 ? "bg-sovela-amber" :
                  "bg-sovela-teal"
                }`}
                style={{ width: `${Math.min(100, capacity.utilization_pct)}%` }}
              />
            </div>
            <p className="text-[11px] text-sovela-text-muted mt-2">
              Cap prevents cognitive exhaustion and sustains daily deep work streaks.
            </p>
          </div>

          {/* Pomodoro Timer Mini Widget */}
          <div className="mt-6 pt-4 border-t border-sovela-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white">Focus Timer (25/5)</span>
              <span className="font-mono text-lg font-bold text-sovela-teal">{formatPomoTime(pomoSeconds)}</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPomoActive(!pomoActive)}
                className="flex-1 py-1.5 rounded-lg bg-sovela-teal/20 hover:bg-sovela-teal/30 border border-sovela-teal/40 text-xs font-semibold text-white flex items-center justify-center space-x-1 transition"
              >
                {pomoActive ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                <span>{pomoActive ? "Pause" : "Start Focus"}</span>
              </button>
              <button
                onClick={() => {
                  setPomoActive(false);
                  setPomoSeconds(25 * 60);
                }}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sovela-text-muted transition"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Task Creation Form & Timeline List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Task Creation */}
        <div className="bg-sovela-card border border-sovela-border rounded-2xl p-6 shadow-xl">
          <h3 className="font-bold text-white text-sm mb-4 flex items-center space-x-2">
            <Plus className="h-4 w-4 text-sovela-teal" />
            <span>Create New Task</span>
          </h3>

          <form onSubmit={handleCreateTask} className="space-y-3.5">
            <div>
              <label className="block text-xs font-medium text-sovela-text-muted mb-1">Title</label>
              <input
                type="text"
                required
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder="e.g. Solve 3 LeetCode Graph problems"
                className="w-full bg-slate-900 border border-sovela-border rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sovela-teal"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-sovela-text-muted mb-1">Duration</label>
                <select
                  value={newTaskDuration}
                  onChange={(e) => setNewTaskDuration(parseInt(e.target.value))}
                  className="w-full bg-slate-900 border border-sovela-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sovela-teal"
                >
                  <option value={15}>15 mins</option>
                  <option value={30}>30 mins</option>
                  <option value={45}>45 mins</option>
                  <option value={60}>60 mins</option>
                  <option value={90}>90 mins</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-sovela-text-muted mb-1">Priority</label>
                <select
                  value={newTaskPriority}
                  onChange={(e) => setNewTaskPriority(parseInt(e.target.value))}
                  className="w-full bg-slate-900 border border-sovela-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-sovela-teal"
                >
                  <option value={1}>1 - Low</option>
                  <option value={2}>2 - Medium</option>
                  <option value={3}>3 - High</option>
                  <option value={4}>4 - Urgent Rock</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-2 rounded-lg bg-sovela-teal hover:bg-sky-400 text-white font-medium text-xs transition shadow-md shadow-sovela-teal/20"
            >
              Add to Today's Backlog
            </button>
          </form>
        </div>

        {/* Task Timeline / List (2 Cols) */}
        <div className="lg:col-span-2 bg-sovela-card border border-sovela-border rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white text-sm">Scheduled Work & Backlog</h3>
            <span className="text-xs text-sovela-text-muted">{tasks.length} total tasks</span>
          </div>

          {tasks.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-sovela-border rounded-xl">
              <p className="text-xs text-sovela-text-muted">No tasks currently registered. Add your first task on the left.</p>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
              {tasks.map((task: any) => {
                const isDone = task.status === "completed";
                return (
                  <div
                    key={task.id}
                    className={`p-3.5 rounded-xl border flex items-center justify-between transition ${
                      isDone
                        ? "bg-slate-900/30 border-slate-800 text-slate-500"
                        : "bg-slate-900/70 border-sovela-border text-white"
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => handleCompleteTask(task.id)}
                        className="text-sovela-teal hover:text-sky-300"
                      >
                        {isDone ? <CheckCircle2 className="h-5 w-5 text-sovela-green" /> : <Circle className="h-5 w-5 text-slate-500 hover:text-sovela-teal" />}
                      </button>
                      <div>
                        <div className={`text-sm font-medium ${isDone ? "line-through text-slate-500" : "text-white"}`}>
                          {task.title}
                        </div>
                        <div className="flex items-center space-x-2 text-[11px] text-sovela-text-muted mt-0.5">
                          <span>{task.duration_minutes}m</span>
                          <span>•</span>
                          <span className={task.priority >= 3 ? "text-sovela-amber font-semibold" : ""}>
                            Priority {task.priority}
                          </span>
                          {task.scheduled_start && (
                            <>
                              <span>•</span>
                              <span className="text-sovela-teal font-mono">
                                {new Date(task.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase ${
                      isDone ? "bg-sovela-green/15 text-sovela-green" :
                      task.status === "in_progress" ? "bg-sovela-teal/15 text-sovela-teal" :
                      "bg-slate-800 text-slate-400"
                    }`}>
                      {task.status}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
