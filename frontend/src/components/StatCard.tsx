import { type ReactNode } from "react";

interface Props {
  label: string;
  value: string | number;
  icon: ReactNode;
  subtext?: string;
  progress?: number;
  accent?: "gold" | "blue";
  highlight?: boolean;
}

export function StatCard({ label, value, icon, subtext, progress, accent = "gold", highlight }: Props) {
  const accentColor = accent === "gold" ? "text-gold" : "text-accent-blue";
  const barColor = accent === "gold" ? "bg-gold" : "bg-accent-blue";

  return (
    <div
      className={`relative rounded-2xl p-4 sm:p-5 border transition-all duration-200
        ${highlight
          ? "bg-gold/[0.06] border-gold/20 shadow-elevated"
          : "bg-navy-surface/60 glass-subtle border-border/50 hover:border-border"}
      `}
    >
      {/* Icon + Label */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-medium uppercase tracking-wider text-cream-faint">{label}</span>
        <span className={accentColor}>{icon}</span>
      </div>

      {/* Value */}
      <p className={`text-2xl sm:text-3xl font-semibold tracking-tight ${highlight ? "text-gradient-gold" : "text-cream"}`}>
        {value}
      </p>

      {/* Progress bar */}
      {progress !== undefined && (
        <div className="mt-3 h-1 rounded-full bg-navy-light/50 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-1000 ease-out ${barColor}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      )}

      {/* Subtext */}
      {subtext && (
        <p className="text-xs text-cream-faint mt-2">{subtext}</p>
      )}
    </div>
  );
}
