import { type ReactNode } from "react";
import { Trophy, Medal, Award } from "lucide-react";

interface Props {
  rank: number;
  name: string;
  value: string;
  subtitle?: string;
  maxValue: number;
  currentValue: number;
}

const rankIcons: Record<number, ReactNode> = {
  1: <Trophy className="w-4 h-4 text-gold" />,
  2: <Medal className="w-4 h-4 text-cream-muted" />,
  3: <Award className="w-4 h-4 text-amber-600" />,
};

export function LeaderboardRow({ rank, name, value, subtitle, maxValue, currentValue }: Props) {
  const pct = maxValue > 0 ? Math.min((currentValue / maxValue) * 100, 100) : 0;
  const isTop3 = rank <= 3;

  return (
    <div
      className={`group relative flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200
        ${isTop3 ? "bg-gold/[0.04] border border-gold/10 hover:border-gold/20" : "hover:bg-navy-elevated/50 border border-transparent"}
      `}
    >
      {/* Rank */}
      <div className="w-8 h-8 flex items-center justify-center shrink-0">
        {rankIcons[rank] ?? (
          <span className="text-sm text-cream-faint font-medium">{rank}</span>
        )}
      </div>

      {/* Name + subtitle */}
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium truncate ${isTop3 ? "text-cream" : "text-cream-muted"}`}>
          {name}
        </p>
        {subtitle && (
          <p className="text-xs text-cream-faint mt-0.5 truncate">{subtitle}</p>
        )}
      </div>

      {/* Bar + Value */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="w-24 sm:w-32 h-1.5 rounded-full bg-navy-light/50 overflow-hidden hidden sm:block">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${
              isTop3 ? "bg-gradient-to-r from-gold-dim to-gold bar-glow" : "bg-cream-faint/30"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className={`text-sm font-semibold tabular-nums min-w-[4rem] text-right ${isTop3 ? "text-gold" : "text-cream-muted"}`}>
          {value}
        </span>
      </div>
    </div>
  );
}
