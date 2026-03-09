import { useState, useRef, useEffect } from "react";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import { format } from "date-fns";

interface Props {
  selectedMonth: Date;
  onMonthChange: (d: Date) => void;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function MonthFilter({ selectedMonth, onMonthChange }: Props) {
  const [open, setOpen] = useState(false);
  const [viewYear, setViewYear] = useState(selectedMonth.getFullYear());
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const now = new Date();

  function selectMonth(m: number) {
    onMonthChange(new Date(viewYear, m, 1));
    setOpen(false);
  }

  function isSelected(m: number) {
    return selectedMonth.getFullYear() === viewYear && selectedMonth.getMonth() === m;
  }

  function isCurrent(m: number) {
    return now.getFullYear() === viewYear && now.getMonth() === m;
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-navy-surface/60 glass-subtle border border-border/50 hover:border-gold/30 transition-colors text-sm text-cream-muted"
      >
        <Calendar className="w-4 h-4 text-gold" />
        {format(selectedMonth, "MMMM yyyy")}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 z-50 w-64 rounded-2xl bg-navy-elevated border border-border/50 shadow-elevated p-4 animate-fade-in">
          {/* Year nav */}
          <div className="flex items-center justify-between mb-4">
            <button onClick={() => setViewYear(viewYear - 1)} className="p-1 hover:bg-navy-light rounded-lg text-cream-faint hover:text-cream">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm font-medium text-cream">{viewYear}</span>
            <button onClick={() => setViewYear(viewYear + 1)} className="p-1 hover:bg-navy-light rounded-lg text-cream-faint hover:text-cream">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Month grid */}
          <div className="grid grid-cols-3 gap-2">
            {MONTHS.map((label, i) => (
              <button
                key={label}
                onClick={() => selectMonth(i)}
                className={`py-2 rounded-xl text-xs font-medium transition-all
                  ${isSelected(i) ? "bg-gold text-navy-deep" : ""}
                  ${isCurrent(i) && !isSelected(i) ? "ring-1 ring-gold/50 text-gold" : ""}
                  ${!isSelected(i) && !isCurrent(i) ? "text-cream-muted hover:bg-navy-light" : ""}
                `}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
