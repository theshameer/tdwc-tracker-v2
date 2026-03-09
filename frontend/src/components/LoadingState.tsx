export function LoadingState() {
  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center gap-3 px-3 py-3 rounded-xl">
          <div className="w-8 h-8 rounded-full bg-navy-light/50 animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-24 rounded bg-navy-light/50 animate-pulse" />
            <div className="h-2 w-16 rounded bg-navy-light/30 animate-pulse" />
          </div>
          <div className="h-3 w-12 rounded bg-navy-light/50 animate-pulse" />
        </div>
      ))}
    </div>
  );
}
