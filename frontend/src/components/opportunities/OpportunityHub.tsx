"use client";

import React, { useState, useEffect } from "react";
import { Briefcase, ExternalLink, Calendar, MapPin, Search, Filter } from "lucide-react";
import { apiFetch } from "../../lib/api";

export function OpportunityHub() {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);

  const categories = [
    { id: "all", label: "All Opportunities" },
    { id: "internship", label: "Internships" },
    { id: "job", label: "Jobs" },
    { id: "hackathon", label: "Hackathons" },
    { id: "contest", label: "Contests" },
    { id: "scholarship", label: "Scholarships" },
    { id: "grant_fellowship", label: "Grants & Fellowships" },
    { id: "research_post", label: "Research Posts" },
    { id: "event", label: "Events" },
  ];

  async function loadOpportunities(cat?: string) {
    setLoading(true);
    try {
      const query = cat && cat !== "all" ? `?category=${cat}` : "";
      const data = await apiFetch<any[]>(`/opportunities${query}`);
      setOpportunities(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOpportunities(selectedCategory);
  }, [selectedCategory]);

  const filtered = opportunities.filter((opp) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      opp.title.toLowerCase().includes(term) ||
      opp.organization.toLowerCase().includes(term) ||
      opp.description?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 lg:px-8 space-y-6">
      {/* Title & Governance Lock Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-white tracking-tight">Opportunity Hub</h2>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-sovela-green/20 text-sovela-green border border-sovela-green/30">
              DEC-06A LOCKED (8 Categories)
            </span>
          </div>
          <p className="text-xs text-sovela-text-muted mt-1">
            Curated opportunities for students and professionals across 8 canonical tracks.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-sovela-text-muted" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search title or company..."
            className="w-full bg-sovela-card border border-sovela-border rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sovela-teal"
          />
        </div>
      </div>

      {/* Category Pills (8 Tracks) */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1">
        {categories.map((c) => {
          const isActive = selectedCategory === c.id;
          return (
            <button
              key={c.id}
              onClick={() => setSelectedCategory(c.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition ${
                isActive
                  ? "bg-sovela-teal text-white shadow-md shadow-sovela-teal/20"
                  : "bg-sovela-card border border-sovela-border text-slate-300 hover:text-white hover:bg-slate-800"
              }`}
            >
              {c.label}
            </button>
          );
        })}
      </div>

      {/* Opportunity Cards */}
      {loading ? (
        <div className="text-center py-12 text-xs text-sovela-text-muted">Loading opportunities...</div>
      ) : filtered.length === 0 ? (
        <div className="bg-sovela-card border border-dashed border-sovela-border rounded-2xl p-12 text-center">
          <Briefcase className="h-8 w-8 text-slate-500 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-white">No opportunities found</h3>
          <p className="text-xs text-sovela-text-muted mt-1">Try selecting a different category or clearing search filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((opp) => (
            <div
              key={opp.id}
              className="bg-sovela-card border border-sovela-border rounded-2xl p-5 shadow-xl flex flex-col justify-between hover:border-sovela-teal/50 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between text-[11px] mb-2">
                  <span className="font-mono text-sovela-teal uppercase tracking-wider font-bold px-2 py-0.5 rounded-full bg-sovela-teal/10">
                    {opp.category.replace("_", " ")}
                  </span>
                  <span className="text-slate-400 flex items-center space-x-1">
                    <MapPin className="h-3 w-3" />
                    <span>{opp.location}</span>
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white line-clamp-1">{opp.title}</h3>
                <div className="text-xs font-semibold text-slate-300 mt-0.5">{opp.organization}</div>

                {opp.description && (
                  <p className="text-xs text-sovela-text-muted mt-2 line-clamp-2 leading-relaxed">{opp.description}</p>
                )}

                {opp.eligibility && (
                  <div className="mt-3 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-300">
                    <span className="font-semibold text-sovela-teal">Eligibility: </span>
                    <span>{opp.eligibility}</span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-sovela-border flex items-center justify-between">
                <span className="text-[11px] text-slate-400 flex items-center space-x-1">
                  <Calendar className="h-3.5 w-3.5 text-sovela-amber" />
                  <span>{opp.deadline ? new Date(opp.deadline).toLocaleDateString() : "Rolling"}</span>
                </span>
                <a
                  href={opp.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1 text-xs text-sovela-teal hover:text-sky-300 font-semibold"
                >
                  <span>Apply Now</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
