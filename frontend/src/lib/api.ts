const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface UserSession {
  token: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    profile?: {
      daily_capacity_minutes: number;
      weekly_capacity_hours: number;
      timezone: string;
      focus_domains: string;
      onboarding_completed: boolean;
    };
  };
}

let activeSession: UserSession | null = null;

export function setSession(session: UserSession | null) {
  activeSession = session;
  if (typeof window !== "undefined") {
    if (session) {
      localStorage.setItem("sovela_session", JSON.stringify(session));
    } else {
      localStorage.removeItem("sovela_session");
      window.dispatchEvent(new Event("sovela_session_cleared"));
    }
  }
}

export function getSession(): UserSession | null {
  if (activeSession) return activeSession;
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem("sovela_session");
    if (raw) {
      try {
        activeSession = JSON.parse(raw);
        return activeSession;
      } catch {
        return null;
      }
    }
  }
  return null;
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const session = getSession();
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (session?.token) {
    headers.set("Authorization", `Bearer ${session.token}`);
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const resp = await fetch(url, {
    ...options,
    headers,
  });

  if (!resp.ok) {
    if (resp.status === 401 && session) {
      setSession(null);
    }
    const err = await resp.json().catch(() => ({ detail: "Network request failed" }));
    throw new Error(err.detail || `Request failed with status ${resp.status}`);
  }

  return resp.json();
}
