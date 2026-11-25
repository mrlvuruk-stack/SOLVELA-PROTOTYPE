"use client";

import React, { useState } from "react";
import { 
  GraduationCap, Briefcase, Sparkles, CheckCircle2, ArrowRight, ArrowLeft, 
  Target, Clock, Compass, ShieldCheck 
} from "lucide-react";
import { apiFetch, setSession, UserSession } from "../../lib/api";

interface OnboardingWizardProps {
  session: UserSession;
  onComplete: (updatedSession: UserSession) => void;
}

const DOMAINS_LIST = [
  "Software Engineering",
  "AI & Machine Learning",
  "Distributed Systems",
  "System Design",
  "Data Science",
  "Cloud Architecture",
  "Algorithms & Data Structures",
  "Full-Stack Web Development",
  "Competitive Programming",
  "Cybersecurity"
];

export function OnboardingWizard({ session, onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState(1);
  const [role, setRole] = useState<string>(session.user.role || "student");
  const [selectedDomains, setSelectedDomains] = useState<string[]>([
    "Software Engineering", "AI & Machine Learning"
  ]);
  const [dailyHours, setDailyHours] = useState<number>(5.0);
  const [primaryGoal, setPrimaryGoal] = useState<string>("");
  const [learningStyle, setLearningStyle] = useState<string>("socratic");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  function toggleDomain(domain: string) {
    if (selectedDomains.includes(domain)) {
      if (selectedDomains.length > 1) {
        setSelectedDomains(selectedDomains.filter((d) => d !== domain));
      }
    } else {
      setSelectedDomains([...selectedDomains, domain]);
    }
  }

  async function handleFinish() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const resp: any = await apiFetch("/auth/onboarding", {
        method: "POST",
        body: JSON.stringify({
          role,
          daily_capacity_hours: dailyHours,
          focus_domains: selectedDomains,
          primary_goal_title: primaryGoal.trim() || undefined,
          learning_style: learningStyle
        }),
      });

      const updatedSession: UserSession = {
        ...session,
        user: resp,
      };
      setSession(updatedSession);
      onComplete(updatedSession);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to complete onboarding.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-sovela-navy/95 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-sovela-card border border-sovela-border rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Progress Header */}
        <div className="p-6 border-b border-sovela-border flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-sovela-teal/15 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-sovela-teal" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                Welcome to Sovela AI
              </h2>
              <p className="text-xs text-sovela-text-muted">
                Step {step} of 4: Personalizing your Life Operating System
              </p>
            </div>
          </div>
          <div className="flex space-x-1.5">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`h-2 rounded-full transition-all duration-300 ${
                  s === step
                    ? "w-7 bg-sovela-teal"
                    : s < step
                    ? "w-3 bg-sovela-teal/60"
                    : "w-3 bg-slate-700"
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
              <span>{errorMsg}</span>
              {(errorMsg.toLowerCase().includes("credentials") || errorMsg.toLowerCase().includes("expired")) && (
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="ml-3 px-3 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-white font-medium rounded-lg text-xs transition"
                >
                  Refresh & Sign In
                </button>
              )}
            </div>
          )}

          {/* STEP 1: Persona */}
          {step === 1 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div>
                <h3 className="text-base font-semibold text-white">Select Your Primary Operating Persona</h3>
                <p className="text-xs text-sovela-text-muted mt-1">
                  Sovela tailors its cognitive load curves, opportunities, and temporal scheduling algorithms to your daily rhythm.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setRole("student")}
                  className={`p-5 rounded-2xl border text-left transition relative flex flex-col justify-between h-44 ${
                    role === "student"
                      ? "border-sovela-teal bg-sovela-teal/10 shadow-lg shadow-sovela-teal/5"
                      : "border-sovela-border bg-sovela-navy/60 hover:border-slate-600"
                  }`}
                >
                  <div>
                    <GraduationCap className={`h-8 w-8 mb-3 ${role === "student" ? "text-sovela-teal" : "text-slate-400"}`} />
                    <h4 className="text-sm font-bold text-white">Student / Academic</h4>
                    <p className="text-xs text-sovela-text-muted mt-1.5 leading-relaxed">
                      Optimized for course mastery, hackathons, internships, exam deadlines, and research projects.
                    </p>
                  </div>
                  {role === "student" && (
                    <div className="flex items-center text-xs font-semibold text-sovela-teal mt-2">
                      <CheckCircle2 className="h-4 w-4 mr-1.5" /> Selected
                    </div>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setRole("working_professional")}
                  className={`p-5 rounded-2xl border text-left transition relative flex flex-col justify-between h-44 ${
                    role === "working_professional"
                      ? "border-sovela-teal bg-sovela-teal/10 shadow-lg shadow-sovela-teal/5"
                      : "border-sovela-border bg-sovela-navy/60 hover:border-slate-600"
                  }`}
                >
                  <div>
                    <Briefcase className={`h-8 w-8 mb-3 ${role === "working_professional" ? "text-sovela-teal" : "text-slate-400"}`} />
                    <h4 className="text-sm font-bold text-white">Working Professional</h4>
                    <p className="text-xs text-sovela-text-muted mt-1.5 leading-relaxed">
                      Optimized for skill acceleration, promotion benchmarks, deep work blocks, and side initiatives.
                    </p>
                  </div>
                  {role === "working_professional" && (
                    <div className="flex items-center text-xs font-semibold text-sovela-teal mt-2">
                      <CheckCircle2 className="h-4 w-4 mr-1.5" /> Selected
                    </div>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: Focus Domains */}
          {step === 2 && (
            <div className="space-y-5 animate-in fade-in duration-300">
              <div>
                <h3 className="text-base font-semibold text-white">Choose Your Focus Domains</h3>
                <p className="text-xs text-sovela-text-muted mt-1">
                  Select the core fields you are mastering. Sovela AI will match relevant opportunities and Socratic prompts.
                </p>
              </div>

              <div className="flex flex-wrap gap-2.5">
                {DOMAINS_LIST.map((domain) => {
                  const isSelected = selectedDomains.includes(domain);
                  return (
                    <button
                      key={domain}
                      type="button"
                      onClick={() => toggleDomain(domain)}
                      className={`px-3.5 py-2 rounded-xl text-xs font-medium transition ${
                        isSelected
                          ? "bg-sovela-teal text-white shadow-md shadow-sovela-teal/15 font-semibold"
                          : "bg-sovela-navy border border-sovela-border text-slate-300 hover:border-slate-600"
                      }`}
                    >
                      {domain}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 3: Capacity & Burnout Safety */}
          {step === 3 && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div>
                <h3 className="text-base font-semibold text-white">Daily Focus Capacity Cap</h3>
                <p className="text-xs text-sovela-text-muted mt-1">
                  Sovela's Knapsack Scheduler strictly enforces your daily limit to eliminate cognitive burnout and guarantee sustainable progress.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-sovela-navy/70 border border-sovela-border space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-300 flex items-center">
                    <Clock className="h-4 w-4 mr-1.5 text-sovela-teal" /> Target Daily Focus
                  </span>
                  <span className="text-lg font-bold text-sovela-teal">
                    {dailyHours.toFixed(1)} Hours <span className="text-xs text-slate-400 font-normal">({Math.round(dailyHours * 60)} min)</span>
                  </span>
                </div>

                <input
                  type="range"
                  min="1"
                  max="10"
                  step="0.5"
                  value={dailyHours}
                  onChange={(e) => setDailyHours(parseFloat(e.target.value))}
                  className="w-full accent-sovela-teal h-2 bg-slate-700 rounded-lg cursor-pointer"
                />

                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>1.0h (Light)</span>
                  <span>5.0h (Standard Cap)</span>
                  <span>10.0h (Maximum)</span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-sky-950/30 border border-sky-800/30 flex items-start space-x-3 text-xs text-sky-200">
                <ShieldCheck className="h-5 w-5 text-sky-400 shrink-0 mt-0.5" />
                <p>
                  <strong>Cognitive Safety Guarantee:</strong> The Knapsack algorithm will never silently overflow tasks onto an overloaded day. Overdue items are gracefully balanced via 3-day recovery windows.
                </p>
              </div>
            </div>
          )}

          {/* STEP 4: Primary Goal & Pedagogical Style */}
          {step === 4 && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div>
                <h3 className="text-base font-semibold text-white">Define Your High-Impact Objective</h3>
                <p className="text-xs text-sovela-text-muted mt-1">
                  What is the #1 breakthrough you want to achieve over the next 60 days?
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Primary SMART Goal Title
                </label>
                <div className="relative">
                  <Target className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={primaryGoal}
                    onChange={(e) => setPrimaryGoal(e.target.value)}
                    placeholder="e.g. Master Distributed Consensus & Build Raft Engine"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-2">
                  AI Mentorship Interaction Style
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setLearningStyle("socratic")}
                    className={`p-3.5 rounded-xl border text-left text-xs transition ${
                      learningStyle === "socratic"
                        ? "border-sovela-teal bg-sovela-teal/10 text-white font-medium"
                        : "border-sovela-border bg-sovela-navy text-slate-400"
                    }`}
                  >
                    <div className="font-bold text-white mb-1">Socratic Diagnostic</div>
                    Probing questions, cognitive scaffolding, zero spoon-fed solutions.
                  </button>

                  <button
                    type="button"
                    onClick={() => setLearningStyle("direct")}
                    className={`p-3.5 rounded-xl border text-left text-xs transition ${
                      learningStyle === "direct"
                        ? "border-sovela-teal bg-sovela-teal/10 text-white font-medium"
                        : "border-sovela-border bg-sovela-navy text-slate-400"
                    }`}
                  >
                    <div className="font-bold text-white mb-1">Direct Guided</div>
                    Structured explanations, bullet point breakdowns, immediate code blueprints.
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="p-5 border-t border-sovela-border flex items-center justify-between bg-sovela-navy/50">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s - 1)}
              className="px-4 py-2 rounded-xl border border-sovela-border text-slate-300 text-xs font-medium hover:bg-slate-800 transition flex items-center"
            >
              <ArrowLeft className="h-3.5 w-3.5 mr-1.5" /> Back
            </button>
          ) : (
            <div />
          )}

          {step < 4 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              className="px-5 py-2.5 rounded-xl bg-sovela-teal hover:bg-sky-400 text-white text-xs font-semibold transition flex items-center shadow-md shadow-sovela-teal/20"
            >
              Continue <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleFinish}
              disabled={loading}
              className="px-6 py-2.5 rounded-xl bg-sovela-teal hover:bg-sky-400 text-white text-xs font-semibold transition flex items-center shadow-lg shadow-sovela-teal/25 disabled:opacity-50"
            >
              {loading ? "Activating OS..." : "Launch Life Operating System"}
              <Sparkles className="h-3.5 w-3.5 ml-2" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
