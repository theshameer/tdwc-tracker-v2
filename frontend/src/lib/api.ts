const API_BASE = "https://tdwc-zoom-tracker-production.up.railway.app";

// ---------- Response types ----------

export interface DailyEntry {
  user_email: string;
  user_name: string;
  total_minutes: number;
  session_count: number;
  first_join: string | null;
  last_leave: string | null;
}

export interface DailyLeaderboardResponse {
  date: string;
  timezone: string;
  entries: DailyEntry[];
}

export interface MonthlyEntry {
  user_email: string;
  user_name: string;
  total_minutes: number;
  unique_days: number;
  session_count: number;
  performance_score: number;
}

export interface MonthlyLeaderboardResponse {
  month: string;
  timezone: string;
  entries: MonthlyEntry[];
}

export interface TodayStatsResponse {
  date: string;
  total_minutes: number;
  active_members: number;
}

// ---------- Fetch helpers ----------

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function fetchDailyLeaderboard(date?: string) {
  const params = date ? `?date=${date}` : "";
  return apiFetch<DailyLeaderboardResponse>(`/leaderboard/daily${params}`);
}

export function fetchMonthlyLeaderboard(month?: string) {
  const params = month ? `?month=${month}` : "";
  return apiFetch<MonthlyLeaderboardResponse>(`/leaderboard/monthly${params}`);
}

export function fetchTodayStats() {
  return apiFetch<TodayStatsResponse>("/stats/today");
}
