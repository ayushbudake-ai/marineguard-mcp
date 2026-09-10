import RiskBadge from "./RiskBadge";

export default function FirewallEventFeed({ events }) {
  if (!events.length) {
    return (
      <div className="border border-line bg-surface px-4 py-6 text-sm text-muted">
        No firewall events yet. Events appear here as detections are evaluated against the risk taxonomy.
      </div>
    );
  }

  return (
    <div className="max-h-[420px] overflow-y-auto border border-line bg-surface">
      <ul className="divide-y divide-line/60">
        {events.map((e) => (
          <li
            key={e.id}
            className={`animate-row-enter flex items-start justify-between gap-4 px-4 py-3 ${
              e.level === "CRITICAL" ? "bg-coral/5" : ""
            }`}
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <RiskBadge level={e.level} size="sm" />
                <span className="truncate font-mono text-xs text-muted">{e.sourceId}</span>
              </div>
              <div className="mt-1 text-sm text-fg">{e.action}</div>
              <div className="mt-0.5 font-mono text-xs text-muted">{e.detail}</div>
            </div>
            <div className="shrink-0 font-mono text-xs text-muted">
              {new Date(e.timestamp).toLocaleTimeString()}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
