export default function OpticalPanel({ evidence, detection }) {
  return (
    <section className="border border-line bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm text-fg">Optical detection</h2>
        <span className="font-mono text-xs text-teal">{detection.confidence.toFixed(2)}</span>
      </div>
      <div className="relative aspect-[4/3] overflow-hidden bg-surface2">
        <div className="absolute inset-0 opacity-30" style={{ backgroundImage: "linear-gradient(135deg, #20343c 25%, transparent 25%), linear-gradient(315deg, #20343c 25%, transparent 25%)", backgroundSize: "24px 24px" }} />
        <div className="absolute border-2 border-teal" style={{ left: `${evidence.boxX / 3}%`, top: `${evidence.boxY / 1.5}%`, width: `${evidence.boxW / 3}%`, height: `${evidence.boxH / 1.5}%` }} />
      </div>
      <div className="mt-3 font-mono text-xs text-muted">Bounding box / {detection.objectClass}</div>
    </section>
  );
}