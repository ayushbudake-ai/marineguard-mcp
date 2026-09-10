export default function StatCard({ label, value, unit, tone = "default", unavailable = false }) {
  const toneClass = {
    default: "text-fg",
    teal: "text-teal",
    amber: "text-amber",
    coral: "text-coral",
  }[tone];

  return (
    <div className="border border-line bg-surface px-5 py-4">
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      {unavailable ? (
        <div className="mt-2 font-mono text-2xl text-muted">— not yet computed</div>
      ) : (
        <div className={`mt-2 font-mono text-2xl ${toneClass}`}>
          {value}
          {unit && <span className="ml-1 text-sm text-muted">{unit}</span>}
        </div>
      )}
    </div>
  );
}