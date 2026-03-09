import { useQuery } from "@tanstack/react-query";
import {
  fetchDailyLeaderboard,
  fetchMonthlyLeaderboard,
  fetchTodayStats,
  type DailyLeaderboardResponse,
  type MonthlyLeaderboardResponse,
  type TodayStatsResponse,
} from "@/lib/api";

export function useDailyLeaderboard(date?: string) {
  return useQuery<DailyLeaderboardResponse>({
    queryKey: ["leaderboard", "daily", date ?? "today"],
    queryFn: () => fetchDailyLeaderboard(date),
    refetchInterval: 60_000,
  });
}

export function useMonthlyLeaderboard(month?: string) {
  return useQuery<MonthlyLeaderboardResponse>({
    queryKey: ["leaderboard", "monthly", month ?? "current"],
    queryFn: () => fetchMonthlyLeaderboard(month),
    refetchInterval: 60_000,
  });
}

export function useTodayStats() {
  return useQuery<TodayStatsResponse>({
    queryKey: ["stats", "today"],
    queryFn: fetchTodayStats,
    refetchInterval: 60_000,
  });
}

// ---------- Formatting ----------

export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return "--:--";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "--:--";
  return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", hour12: true });
}

export function toDateParam(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function toMonthParam(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}
