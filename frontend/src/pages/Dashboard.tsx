import { Link, useLocation } from "react-router-dom";
import { Clock, CalendarDays, Users, Flame, BarChart3, Target } from "lucide-react";
import { useDailyLeaderboard, useMonthlyLeaderboard, useTodayStats, formatDuration } from "@/hooks/useLeaderboardData";
import { LeaderboardRow } from "@/components/LeaderboardRow";
import { LeaderboardSection } from "@/components/LeaderboardSection";
import { StatCard } from "@/components/StatCard";
import { LoadingState } from "@/components/LoadingState";
import { EmptyState } from "@/components/EmptyState";
import { DeepWorkRules } from "@/components/DeepWorkRules";
import logo from "@/assets/logo.png";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/", icon: <BarChart3 className="w-4 h-4" /> },
  { label: "Today", href: "/today", icon: <Clock className="w-4 h-4" /> },
  { label: "Monthly", href: "/monthly", icon: <CalendarDays className="w-4 h-4" /> },
];

export default function Dashboard() {
  const location = useLocation();
  const daily = useDailyLeaderboard();
  const monthly = useMonthlyLeaderboard();
  const stats = useTodayStats();

  const dailyEntries = daily.data?.entries ?? [];
  const monthlyEntries = monthly.data?.entries ?? [];

  const topDaily = dailyEntries.slice(0, 8);
  const topMonthly = monthlyEntries.slice(0, 8);

  const dailyMax = topDaily.length > 0 ? topDaily[0].total_minutes : 1;
  const monthlyMax = topMonthly.length > 0 ? topMonthly[0].performance_score : 1;

  // Year progress
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 1);
  const endOfYear = new Date(now.getFullYear() + 1, 0, 1);
  const yearProgress = Math.round(((now.getTime() - startOfYear.getTime()) / (endOfYear.getTime() - startOfYear.getTime())) * 100);

  // Month progress
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  const monthProgress = Math.round(((now.getTime() - startOfMonth.getTime()) / (endOfMonth.getTime() - startOfMonth.getTime())) * 100);

  return (
    <div className="min-h-screen bg-navy-deep">
      {/* Background cityscape */}
      <div
        className="fixed inset-0 bg-cover bg-center bg-no-repeat opacity-[0.03] pointer-events-none"
        style={{ backgroundImage: "url(/cityscape.jpg)" }}
      />

      {/* Navigation */}
      <nav className="sticky top-0 z-40 bg-navy-deep/80 backdrop-blur-xl border-b border-border/30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-3">
              <img src={logo} alt="TDWC" className="h-9 w-auto" />
              <div className="hidden sm:block">
                <p className="text-sm font-semibold text-cream tracking-wide">The Deep Work Club</p>
                <p className="text-[10px] text-cream-faint uppercase tracking-[0.15em]">Performance Tracker</p>
              </div>
            </Link>

            <div className="flex items-center gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  to={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200
                    ${location.pathname === item.href
                      ? "bg-gold/10 text-gold border border-gold/20"
                      : "text-cream-muted hover:text-cream hover:bg-navy-elevated/50"
                    }
                  `}
                >
                  {item.icon}
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </nav>

      <main className="relative max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8 animate-fade-up">
        {/* Hero stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <StatCard
            label="Today's Deep Work"
            value={stats.data ? formatDuration(stats.data.total_minutes) : "—"}
            icon={<Flame className="w-5 h-5" />}
            subtext={stats.data ? `${stats.data.active_members} active members` : undefined}
            highlight
          />
          <StatCard
            label="Active Members"
            value={stats.data?.active_members ?? "—"}
            icon={<Users className="w-5 h-5" />}
            subtext="In the room today"
          />
          <StatCard
            label="Year Progress"
            value={`${yearProgress}%`}
            icon={<Target className="w-5 h-5" />}
            progress={yearProgress}
            subtext={`Day ${Math.ceil((now.getTime() - startOfYear.getTime()) / 86400000)} of 365`}
            accent="blue"
          />
          <StatCard
            label="Month Progress"
            value={`${monthProgress}%`}
            icon={<CalendarDays className="w-5 h-5" />}
            progress={monthProgress}
            subtext={now.toLocaleString("default", { month: "long", year: "numeric" })}
            accent="blue"
          />
        </div>

        {/* Leaderboards */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Daily */}
          <LeaderboardSection
            title="Today's Leaderboard"
            icon={<Clock className="w-5 h-5" />}
            href="/today"
            onRefresh={() => daily.refetch()}
            isRefreshing={daily.isFetching}
          >
            {daily.isLoading ? (
              <LoadingState />
            ) : topDaily.length === 0 ? (
              <EmptyState message="No deep work sessions recorded today" />
            ) : (
              <div className="space-y-1">
                {topDaily.map((entry, i) => (
                  <LeaderboardRow
                    key={entry.user_email}
                    rank={i + 1}
                    name={entry.user_name}
                    value={formatDuration(entry.total_minutes)}
                    subtitle={`${entry.session_count} session${entry.session_count !== 1 ? "s" : ""}`}
                    maxValue={dailyMax}
                    currentValue={entry.total_minutes}
                  />
                ))}
              </div>
            )}
          </LeaderboardSection>

          {/* Monthly */}
          <LeaderboardSection
            title="Monthly Consistency"
            icon={<CalendarDays className="w-5 h-5" />}
            href="/monthly"
            onRefresh={() => monthly.refetch()}
            isRefreshing={monthly.isFetching}
          >
            {monthly.isLoading ? (
              <LoadingState />
            ) : topMonthly.length === 0 ? (
              <EmptyState message="No data for this month yet" />
            ) : (
              <div className="space-y-1">
                {topMonthly.map((entry, i) => (
                  <LeaderboardRow
                    key={entry.user_email}
                    rank={i + 1}
                    name={entry.user_name}
                    value={`${entry.performance_score.toFixed(1)} pts`}
                    subtitle={`${formatDuration(entry.total_minutes)} · ${entry.unique_days} day${entry.unique_days !== 1 ? "s" : ""}`}
                    maxValue={monthlyMax}
                    currentValue={entry.performance_score}
                  />
                ))}
              </div>
            )}
          </LeaderboardSection>
        </div>

        {/* Deep Work Rules */}
        <div className="rounded-2xl bg-navy-surface/60 glass-subtle border border-border/50 p-6 shadow-elevated">
          <DeepWorkRules />
        </div>

        {/* Footer */}
        <footer className="text-center pb-8">
          <p className="text-xs text-cream-faint/40">
            The Deep Work Club &middot; Track your focus, build consistency
          </p>
        </footer>
      </main>
    </div>
  );
}
