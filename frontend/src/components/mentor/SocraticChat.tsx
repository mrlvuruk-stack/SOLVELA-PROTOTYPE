"use client";

import React, { useState, useEffect } from "react";
import { 
  MessageSquare, Send, Sparkles, Bot, User as UserIcon, Zap, 
  Plus, History, Clock, ChevronRight, ShieldCheck 
} from "lucide-react";
import { apiFetch, UserSession } from "../../lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  modelUsed?: string;
  ttfbMs?: number;
  turnaroundMs?: number;
  failoverTriggered?: boolean;
}

interface ChatSessionSummary {
  id: string;
  title: string;
  domain: string;
  updated_at: string;
  message_count: number;
}

interface SocraticChatProps {
  session: UserSession | null;
  onOpenAuth: () => void;
}

export function SocraticChat({ session, onOpenAuth }: SocraticChatProps) {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Greetings. I am your Sovela Socratic Mentor. I am designed not to feed you direct answers, but to ask diagnostic questions, decompose complexity, and guide your first-principles understanding. What challenge or concept would you like to master today?",
      modelUsed: "claude-haiku-5-5",
      ttfbMs: 38,
      turnaroundMs: 65,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSessionsList, setShowSessionsList] = useState(false);

  const quickPrompts = [
    "Break down dynamic programming memoization vs tabulation",
    "How does two-phase commit handle coordinator crashes?",
    "Review my system design approach for high-concurrency feed",
    "What is the mathematical difference between BFS and Dijkstra?",
  ];

  async function loadSessions() {
    if (!session) return;
    try {
      const data = await apiFetch<ChatSessionSummary[]>("/intelligence/socratic/sessions");
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        selectSession(data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function selectSession(sessionId: string) {
    setActiveSessionId(sessionId);
    try {
      const msgs = await apiFetch<any[]>(`/intelligence/socratic/sessions/${sessionId}`);
      if (msgs.length > 0) {
        setMessages(
          msgs.map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
            modelUsed: m.model_used,
            ttfbMs: m.ttfb_ms,
            turnaroundMs: m.total_turnaround_ms,
          }))
        );
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleNewSession() {
    if (!session) {
      onOpenAuth();
      return;
    }
    try {
      const newS = await apiFetch<ChatSessionSummary>("/intelligence/socratic/sessions", {
        method: "POST",
        body: JSON.stringify({ title: "New Socratic Inquiry" }),
      });
      setSessions((prev) => [newS, ...prev]);
      setActiveSessionId(newS.id);
      setMessages([
        {
          role: "assistant",
          content:
            "New Socratic thread initialized. Name the algorithm, architectural question, or proof you are investigating.",
          modelUsed: "claude-haiku-5-5",
          ttfbMs: 35,
          turnaroundMs: 50,
        },
      ]);
      setShowSessionsList(false);
    } catch (e) {
      console.error(e);
    }
  }

  useEffect(() => {
    loadSessions();
  }, [session]);

  async function handleSend(promptText: string) {
    const text = promptText || input;
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      let resp: any;
      if (session && activeSessionId) {
        resp = await apiFetch(`/intelligence/socratic/sessions/${activeSessionId}/message`, {
          method: "POST",
          body: JSON.stringify({ prompt: text, simulated_delay_ms: 75.0 }),
        });
      } else {
        resp = await apiFetch("/intelligence/socratic/chat", {
          method: "POST",
          body: JSON.stringify({ prompt: text, simulated_delay_ms: 75.0 }),
        });
      }

      const assistantMsg: Message = {
        role: "assistant",
        content: resp.content,
        modelUsed: resp.model_used,
        ttfbMs: resp.ttfb_ms,
        turnaroundMs: resp.total_turnaround_ms,
        failoverTriggered: resp.failover_triggered,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      if (session) loadSessions();
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Apologies, an error occurred: ${err.message}. Please verify backend connectivity.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-6xl mx-auto py-6 px-4 lg:px-8 h-[calc(100vh-5rem)] flex flex-col space-y-4">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-3 border-b border-sovela-border">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-sovela-teal/15 flex items-center justify-center">
            <MessageSquare className="h-4 w-4 text-sovela-teal" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center space-x-2">
              <span>Socratic Pedagogical Dialogue</span>
              {session && (
                <span className="text-[10px] font-mono font-normal text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded-full border border-emerald-800/30">
                  Memory Linked
                </span>
              )}
            </h2>
            <p className="text-[11px] text-sovela-text-muted">
              Multi-provider dual-router with 200ms TTFB abort probe • Pinned to active {messages[messages.length - 1]?.modelUsed || "claude-haiku-5-5"}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {session && (
            <button
              onClick={() => setShowSessionsList(!showSessionsList)}
              className="px-3 py-1.5 rounded-xl border border-sovela-border bg-sovela-card hover:border-slate-600 text-slate-300 text-xs flex items-center space-x-1.5 transition"
            >
              <History className="h-3.5 w-3.5 text-sovela-teal" />
              <span>Threads ({sessions.length})</span>
            </button>
          )}

          <button
            onClick={handleNewSession}
            className="px-3.5 py-1.5 rounded-xl bg-sovela-teal hover:bg-sky-400 text-white text-xs font-semibold flex items-center space-x-1.5 transition shadow-sm"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New Thread</span>
          </button>
        </div>
      </div>

      {/* Main Dialogue Layout */}
      <div className="flex-1 flex space-x-4 overflow-hidden">
        {/* Sessions Sidebar (if toggled) */}
        {showSessionsList && session && (
          <div className="w-64 bg-sovela-card border border-sovela-border rounded-2xl p-3 flex flex-col space-y-2 overflow-y-auto animate-in fade-in">
            <div className="text-[11px] font-bold text-slate-400 px-2 uppercase tracking-wider">
              Previous Threads
            </div>
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  selectSession(s.id);
                  setShowSessionsList(false);
                }}
                className={`p-2.5 rounded-xl text-left text-xs transition flex flex-col space-y-1 ${
                  s.id === activeSessionId
                    ? "bg-sovela-teal/15 border border-sovela-teal text-white"
                    : "bg-sovela-navy/60 hover:bg-slate-800 text-slate-300 border border-transparent"
                }`}
              >
                <span className="font-semibold truncate">{s.title}</span>
                <span className="text-[10px] text-slate-500">
                  {new Date(s.updated_at).toLocaleDateString()} • {s.message_count} turns
                </span>
              </button>
            ))}
          </div>
        )}

        {/* Chat Messages Scroll Window */}
        <div className="flex-1 bg-sovela-navy/40 border border-sovela-border rounded-2xl flex flex-col p-4 overflow-hidden">
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {messages.map((m, idx) => {
              const isUser = m.role === "user";
              return (
                <div
                  key={idx}
                  className={`flex items-start space-x-3 ${isUser ? "flex-row-reverse space-x-reverse" : "flex-row"}`}
                >
                  <div
                    className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold ${
                      isUser
                        ? "bg-sovela-teal text-white"
                        : "bg-sovela-card border border-sovela-border text-sovela-teal"
                    }`}
                  >
                    {isUser ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  <div className={`space-y-1 max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? "bg-sovela-teal text-white rounded-tr-none shadow-md"
                          : "bg-sovela-card border border-sovela-border text-slate-200 rounded-tl-none shadow-md"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{m.content}</p>
                    </div>

                    {!isUser && m.modelUsed && (
                      <div className="flex items-center space-x-2 text-[10px] text-slate-500 px-1 font-mono">
                        <span className="text-sovela-teal">{m.modelUsed}</span>
                        {m.ttfbMs && <span>• TTFB: {Math.round(m.ttfbMs)}ms</span>}
                        {m.turnaroundMs && <span>• Total: {Math.round(m.turnaroundMs)}ms</span>}
                        {m.failoverTriggered && (
                          <span className="text-amber-400 font-bold">• Fallback Engaged</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex items-start space-x-3">
                <div className="h-8 w-8 rounded-xl bg-sovela-card border border-sovela-border flex items-center justify-center text-sovela-teal">
                  <Bot className="h-4 w-4 animate-spin" />
                </div>
                <div className="p-3.5 rounded-2xl bg-sovela-card border border-sovela-border text-xs text-slate-400 rounded-tl-none flex items-center space-x-2">
                  <Sparkles className="h-3.5 w-3.5 text-sovela-teal animate-pulse" />
                  <span>Socratic Scaffolding Engine formulating diagnostic probe...</span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Prompts */}
          <div className="pt-3 pb-2 flex items-center space-x-2 overflow-x-auto text-[11px]">
            {quickPrompts.map((qp, i) => (
              <button
                key={i}
                onClick={() => handleSend(qp)}
                className="whitespace-nowrap px-3 py-1 rounded-full bg-sovela-card border border-sovela-border text-slate-300 hover:border-sovela-teal hover:text-white transition"
              >
                {qp}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="pt-2">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend(input);
              }}
              className="flex items-center space-x-2 bg-sovela-card border border-sovela-border rounded-xl p-2 focus-within:border-sovela-teal transition"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a conceptual, algorithmic, or systems question..."
                className="flex-1 bg-transparent px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="p-2 rounded-lg bg-sovela-teal hover:bg-sky-400 text-white transition disabled:opacity-40"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
