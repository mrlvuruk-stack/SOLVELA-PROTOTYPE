"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen, Compass, CheckCircle2, Circle, Clock, Award, ChevronRight,
  ExternalLink, ArrowLeft, Play, Filter, Sparkles, RefreshCw, AlertCircle
} from "lucide-react";
import { apiFetch, UserSession } from "../../lib/api";
import { AssessmentModal } from "./AssessmentModal";
import { SkillPortfolio } from "./SkillPortfolio";

interface ResourceItem {
  title: string;
  url: string;
  type: string;
  est_minutes: number;
}

interface RoadmapNodeItem {
  id: string;
  roadmap_id: string;
  order_index: number;
  title: string;
  description: string;
  estimated_minutes: number;
  key_takeaways: string[];
  resources: ResourceItem[];
  is_completed: boolean;
  has_assessment: boolean;
}

interface RoadmapSummary {
  id: string;
  slug: string;
  title: string;
  domain: string;
  description: string;
  difficulty_level: string;
  estimated_hours: number;
  nodes_count: number;
  is_enrolled: boolean;
  progress_pct: number;
}

interface RoadmapDetail extends RoadmapSummary {
  nodes: RoadmapNodeItem[];
  enrollment_id: string | null;
  completed_nodes_count: number;
}

interface LearningRoadmapsProps {
  session: UserSession | null;
}

export function LearningRoadmaps({ session }: LearningRoadmapsProps) {
  const [roadmaps, setRoadmaps] = useState<RoadmapSummary[]>([]);
  const [selectedRoadmap, setSelectedRoadmap] = useState<RoadmapDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [domainFilter, setDomainFilter] = useState<string>("All");
  const [activeAssessmentNode, setActiveAssessmentNode] = useState<{ id: string; title: string } | null>(null);

  // Load catalog
  const loadRoadmaps = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<RoadmapSummary[]>("/learning/roadmaps");
      setRoadmaps(data);
    } catch (err: any) {
      setError(err.message || "Failed to load learning roadmaps.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoadmaps();
  }, [session?.token]);

  // Load specific roadmap detail
  const handleSelectRoadmap = async (slugOrId: string) => {
    setDetailLoading(true);
    try {
      const detail = await apiFetch<RoadmapDetail>(`/learning/roadmaps/${slugOrId}`);
      setSelectedRoadmap(detail);
    } catch (err: any) {
      setError(err.message || "Failed to load roadmap details.");
    } finally {
      setDetailLoading(false);
    }
  };

  // Enroll in roadmap
  const handleEnroll = async (roadmapId: string) => {
    try {
      const detail = await apiFetch<RoadmapDetail>(
        `/learning/roadmaps/${roadmapId}/enroll`,
        { method: "POST" }
      );
      setSelectedRoadmap(detail);
      loadRoadmaps();
    } catch (err: any) {
      alert("Failed to enroll: " + err.message);
    }
  };

  // Complete a curriculum node
  const handleCompleteNode = async (nodeId: string) => {
    try {
      await apiFetch(
        `/learning/nodes/${nodeId}/complete`,
        { method: "POST", body: JSON.stringify({ notes: "Self-verified study completion." }) }
      );
      if (selectedRoadmap) {
        handleSelectRoadmap(selectedRoadmap.id);
      }
      loadRoadmaps();
    } catch (err: any) {
      alert("Failed to mark node complete: " + err.message);
    }
  };

  const domains = ["All", ...Array.from(new Set(roadmaps.map(r => r.domain)))];
  const filteredRoadmaps = domainFilter === "All"
    ? roadmaps
    : roadmaps.filter(r => r.domain === domainFilter);

  return (
    <div className="space-y-8 animate-in fade-in">
      {/* Top Banner & Portfolio */}
      <SkillPortfolio session={session} />

      {/* Main Content Area */}
      {!selectedRoadmap ? (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                <BookOpen className="w-5 h-5 text-sovela-teal" />
                <span>Curated Learning Roadmaps</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Node-based skill curricula aligned with high-impact industry engineering roles.
              </p>
            </div>

            {/* Domain Filters */}
            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0">
              {domains.map((dom) => (
                <button
                  key={dom}
                  onClick={() => setDomainFilter(dom)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
                    domainFilter === dom
                      ? "bg-sovela-teal text-white shadow-sm"
                      : "bg-sovela-card border border-sovela-border text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  {dom}
                </button>
              ))}
            </div>
          </div>

          {loading && (
            <div className="py-16 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
              <RefreshCw className="w-8 h-8 animate-spin text-sovela-teal" />
              <p>Fetching accredited roadmap curricula...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-sm flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {!loading && !error && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredRoadmaps.map((r) => (
                <div
                  key={r.id}
                  onClick={() => handleSelectRoadmap(r.slug)}
                  className="bg-sovela-card border border-sovela-border rounded-2xl p-6 hover:border-sovela-teal/60 transition-all cursor-pointer shadow-lg hover:shadow-sovela-teal/5 flex flex-col justify-between group"
                >
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-sovela-teal/10 border border-sovela-teal/30 text-sovela-teal">
                        {r.domain}
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                        {r.difficulty_level}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-lg font-bold text-white group-hover:text-sovela-teal transition-colors">
                        {r.title}
                      </h3>
                      <p className="text-xs text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                        {r.description}
                      </p>
                    </div>

                    <div className="flex items-center space-x-4 text-xs text-slate-400 pt-2 border-t border-sovela-border/50">
                      <div className="flex items-center space-x-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span>~{r.estimated_hours} Hours</span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-slate-500" />
                        <span>{r.nodes_count} Modules</span>
                      </div>
                    </div>
                  </div>

                  {/* Enrollment / Progress Bar */}
                  <div className="pt-5 mt-4 border-t border-sovela-border">
                    {r.is_enrolled ? (
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-emerald-400 font-semibold flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Enrolled</span>
                          </span>
                          <span className="font-mono text-white font-bold">{r.progress_pct}%</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-sovela-teal to-blue-500 h-full rounded-full transition-all"
                            style={{ width: `${r.progress_pct}%` }}
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between text-xs text-slate-400 group-hover:text-sovela-teal font-medium">
                        <span>Start Learning Path</span>
                        <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Detailed Roadmap Curriculum View */
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setSelectedRoadmap(null)}
              className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-white px-3 py-1.5 rounded-xl bg-sovela-card border border-sovela-border hover:bg-slate-800 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Roadmaps</span>
            </button>

            {!selectedRoadmap.is_enrolled ? (
              <button
                onClick={() => handleEnroll(selectedRoadmap.id)}
                className="px-4 py-2 rounded-xl bg-sovela-teal text-white text-xs font-semibold hover:bg-teal-500 transition-all shadow-md shadow-sovela-teal/20"
              >
                Enroll in Roadmap
              </button>
            ) : (
              <div className="flex items-center space-x-3 text-xs">
                <span className="text-slate-400">Roadmap Progress:</span>
                <span className="font-mono text-sovela-teal font-bold text-sm">
                  {selectedRoadmap.progress_pct}% ({selectedRoadmap.completed_nodes_count}/{selectedRoadmap.nodes.length})
                </span>
              </div>
            )}
          </div>

          {/* Hero Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-sovela-card to-slate-900 border border-sovela-border shadow-xl space-y-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-sovela-teal uppercase tracking-wider">{selectedRoadmap.domain}</span>
              <span className="text-slate-600">•</span>
              <span className="text-xs text-slate-400 capitalize">{selectedRoadmap.difficulty_level} Level</span>
            </div>
            <h1 className="text-2xl font-black text-white">{selectedRoadmap.title}</h1>
            <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">{selectedRoadmap.description}</p>
          </div>

          {/* Node Stepper Sequence */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Curriculum Modules</h3>

            {selectedRoadmap.nodes.map((node, index) => (
              <div
                key={node.id}
                className={`p-6 rounded-2xl border transition-all ${
                  node.is_completed
                    ? "bg-emerald-950/10 border-emerald-500/30"
                    : "bg-sovela-card border-sovela-border"
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                  <div className="flex items-start space-x-4">
                    <div className="mt-1">
                      {node.is_completed ? (
                        <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
                      ) : (
                        <div className="w-6 h-6 rounded-full border-2 border-slate-600 flex items-center justify-center text-xs font-mono font-bold text-slate-400">
                          {index + 1}
                        </div>
                      )}
                    </div>

                    <div className="space-y-3">
                      <div>
                        <h4 className="text-base font-bold text-white">{node.title}</h4>
                        <p className="text-xs text-slate-400 mt-1 leading-relaxed">{node.description}</p>
                      </div>

                      {/* Key Takeaways */}
                      {node.key_takeaways && node.key_takeaways.length > 0 && (
                        <div className="space-y-1.5 pt-2">
                          <div className="text-[11px] font-semibold text-sovela-teal uppercase tracking-wider">
                            Core Competencies
                          </div>
                          <ul className="space-y-1">
                            {node.key_takeaways.map((takeaway, tIdx) => (
                              <li key={tIdx} className="text-xs text-slate-300 flex items-start space-x-2">
                                <span className="text-sovela-teal mt-0.5">•</span>
                                <span>{takeaway}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Curated Resources */}
                      {node.resources && node.resources.length > 0 && (
                        <div className="space-y-2 pt-2">
                          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                            Curated Learning Assets
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {node.resources.map((res, rIdx) => (
                              <a
                                key={rIdx}
                                href={res.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-sovela-border hover:border-sovela-teal text-xs text-slate-200 transition-all hover:bg-slate-800"
                              >
                                <span>{res.title}</span>
                                <ExternalLink className="w-3 h-3 text-slate-400" />
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Node Actions */}
                  <div className="flex lg:flex-col items-center lg:items-end space-x-2 lg:space-x-0 lg:space-y-2 flex-shrink-0 pt-2 lg:pt-0">
                    {!node.is_completed && (
                      <button
                        onClick={() => handleCompleteNode(node.id)}
                        className="px-3.5 py-1.5 rounded-xl bg-slate-800 border border-sovela-border hover:border-emerald-500 text-xs font-medium text-slate-300 hover:text-emerald-300 transition-all flex items-center space-x-1.5"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Mark Done (+25 XP)</span>
                      </button>
                    )}

                    {node.has_assessment && (
                      <button
                        onClick={() => setActiveAssessmentNode({ id: node.id, title: node.title })}
                        className="px-3.5 py-1.5 rounded-xl bg-sovela-teal/15 border border-sovela-teal/30 hover:border-sovela-teal text-xs font-semibold text-sovela-teal transition-all flex items-center space-x-1.5 shadow-sm"
                      >
                        <Award className="w-3.5 h-3.5" />
                        <span>Take Quiz (+50 XP)</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assessment Quiz Modal */}
      {activeAssessmentNode && (
        <AssessmentModal
          nodeId={activeAssessmentNode.id}
          nodeTitle={activeAssessmentNode.title}
          session={session}
          onClose={() => setActiveAssessmentNode(null)}
          onAssessmentPassed={() => {
            if (selectedRoadmap) {
              handleSelectRoadmap(selectedRoadmap.id);
            }
            loadRoadmaps();
          }}
        />
      )}
    </div>
  );
}
