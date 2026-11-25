"use client";

import React, { useState, useEffect } from "react";
import { Navigation } from "../components/Navigation";
import { TodayView } from "../components/dashboard/TodayView";
import { GoalManager } from "../components/goals/GoalManager";
import { SocraticChat } from "../components/mentor/SocraticChat";
import { OpportunityHub } from "../components/opportunities/OpportunityHub";
import { LearningRoadmaps } from "../components/learning/LearningRoadmaps";
import { AuthModal } from "../components/auth/AuthModal";
import { OnboardingWizard } from "../components/onboarding/OnboardingWizard";
import { ProfileModal } from "../components/profile/ProfileModal";
import { getSession, setSession, UserSession } from "../lib/api";

export default function Home() {
  const [currentTab, setCurrentTab] = useState<string>("today");
  const [session, setLocalSession] = useState<UserSession | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    const s = getSession();
    if (s) setLocalSession(s);

    const handleCleared = () => setLocalSession(null);
    window.addEventListener("sovela_session_cleared", handleCleared);
    return () => window.removeEventListener("sovela_session_cleared", handleCleared);
  }, []);

  function handleLogout() {
    setSession(null);
    setLocalSession(null);
  }

  const needsOnboarding = Boolean(
    session && session.user && session.user.profile && !session.user.profile.onboarding_completed
  );

  return (
    <div className="min-h-screen bg-sovela-navy flex flex-col">
      <Navigation
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        session={session}
        onOpenAuth={() => setIsAuthOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
        onLogout={handleLogout}
      />

      <main className="flex-1">
        {currentTab === "today" && (
          <TodayView session={session} onOpenAuth={() => setIsAuthOpen(true)} />
        )}
        {currentTab === "learning" && (
          <div className="max-w-7xl mx-auto px-4 lg:px-8 py-8">
            <LearningRoadmaps session={session} />
          </div>
        )}
        {currentTab === "goals" && (
          <GoalManager session={session} onOpenAuth={() => setIsAuthOpen(true)} />
        )}
        {currentTab === "mentor" && (
          <SocraticChat session={session} onOpenAuth={() => setIsAuthOpen(true)} />
        )}
        {currentTab === "opportunities" && (
          <OpportunityHub />
        )}
      </main>

      {/* Onboarding Wizard for new accounts */}
      {needsOnboarding && session && (
        <OnboardingWizard
          session={session}
          onComplete={(updated) => {
            setLocalSession(updated);
          }}
        />
      )}

      {/* User Profile & Settings Modal */}
      {isProfileOpen && session && (
        <ProfileModal
          isOpen={isProfileOpen}
          onClose={() => setIsProfileOpen(false)}
          session={session}
          onUpdate={(updated) => {
            setLocalSession(updated);
          }}
        />
      )}

      {/* Authentication Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onSuccess={(s) => {
          setLocalSession(s);
          setIsAuthOpen(false);
        }}
      />
    </div>
  );
}
