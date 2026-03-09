import { Crosshair, Timer, ShieldOff, Brain } from "lucide-react";

const rules = [
  {
    icon: <Crosshair className="w-5 h-5" />,
    title: "Task Clarity",
    desc: "Plan out exactly what task you will execute upon.",
  },
  {
    icon: <Timer className="w-5 h-5" />,
    title: "Duration Clarity",
    desc: "Know exactly how long you're working for.",
  },
  {
    icon: <ShieldOff className="w-5 h-5" />,
    title: "Distraction Elimination",
    desc: 'Remove every digital and physical distraction before you join the room so the "Live" timer represents pure work.',
  },
  {
    icon: <Brain className="w-5 h-5" />,
    title: "Boredom Acceptance",
    desc: 'When the task gets hard or boring, stay in the chair; this is where the "Performance Score" is truly earned.',
  },
];

export function DeepWorkRules() {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-gold/70">The Four Principles</p>
      </div>
      <div className="grid sm:grid-cols-2 gap-3">
        {rules.map((r, i) => (
          <div
            key={i}
            className="flex gap-3 p-4 rounded-2xl bg-navy-surface/40 border border-border/30 hover:border-border/50 transition-colors"
          >
            <div className="w-9 h-9 rounded-xl bg-gold/[0.07] border border-gold/10 flex items-center justify-center shrink-0 text-gold">
              {r.icon}
            </div>
            <div>
              <p className="text-sm font-medium text-cream mb-0.5">
                <span className="text-gold/60 mr-1.5 text-xs">0{i + 1}</span>
                {r.title}
              </p>
              <p className="text-xs text-cream-faint leading-relaxed">{r.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
