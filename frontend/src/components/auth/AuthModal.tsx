"use client";

import React, { useState } from "react";
import { X, Lock, Mail, User as UserIcon, GraduationCap, Briefcase, ArrowRight } from "lucide-react";
import { apiFetch, setSession, UserSession } from "../../lib/api";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (session: UserSession) => void;
}

export function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("student");
  const [capacityHours, setCapacityHours] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        const resp = await apiFetch<UserSession>("/auth/register", {
          method: "POST",
          body: JSON.stringify({
            email,
            password,
            full_name: fullName,
            role,
            daily_capacity_minutes: capacityHours * 60,
            focus_domains: role === "student" ? "Computer Science,Algorithms" : "Engineering Management,System Design",
          }),
        });
        setSession(resp);
        onSuccess(resp);
        onClose();
      } else {
        const resp = await apiFetch<UserSession>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        setSession(resp);
        onSuccess(resp);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-sovela-card border border-sovela-border rounded-2xl p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-sovela-text-muted hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="text-center mb-6">
          <h2 className="text-xl font-bold text-white tracking-tight">
            {isRegister ? "Create Sovela Account" : "Welcome Back"}
          </h2>
          <p className="text-xs text-sovela-text-muted mt-1">
            {isRegister
              ? "Set up your personal AI operating system"
              : "Sign in to access your dashboard and schedule"}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-sovela-rose/10 border border-sovela-rose/30 text-sovela-rose text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-sovela-text-muted mb-1">Full Name</label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-sovela-text-muted" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Rivera"
                  className="w-full bg-slate-900/80 border border-sovela-border rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sovela-teal"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-sovela-text-muted mb-1">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-sovela-text-muted" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@domain.com"
                className="w-full bg-slate-900/80 border border-sovela-border rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sovela-teal"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-sovela-text-muted mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-sovela-text-muted" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-900/80 border border-sovela-border rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sovela-teal"
              />
            </div>
          </div>

          {isRegister && (
            <>
              <div>
                <label className="block text-xs font-medium text-sovela-text-muted mb-1.5">Primary Persona</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRole("student")}
                    className={`flex items-center justify-center space-x-2 p-2.5 rounded-lg border text-xs font-medium transition ${
                      role === "student"
                        ? "bg-sovela-teal/15 border-sovela-teal text-white"
                        : "bg-slate-900/60 border-sovela-border text-sovela-text-muted hover:text-white"
                    }`}
                  >
                    <GraduationCap className="h-4 w-4 text-sovela-teal" />
                    <span>Student</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole("working_professional")}
                    className={`flex items-center justify-center space-x-2 p-2.5 rounded-lg border text-xs font-medium transition ${
                      role === "working_professional"
                        ? "bg-sovela-teal/15 border-sovela-teal text-white"
                        : "bg-slate-900/60 border-sovela-border text-sovela-text-muted hover:text-white"
                    }`}
                  >
                    <Briefcase className="h-4 w-4 text-blue-400" />
                    <span>Professional</span>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-sovela-text-muted mb-1">
                  Daily Cognitive Capacity ({capacityHours} hours / {capacityHours * 60} mins)
                </label>
                <input
                  type="range"
                  min="2"
                  max="8"
                  step="0.5"
                  value={capacityHours}
                  onChange={(e) => setCapacityHours(parseFloat(e.target.value))}
                  className="w-full accent-sovela-teal"
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 flex items-center justify-center space-x-2 py-2.5 rounded-lg bg-sovela-teal hover:bg-sky-400 text-white font-medium text-sm transition shadow-lg shadow-sovela-teal/20 disabled:opacity-50"
          >
            <span>{loading ? "Processing..." : isRegister ? "Complete Setup" : "Sign In"}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>

        <div className="mt-5 text-center">
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
            }}
            className="text-xs text-sovela-teal hover:underline font-medium"
          >
            {isRegister ? "Already have an account? Sign in" : "New to Sovela? Create an account"}
          </button>
        </div>
      </div>
    </div>
  );
}
