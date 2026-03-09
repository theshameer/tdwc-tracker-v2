import { useState, useRef, useEffect } from "react";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  selectedDate: Date | null;
  onDateChange: (date: Date | null) => void;
}

const DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export function DateFilter({ selectedDate, onDateChange }: Props) {
  const [open, setOpen] = useState(false);
  const [viewDate, setViewDate] = useState(() => selectedDate ?? new Date());
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const today = new Date();
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const monthName = viewDate.toLocaleString("default", { month: "long", year: "numeric" });

  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  function selectDay(day: number) {
    const d = new Date(year, month, day);
    onDateChange(d);
    setOpen(false);
  }

  function isSelected(day: number) {
    if (!selectedDate) return false;
    return selectedDate.getFullYear() === year && selectedDate.getMonth() === month && selectedDate.getDate() === day;
  }

  function isToday(day: number) {
    return today.getFullYear() === year && today.getMonth() === month && today.getDate() === day;
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-navy-surface/60 glass-subtle border border-border/50 hover:border-gold/30 transition-colors text-sm text-cream-muted"
      >
        <Calendar className="w-4 h-4 text-gold" />
        {selectedDate ? "Custom Date" : "Last 24h"}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 z-50 w-72 rounded-2xl bg-navy-elevated border border-border/50 shadow-elevated p-4 animate-fade-in">
          {/* Month nav */}
          <div className="flex items-center justify-between mb-4">
            <button onClick={() => setViewDate(new Date(year, month - 1, 1))} className="p-1 hover:bg-navy-light rounded-lg text-cream-faint hover:text-cream">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm font-medium text-cream">{monthName}</span>
            <button onClick={() => setViewDate(new Date(year, month + 1, 1))} className="p-1 hover:bg-navy-light rounded-lg text-cream-faint hover:text-cream">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 gap-1 mb-1">
            {DAYS.map((d) => (
              <div key={d} className="text-[10px] text-cream-faint text-center font-medium py-1">{d}</div>
            ))}
          </div>

          {/* Days */}
          <div className="grid grid-cols-7 gap-1">
            {cells.map((day, i) => (
              <button
                key={i}
                disabled={!day}
                onClick={() => day && selectDay(day)}
                className={`h-8 rounded-lg text-xs font-medium transition-all
                  ${!day ? "invisible" : ""}
                  ${day && isSelected(day) ? "bg-gold text-navy-deep" : ""}
                  ${day && isToday(day) && !isSelected(day) ? "ring-1 ring-gold/50 text-gold" : ""}
                  ${day && !isSelected(day) && !isToday(day) ? "text-cream-muted hover:bg-navy-light" : ""}
                `}
              >
                {day}
              </button>
            ))}
          </div>

          {/* Reset */}
          {selectedDate && (
            <button
              onClick={() => { onDateChange(null); setOpen(false); }}
              className="mt-3 w-full text-xs text-gold hover:text-gold-light py-1.5 rounded-lg hover:bg-gold/5 transition-colors"
            >
              Reset to Today
            </button>
          )}
        </div>
      )}
    </div>
  );
}
