"use client";

import React from "react";
import { User, Compass, Target, MessageSquare, Briefcase, BookOpen, Sparkles, LogOut, LogIn } from "lucide-react";
import { UserSession } from "../lib/api";

interface NavigationProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  session: UserSession | null;
  onOpenAuth: () => void;
  onOpenProfile?: () => void;
  onLogout: () => void;
}

export function Navigation({
  currentTab,
  setCurrentTab,
  session,
  onOpenAuth,
  onOpenProfile,
  onLogout,
}: NavigationProps) {
  const tabs = [
    { id: "today", label: "Today & Plan", icon: Compass },
    { id: "learning", label: "Roadmaps & Skills", icon: BookOpen },
    { id: "goals", label: "Goals & Milestones", icon: Target },
    { id: "mentor", label: "Socratic Mentor", icon: MessageSquare },
    { id: "opportunities", label: "Opportunity Hub (DEC-06A)", icon: Briefcase },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-sovela-border bg-sovela-navy/95 backdrop-blur px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentTab("today")}>
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-sovela-teal to-blue-500 flex items-center justify-center shadow-lg shadow-sovela-teal/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-sovela-teal bg-clip-text text-transparent">
              SOVELA AI
            </span>
            <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-sovela-card border border-sovela-border text-sovela-teal">
              Life OS v1.0
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1 bg-sovela-card/60 p-1 rounded-xl border border-sovela-border">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-sovela-teal text-white shadow-sm"
                    : "text-sovela-text-muted hover:text-white hover:bg-slate-800"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User Status / Auth Button */}
        <div className="flex items-center space-x-3">
          {session ? (
            <div className="flex items-center space-x-3">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-semibold text-white">{session.user.full_name}</div>
                <div className="text-[10px] text-sovela-teal uppercase tracking-wider font-mono">
                  {session.user.role.replace("_", " ")}
                </div>
              </div>
              <button
                onClick={onOpenProfile}
                title="Profile & Settings"
                className="p-2 rounded-lg bg-sovela-card border border-sovela-border text-slate-300 hover:text-white hover:border-sovela-teal transition-colors"
              >
                <User className="h-4 w-4" />
              </button>
              <button
                onClick={onLogout}
                title="Logout"
                className="p-2 rounded-lg bg-sovela-card border border-sovela-border text-sovela-text-muted hover:text-sovela-rose hover:border-sovela-rose/50 transition-colors"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-sovela-teal hover:bg-sky-400 text-white font-medium text-sm transition-all shadow-md shadow-sovela-teal/20"
            >
              <LogIn className="h-4 w-4" />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
