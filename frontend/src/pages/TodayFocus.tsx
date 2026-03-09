import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Clock, CalendarDays, BarChart3, ArrowLeft, Users, Flame } from "lucide-react";
import { useDailyLeaderboard, useTodayStats, formatDuration, formatTime, toDateParam } from "@/hooks/useLeaderboardData";
import { LeaderboardRow } from "@/components/LeaderboardRow";
import { StatCard } from "@/components/StatCard";
import { LoadingState } from "@/components/LoadingState";
import { EmptyState } from "@/components/EmptyState";
import { DateFilter } from "@/components/DateFilter";
import logo from "@/assets/logo.png";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/", icon: <BarChart3 className="w-4 h-4" /> },
  { label: "Today", href: "/today", icon: <Clock className="w-4 h-4" /> },
  { label: "Monthly", href: "/monthly", icon: <CalendarDays className="w-4 h-4" /> },
];

export default function TodayFocus() {
  const location = useLocation();
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  const dateParam = selectedDate ? toDateParam(selectedDate) : undefined;
  const daily = useDailyLeaderboard(dateParam);
  const stats = useTodayStats();

  const entries = daily.data?.entries ?? [];
  const maxMinutes = entries.length > 0 ? entries[0].total_minutes : 1;

  const totalMinutes = entries.reduce((sum, e) => sum + e.total_minutes, 0);
  const totalSessions = entries.reduce((sum, e) => sum + e.session_count, 0);

  const displayDate = selectedDate
    ? selectedDate.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" })
    : new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

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
              <h1 className="text-xl font-semibold text-cream">Today's Focus</h1>
              <p className="text-sm text-cream-faint mt-0.5">{displayDate}</p>
            </div>
          </div>
          <DateFilter selectedDate={selectedDate} onDateChange={setSelectedDate} />
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-3">
          <StatCard
            label="Total Deep Work"
            value={formatDuration(totalMinutes)}
            icon={<Flame className="w-5 h-5" />}
            highlight
          />
          <StatCard
            label="Members"
            value={entries.length}
            icon={<Users className="w-5 h-5" />}
            subtext={!selectedDate && stats.data ? "today" : undefined}
          />
          <StatCard
            label="Sessions"
            value={totalSessions}
            icon={<Clock className="w-5 h-5" />}
            accent="blue"
          />
        </div>

        {/* Full leaderboard */}
        <div className="rounded-2xl bg-navy-surface/60 glass-subtle border border-border/50 overflow-hidden shadow-elevated">
          <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-border/30">
            <div className="flex items-center gap-2.5">
              <Clock className="w-5 h-5 text-gold" />
              <h2 className="font-semibold text-cream text-base">Daily Leaderboard</h2>
            </div>
            <span className="text-xs text-cream-faint tabular-nums">
              {entries.length} member{entries.length !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="p-4 sm:p-6">
            {daily.isLoading ? (
              <LoadingState />
            ) : entries.length === 0 ? (
              <EmptyState message={selectedDate ? "No sessions recorded on this date" : "No deep work sessions recorded today"} />
            ) : (
              <div className="space-y-1">
                {entries.map((entry, i) => (
                  <LeaderboardRow
                    key={entry.user_email}
                    rank={i + 1}
                    name={entry.user_name}
                    value={formatDuration(entry.total_minutes)}
                    subtitle={`${formatTime(entry.first_join)} — ${formatTime(entry.last_leave)} · ${entry.session_count} session${entry.session_count !== 1 ? "s" : ""}`}
                    maxValue={maxMinutes}
                    currentValue={entry.total_minutes}
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
