import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Clock, CalendarDays, BarChart3, ArrowLeft, Users, TrendingUp, Flame } from "lucide-react";
import { useMonthlyLeaderboard, formatDuration, toMonthParam } from "@/hooks/useLeaderboardData";
import { LeaderboardRow } from "@/components/LeaderboardRow";
import { StatCard } from "@/components/StatCard";
import { LoadingState } from "@/components/LoadingState";
import { EmptyState } from "@/components/EmptyState";
import { MonthFilter } from "@/components/MonthFilter";
import logo from "@/assets/logo.png";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/", icon: <BarChart3 className="w-4 h-4" /> },
  { label: "Today", href: "/today", icon: <Clock className="w-4 h-4" /> },
  { label: "Monthly", href: "/monthly", icon: <CalendarDays className="w-4 h-4" /> },
];

export default function MonthlyConsistency() {
  const location = useLocation();
  const [selectedMonth, setSelectedMonth] = useState(() => new Date());

  const monthParam = toMonthParam(selectedMonth);
  const monthly = useMonthlyLeaderboard(monthParam);

  const entries = monthly.data?.entries ?? [];
  const maxScore = entries.length > 0 ? entries[0].performance_score : 1;

  const totalHours = entries.reduce((sum, e) => sum + e.total_minutes / 60, 0);
  const avgDays = entries.length > 0 ? entries.reduce((sum, e) => sum + e.unique_days, 0) / entries.length : 0;

  const displayMonth = selectedMonth.toLocaleDateString("en-GB", { month: "long", year: "numeric" });

  return (
    <div className="min-h-screen bg-navy-deep">
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

      <main className="relative max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6 animate-fade-up">
        {/* Page header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="p-2 rounded-xl hover:bg-navy-elevated/50 transition-colors text-cream-faint hover:text-cream">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-xl font-semibold text-cream">Monthly Consistency</h1>
              <p className="text-sm text-cream-faint mt-0.5">{displayMonth}</p>
            </div>
          </div>
          <MonthFilter selectedMonth={selectedMonth} onMonthChange={setSelectedMonth} />
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-3">
          <StatCard
            label="Total Club Hours"
            value={`${totalHours.toFixed(0)}h`}
            icon={<Flame className="w-5 h-5" />}
            highlight
          />
          <StatCard
            label="Members"
            value={entries.length}
            icon={<Users className="w-5 h-5" />}
            subtext={`in ${displayMonth}`}
          />
          <StatCard
            label="Avg Days Active"
            value={avgDays.toFixed(1)}
            icon={<TrendingUp className="w-5 h-5" />}
            accent="blue"
            subtext="days per member"
          />
        </div>

        {/* Score explanation */}
        <div className="rounded-xl bg-gold/[0.04] border border-gold/10 px-4 py-3">
          <p className="text-xs text-cream-faint leading-relaxed">
            <span className="text-gold font-medium">Score formula: </span>
            (Total hours &times; 0.7) + (Days attended &times; 0.3) — rewards both volume and consistency.
          </p>
        </div>

        {/* Full leaderboard */}
        <div className="rounded-2xl bg-navy-surface/60 glass-subtle border border-border/50 overflow-hidden shadow-elevated">
          <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-border/30">
            <div className="flex items-center gap-2.5">
              <CalendarDays className="w-5 h-5 text-gold" />
              <h2 className="font-semibold text-cream text-base">Consistency Leaderboard</h2>
            </div>
            <span className="text-xs text-cream-faint tabular-nums">
              {entries.length} member{entries.length !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="p-4 sm:p-6">
            {monthly.isLoading ? (
              <LoadingState />
            ) : entries.length === 0 ? (
              <EmptyState message="No data for this month yet" />
            ) : (
              <div className="space-y-1">
                {entries.map((entry, i) => (
                  <LeaderboardRow
                    key={entry.user_email}
                    rank={i + 1}
                    name={entry.user_name}
                    value={`${entry.performance_score.toFixed(1)} pts`}
                    subtitle={`${formatDuration(entry.total_minutes)} · ${entry.unique_days} day${entry.unique_days !== 1 ? "s" : ""} · ${entry.session_count} session${entry.session_count !== 1 ? "s" : ""}`}
                    maxValue={maxScore}
                    currentValue={entry.performance_score}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
