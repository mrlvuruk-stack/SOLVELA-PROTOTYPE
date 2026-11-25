"use client";

import React, { useState } from "react";
import { X, User as UserIcon, Clock, Globe, Shield, Key, Save, CheckCircle2, AlertCircle } from "lucide-react";
import { apiFetch, setSession, UserSession } from "../../lib/api";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  session: UserSession;
  onUpdate: (updatedSession: UserSession) => void;
}

export function ProfileModal({ isOpen, onClose, session, onUpdate }: ProfileModalProps) {
  const profile = session.user.profile;
  const [fullName, setFullName] = useState(session.user.full_name);
  const [dailyMinutes, setDailyMinutes] = useState(profile?.daily_capacity_minutes || 300);
  const [weeklyHours, setWeeklyHours] = useState(profile?.weekly_capacity_hours || 25);
  const [timezone, setTimezone] = useState(profile?.timezone || "UTC");
  const [focusDomains, setFocusDomains] = useState(profile?.focus_domains || "Software Engineering, AI");
  
  // Password change state
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [pwMsg, setPwMsg] = useState<{ text: string; isError: boolean } | null>(null);
  
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ text: string; isError: boolean } | null>(null);

  if (!isOpen) return null;

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setStatusMsg(null);
    try {
      const resp: any = await apiFetch("/auth/profile", {
        method: "PUT",
        body: JSON.stringify({
          full_name: fullName,
          daily_capacity_minutes: dailyMinutes,
          weekly_capacity_hours: weeklyHours,
          timezone,
          focus_domains: focusDomains,
        }),
      });

      const updated: UserSession = {
        ...session,
        user: resp,
      };
      setSession(updated);
      onUpdate(updated);
      setStatusMsg({ text: "Profile settings saved successfully", isError: false });
    } catch (err: any) {
      setStatusMsg({ text: err.message || "Failed to update profile", isError: true });
    } finally {
      setSaving(false);
    }
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (!oldPassword || !newPassword) return;
    setPwMsg(null);
    try {
      await apiFetch("/auth/change-password", {
        method: "PUT",
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
        }),
      });
      setOldPassword("");
      setNewPassword("");
      setPwMsg({ text: "Password changed successfully", isError: false });
    } catch (err: any) {
      setPwMsg({ text: err.message || "Failed to change password", isError: true });
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-sovela-card border border-sovela-border rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-5 border-b border-sovela-border flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="h-8 w-8 rounded-lg bg-sovela-teal/15 flex items-center justify-center">
              <UserIcon className="h-4 w-4 text-sovela-teal" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">Personal Life OS Profile</h3>
              <p className="text-xs text-sovela-text-muted">{session.user.email} • {session.user.role}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6 text-xs">
          {statusMsg && (
            <div
              className={`p-3 rounded-xl flex items-center space-x-2 ${
                statusMsg.isError
                  ? "bg-rose-500/10 border border-rose-500/20 text-rose-400"
                  : "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
              }`}
            >
              {statusMsg.isError ? <AlertCircle className="h-4 w-4 shrink-0" /> : <CheckCircle2 className="h-4 w-4 shrink-0" />}
              <span>{statusMsg.text}</span>
            </div>
          )}

          {/* Profile Form */}
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
              />
            </div>

            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="block text-slate-300 font-medium mb-1 flex items-center">
                  <Clock className="h-3.5 w-3.5 mr-1 text-sovela-teal" /> Daily Capacity Cap (Minutes)
                </label>
                <input
                  type="number"
                  min="30"
                  max="960"
                  step="15"
                  value={dailyMinutes}
                  onChange={(e) => setDailyMinutes(parseInt(e.target.value))}
                  className="w-full px-3.5 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                />
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  Current: {(dailyMinutes / 60).toFixed(1)} hours/day
                </span>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1 flex items-center">
                  <Globe className="h-3.5 w-3.5 mr-1 text-sovela-teal" /> Timezone
                </label>
                <input
                  type="text"
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  placeholder="UTC or Asia/Kolkata"
                  className="w-full px-3.5 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Focus Domains</label>
              <input
                type="text"
                value={focusDomains}
                onChange={(e) => setFocusDomains(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">Comma-separated skills & domains</span>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 rounded-xl bg-sovela-teal hover:bg-sky-400 text-white font-medium text-xs transition flex items-center shadow-md shadow-sovela-teal/15 disabled:opacity-50"
            >
              <Save className="h-3.5 w-3.5 mr-1.5" />
              {saving ? "Saving Changes..." : "Save Profile Settings"}
            </button>
          </form>

          {/* Password Change Box */}
          <div className="pt-5 border-t border-sovela-border space-y-3.5">
            <h4 className="text-slate-200 font-bold flex items-center">
              <Key className="h-3.5 w-3.5 mr-1.5 text-sovela-teal" /> Security & Password
            </h4>

            {pwMsg && (
              <div
                className={`p-3 rounded-xl flex items-center space-x-2 ${
                  pwMsg.isError
                    ? "bg-rose-500/10 border border-rose-500/20 text-rose-400"
                    : "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                }`}
              >
                {pwMsg.isError ? <AlertCircle className="h-4 w-4 shrink-0" /> : <CheckCircle2 className="h-4 w-4 shrink-0" />}
                <span>{pwMsg.text}</span>
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="password"
                  placeholder="Current Password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                />
                <input
                  type="password"
                  placeholder="New Password (min 8 chars)"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-sovela-navy border border-sovela-border text-white text-xs focus:outline-none focus:border-sovela-teal"
                />
              </div>
              <button
                type="submit"
                className="px-3.5 py-1.5 rounded-lg border border-slate-700 hover:border-slate-500 text-slate-300 font-medium text-xs transition"
              >
                Update Password
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
