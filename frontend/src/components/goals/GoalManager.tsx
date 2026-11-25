"use client";

import React, { useState, useEffect } from "react";
import { Target, Plus, CheckCircle2, Circle, Calendar, Sparkles, Layers, Trash2 } from "lucide-react";
import { apiFetch, UserSession } from "../../lib/api";

interface GoalManagerProps {
  session: UserSession | null;
  onOpenAuth: () => void;
}

export function GoalManager({ session, onOpenAuth }: GoalManagerProps) {
  const [goals, setGoals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [decomposingId, setDecomposingId] = useState<string | null>(null);
  const [bannerMsg, setBannerMsg] = useState<string | null>(null);

  // Form State
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("career");
  const [description, setDescription] = useState("");
  const [targetDays, setTargetDays] = useState(60);
  const [m1, setM1] = useState("");
  const [m2, setM2] = useState("");

  async function loadGoals() {
    if (!session) return;
    setLoading(true);
    try {
      const data = await apiFetch<any[]>("/goals");
      setGoals(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadGoals();
  }, [session]);

  async function handleCreateGoal(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !session) return;

    const milestones = [];
    if (m1.trim()) milestones.push({ title: m1 });
    if (m2.trim()) milestones.push({ title: m2 });

    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + targetDays);

    try {
      await apiFetch("/goals", {
        method: "POST",
        body: JSON.stringify({
          title,
          category,
          description,
          target_date: targetDate.toISOString(),
          milestones,
        }),
      });
      setTitle("");
      setDescription("");
      setM1("");
      setM2("");
      setIsModalOpen(false);
      setBannerMsg("SMART Goal created successfully!");
      loadGoals();
    } catch (err: any) {
      alert(`Error creating goal: ${err.message}`);
    }
  }

  async function handleDecompose(goalId: string, goalTitle: string) {
    setDecomposingId(goalId);
    setBannerMsg(null);
    try {
      const tasks: any[] = await apiFetch(`/goals/${goalId}/decompose`, {
        method: "POST",
      });
      setBannerMsg(`AI Planner decomposed "${goalTitle}" into ${tasks.length} actionable micro-tasks in your task pool.`);
      loadGoals();
    } catch (err: any) {
      alert(`Decomposition failed: ${err.message}`);
    } finally {
      setDecomposingId(null);
    }
  }

  async function handleDeleteGoal(goalId: string) {
    if (!confirm("Are you sure you want to delete this goal? Linked milestones will be removed.")) return;
    try {
      await apiFetch(`/goals/${goalId}`, { method: "DELETE" });
      setBannerMsg("Goal removed.");
      loadGoals();
    } catch (err: any) {
      alert(`Failed to delete: ${err.message}`);
    }
  }

  if (!session) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-center">
        <div className="bg-sovela-card border border-sovela-border rounded-2xl p-8 max-w-xl mx-auto shadow-2xl">
          <Target className="h-10 w-10 text-sovela-teal mx-auto mb-3" />
          <h2 className="text-xl font-bold text-white">SMART Goal Management</h2>
          <p className="text-sm text-sovela-text-muted mt-2 mb-6">
            Sign in to define your high-impact objectives, track milestone progression, and let Sovela AI schedule micro-actions.
          </p>
          <button
            onClick={onOpenAuth}
            className="px-6 py-2.5 rounded-xl bg-sovela-teal hover:bg-sky-400 text-white font-medium text-sm transition"
          >
            Sign In to Manage Goals
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 lg:px-8 space-y-6">
      {/* Header & Add Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Active Goals & Milestones</h2>
          <p className="text-xs text-sovela-text-muted mt-0.5">
            Structured SMART objectives with automated AI decomposition into daily micro-tasks.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 rounded-xl bg-sovela-teal hover:bg-sky-400 text-white font-medium text-xs transition flex items-center shadow-lg shadow-sovela-teal/10"
        >
          <Plus className="h-4 w-4 mr-1.5" /> New SMART Goal
        </button>
      </div>

      {bannerMsg && (
        <div className="p-3.5 rounded-xl bg-sovela-teal/10 border border-sovela-teal/20 text-sovela-teal text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-4 w-4 shrink-0" />
            <span>{bannerMsg}</span>
          </div>
          <button onClick={() => setBannerMsg(null)} className="text-slate-400 hover:text-white text-xs">
            ✕
          </button>
        </div>
      )}

      {/* Goals Grid */}
      {goals.length === 0 ? (
        <div className="bg-sovela-card border border-sovela-border rounded-2xl p-12 text-center max-w-lg mx-auto">
          <Target className="h-8 w-8 text-slate-500 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-white">No active goals yet</h3>
          <p className="text-xs text-sovela-text-muted mt-1">
            Click "New SMART Goal" to set up your primary career or academic objective.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {goals.map((g) => (
            <div
              key={g.id}
              className="bg-sovela-card border border-sovela-border rounded-2xl p-6 shadow-xl flex flex-col justify-between relative overflow-hidden"
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-mono text-sovela-teal uppercase text-[10px] tracking-wider font-bold px-2 py-0.5 rounded-full bg-sovela-teal/10 border border-sovela-teal/20">
                    {g.category}
                  </span>
                  <div className="flex items-center space-x-3">
                    <span className="text-sovela-text-muted flex items-center space-x-1 text-[11px]">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>
                        {g.target_date ? new Date(g.target_date).toLocaleDateString() : "Ongoing"}
                      </span>
                    </span>
                    <button
                      onClick={() => handleDeleteGoal(g.id)}
                      className="text-slate-500 hover:text-rose-400 transition"
                      title="Delete goal"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                <h3 className="text-base font-bold text-white">{g.title}</h3>
                {g.description && (
                  <p className="text-xs text-sovela-text-muted mt-1.5 line-clamp-2">{g.description}</p>
                )}

                {/* Progress Bar */}
                <div className="w-full bg-slate-900 rounded-full h-2 mt-4 overflow-hidden border border-sovela-border">
                  <div
                    className="bg-sovela-teal h-full rounded-full transition-all"
                    style={{ width: `${Math.max(10, g.progress_pct || 15)}%` }}
                  />
                </div>
              </div>

              {/* Milestones Checklist */}
              <div className="mt-5 pt-4 border-t border-sovela-border">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-semibold text-slate-300">Milestones ({g.milestones?.length || 0})</h4>
                  <button
                    onClick={() => handleDecompose(g.id, g.title)}
                    disabled={decomposingId === g.id}
                    className="text-[11px] font-semibold text-sovela-teal hover:text-sky-300 transition flex items-center space-x-1 disabled:opacity-50"
                  >
                    <Sparkles className="h-3 w-3" />
                    <span>{decomposingId === g.id ? "Decomposing..." : "AI Decompose to Tasks"}</span>
                  </button>
                </div>

                <div className="space-y-1.5">
                  {g.milestones && g.milestones.length > 0 ? (
                    g.milestones.map((m: any) => (
                      <div key={m.id} className="flex items-center space-x-2 text-xs text-slate-300">
                        {m.is_completed ? (
                          <CheckCircle2 className="h-4 w-4 text-sovela-green shrink-0" />
                        ) : (
                          <Circle className="h-4 w-4 text-slate-500 shrink-0" />
                        )}
                        <span className={m.is_completed ? "line-through text-slate-500" : ""}>{m.title}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-[11px] text-slate-500 italic">
                      Click "AI Decompose to Tasks" to auto-generate micro-action items.
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Goal Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="bg-sovela-card border border-sovela-border rounded-2xl p-6 w-full max-w-lg shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4">Create SMART Goal</h3>
            <form onSubmit={handleCreateGoal} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-sovela-text-muted mb-1">Goal Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Master Distributed Systems Architecture"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-sovela-text-muted mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                  >
                    <option value="career">Career</option>
                    <option value="academic">Academic</option>
                    <option value="skill">Skill</option>
                    <option value="personal">Personal</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-sovela-text-muted mb-1">Target Horizon</label>
                  <select
                    value={targetDays}
                    onChange={(e) => setTargetDays(parseInt(e.target.value))}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                  >
                    <option value={30}>30 Days (Sprint)</option>
                    <option value={60}>60 Days (Quarter)</option>
                    <option value={90}>90 Days (Horizon)</option>
                    <option value={180}>6 Months (Milestone)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-sovela-text-muted mb-1">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Explain why this objective matters and what success looks like..."
                  className="w-full px-3.5 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-sovela-text-muted mb-1">Milestones (Key Results)</label>
                <div className="space-y-2">
                  <input
                    type="text"
                    value={m1}
                    onChange={(e) => setM1(e.target.value)}
                    placeholder="Key Result 1: Build working Raft leader election"
                    className="w-full px-3.5 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                  />
                  <input
                    type="text"
                    value={m2}
                    onChange={(e) => setM2(e.target.value)}
                    placeholder="Key Result 2: Implement log compaction and benchmark throughput"
                    className="w-full px-3.5 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-sovela-border">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-sovela-border text-slate-300 text-xs hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-sovela-teal hover:bg-sky-400 text-white font-medium text-xs transition shadow-md shadow-sovela-teal/10"
                >
                  Create Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
