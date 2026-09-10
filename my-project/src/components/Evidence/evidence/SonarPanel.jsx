export default function SonarPanel({ evidence }) {
  return (
    <section className="border border-line bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm text-fg">Side-scan sonar</h2>
        <span className="font-mono text-xs text-muted">waterfall</span>
      </div>
      <div className="grid gap-px bg-line p-px">
        {evidence.sonarRows.map((intensity, index) => (
          <div
            key={index}
            className="h-2"
            style={{
              background: `linear-gradient(90deg, rgba(63,184,175,${intensity}) 0 42%, rgba(226,87,76,${index === evidence.shadowRow ? 0.85 : 0.12}) 42% 58%, rgba(63,184,175,${intensity}) 58%)`,
            }}
          />
        ))}
      </div>
      <div className="mt-3 font-mono text-xs text-muted">Shadow row {evidence.shadowRow} / width {evidence.shadowWidth.toFixed(0)}px</div>
    </section>
  );
}