"use client";

import React, { useState, useEffect } from "react";
import { Zap, Award, Star, CheckCircle, RefreshCw, BarChart2 } from "lucide-react";
import { apiFetch, UserSession } from "../../lib/api";

interface SkillItem {
  id: string;
  name: string;
  category: string;
  description: string | null;
  level: "beginner" | "intermediate" | "advanced" | "mastery";
  points: number;
  last_practiced_at: string | null;
}

interface SkillPortfolioProps {
  session: UserSession | null;
}

export function SkillPortfolio({ session }: SkillPortfolioProps) {
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSkills() {
      setLoading(true);
      try {
        const data = await apiFetch<SkillItem[]>("/learning/skills");
        setSkills(data);
      } catch (err) {
        console.error("Failed to load skills:", err);
      } finally {
        setLoading(false);
      }
    }
    loadSkills();
  }, [session?.token]);

  const totalPoints = skills.reduce((sum, s) => sum + s.points, 0);

  const getTierColor = (level: string) => {
    switch (level) {
      case "mastery":
        return "text-purple-400 border-purple-500/30 bg-purple-500/10";
      case "advanced":
        return "text-blue-400 border-blue-500/30 bg-blue-500/10";
      case "intermediate":
        return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
      default:
        return "text-amber-400 border-amber-500/30 bg-amber-500/10";
    }
  };

  const getProgressToNextLevel = (points: number) => {
    if (points >= 150) return 100;
    if (points >= 100) return Math.min(100, Math.round(((points - 100) / 50) * 100));
    if (points >= 50) return Math.min(100, Math.round(((points - 50) / 50) * 100));
    return Math.min(100, Math.round((points / 50) * 100));
  };

  return (
    <div className="bg-sovela-card border border-sovela-border rounded-2xl p-6 shadow-xl space-y-6">
      {/* Portfolio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-sovela-border pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart2 className="w-5 h-5 text-sovela-teal" />
            <h3 className="text-lg font-bold text-white">Verified Skill Competencies</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Empirical proficiency tracked through roadmap completion and assessment benchmarks.
          </p>
        </div>

        <div className="flex items-center space-x-3 bg-slate-900/60 border border-sovela-border px-4 py-2 rounded-xl">
          <Zap className="w-5 h-5 text-amber-400" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Total Skill XP</div>
            <div className="text-base font-black text-white font-mono">{totalPoints} PTS</div>
          </div>
        </div>
      </div>

      {loading && (
        <div className="py-10 text-center text-slate-400 flex items-center justify-center space-x-2">
          <RefreshCw className="w-5 h-5 animate-spin text-sovela-teal" />
          <span>Synchronizing competency matrix...</span>
        </div>
      )}

      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {skills.map((skill) => {
            const nextLvlPct = getProgressToNextLevel(skill.points);
            return (
              <div
                key={skill.id}
                className="p-4 rounded-xl bg-slate-900/40 border border-sovela-border hover:border-slate-700 transition-all space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                      {skill.category}
                    </span>
                    <h4 className="text-sm font-bold text-white mt-0.5">{skill.name}</h4>
                  </div>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${getTierColor(skill.level)}`}>
                    {skill.level}
                  </span>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Mastery Progress</span>
                    <span className="font-mono text-sovela-teal font-semibold">{skill.points} XP</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-sovela-teal to-blue-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${nextLvlPct}%` }}
                    />
                  </div>
                </div>

                {skill.description && (
                  <p className="text-[11px] text-slate-400 line-clamp-2">
                    {skill.description}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
