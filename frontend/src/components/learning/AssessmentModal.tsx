"use client";

import React, { useState, useEffect } from "react";
import { CheckCircle2, XCircle, AlertCircle, Award, ArrowRight, RefreshCw, X } from "lucide-react";
import { apiFetch, UserSession } from "../../lib/api";

interface QuestionItem {
  id: number;
  question: string;
  options: string[];
}

interface AssessmentData {
  id: string;
  node_id: string;
  title: string;
  passing_score_pct: number;
  questions: QuestionItem[];
}

interface AssessmentResult {
  score_pct: number;
  passed: boolean;
  passing_score_pct: number;
  correct_count: number;
  total_questions: number;
  feedback: string;
  points_awarded: number;
}

interface AssessmentModalProps {
  nodeId: string;
  nodeTitle: string;
  session: UserSession | null;
  onClose: () => void;
  onAssessmentPassed: () => void;
}

export function AssessmentModal({
  nodeId,
  nodeTitle,
  session,
  onClose,
  onAssessmentPassed
}: AssessmentModalProps) {
  const [assessment, setAssessment] = useState<AssessmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<AssessmentResult | null>(null);

  useEffect(() => {
    async function fetchAssessment() {
      setLoading(true);
      setError(null);
      try {
        const data = await apiFetch<AssessmentData>(
          `/learning/assessments/node/${nodeId}`
        );
        setAssessment(data);
      } catch (err: any) {
        setError(err.message || "Failed to load assessment questions.");
      } finally {
        setLoading(false);
      }
    }
    fetchAssessment();
  }, [nodeId, session?.token]);

  const handleSelectOption = (questionId: number, optionIdx: number) => {
    setAnswers(prev => ({
      ...prev,
      [String(questionId)]: optionIdx
    }));
  };

  const handleSubmit = async () => {
    if (!assessment) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await apiFetch<AssessmentResult>(
        `/learning/assessments/${assessment.id}/submit`,
        {
          method: "POST",
          body: JSON.stringify({ answers })
        }
      );
      setResult(res);
      if (res.passed) {
        onAssessmentPassed();
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit assessment.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
      <div className="bg-sovela-card border border-sovela-border rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-sovela-border flex items-center justify-between bg-slate-900/50">
          <div>
            <div className="text-xs font-semibold text-sovela-teal uppercase tracking-wider">Skill Verification Quiz</div>
            <h3 className="text-lg font-bold text-white">{nodeTitle}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {loading && (
            <div className="py-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
              <RefreshCw className="w-8 h-8 animate-spin text-sovela-teal" />
              <p>Loading assessment questions...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-sm flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {result && (
            <div className={`p-6 rounded-2xl border text-center space-y-4 ${
              result.passed
                ? "bg-emerald-950/30 border-emerald-500/40 text-emerald-200"
                : "bg-amber-950/30 border-amber-500/40 text-amber-200"
            }`}>
              <div className="w-16 h-16 rounded-full mx-auto flex items-center justify-center bg-slate-900/80 border border-sovela-border shadow-inner">
                {result.passed ? (
                  <Award className="w-8 h-8 text-emerald-400" />
                ) : (
                  <XCircle className="w-8 h-8 text-amber-400" />
                )}
              </div>
              <div>
                <h4 className="text-xl font-bold text-white">
                  {result.passed ? "Assessment Passed!" : "Passing Threshold Not Met"}
                </h4>
                <p className="text-2xl font-black mt-1 font-mono text-sovela-teal">
                  {result.score_pct}%
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Required: {result.passing_score_pct}% | Correct: {result.correct_count} of {result.total_questions}
                </p>
              </div>

              <p className="text-sm text-slate-300 max-w-md mx-auto">
                {result.feedback}
              </p>

              {result.passed && (
                <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-semibold">
                  <span>+{result.points_awarded} Skill Mastery Points Awarded</span>
                </div>
              )}

              <div className="pt-2">
                <button
                  onClick={onClose}
                  className="px-6 py-2.5 rounded-xl bg-sovela-teal text-white font-medium hover:bg-teal-500 transition-all shadow-md"
                >
                  Return to Roadmap
                </button>
              </div>
            </div>
          )}

          {!loading && !result && assessment && (
            <div className="space-y-6">
              <div className="p-3.5 rounded-xl bg-slate-900/40 border border-sovela-border text-xs text-slate-300 flex items-center justify-between">
                <span>Total Questions: {assessment.questions.length}</span>
                <span>Passing Grade: {assessment.passing_score_pct}%</span>
              </div>

              {assessment.questions.map((q, idx) => (
                <div key={q.id} className="p-4 rounded-xl bg-slate-900/60 border border-sovela-border space-y-3">
                  <div className="text-sm font-semibold text-white">
                    <span className="text-sovela-teal mr-2 font-mono">Q{idx + 1}.</span>
                    {q.question}
                  </div>
                  <div className="space-y-2">
                    {q.options.map((opt, optIdx) => {
                      const isSelected = answers[String(q.id)] === optIdx;
                      return (
                        <button
                          key={optIdx}
                          type="button"
                          onClick={() => handleSelectOption(q.id, optIdx)}
                          className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs sm:text-sm border transition-all flex items-center justify-between ${
                            isSelected
                              ? "bg-sovela-teal/20 border-sovela-teal text-white shadow-sm"
                              : "bg-slate-800/40 border-sovela-border text-slate-300 hover:bg-slate-800 hover:text-white"
                          }`}
                        >
                          <span>{opt}</span>
                          <div className={`w-4 h-4 rounded-full border flex items-center justify-center ml-3 flex-shrink-0 ${
                            isSelected ? "border-sovela-teal bg-sovela-teal" : "border-slate-600"
                          }`}>
                            {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {!result && assessment && (
          <div className="p-4 border-t border-sovela-border bg-slate-900/50 flex items-center justify-between">
            <span className="text-xs text-slate-400">
              Answered: {Object.keys(answers).length} of {assessment.questions.length}
            </span>
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting || Object.keys(answers).length < assessment.questions.length}
                className="px-5 py-2 rounded-xl bg-sovela-teal text-white text-sm font-medium hover:bg-teal-500 disabled:opacity-50 transition-all flex items-center space-x-2 shadow-md shadow-sovela-teal/20"
              >
                {submitting && <RefreshCw className="w-4 h-4 animate-spin" />}
                <span>Submit Assessment</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
