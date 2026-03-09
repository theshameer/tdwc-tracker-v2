import { type ReactNode } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, RefreshCw } from "lucide-react";

interface Props {
  title: string;
  icon: ReactNode;
  href: string;
  children: ReactNode;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function LeaderboardSection({ title, icon, href, children, onRefresh, isRefreshing }: Props) {
  return (
    <div className="rounded-2xl bg-navy-surface/60 glass-subtle border border-border/50 overflow-hidden shadow-elevated">
      {/* Header */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-border/30">
        <div className="flex items-center gap-2.5">
          <span className="text-gold">{icon}</span>
          <h2 className="font-semibold text-cream text-base">{title}</h2>
        </div>
        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="p-1.5 rounded-lg hover:bg-navy-elevated transition-colors text-cream-faint hover:text-cream disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            </button>
          )}
          <Link
            to={href}
            className="p-1.5 rounded-lg hover:bg-navy-elevated transition-colors text-cream-faint hover:text-gold"
          >
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 sm:p-6">
        {children}
      </div>
    </div>
  );
}
