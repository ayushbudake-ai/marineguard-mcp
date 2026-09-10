export default function BathymetryPanel({ evidence }) {
  const points = evidence.bathymetry.map((depth, index) => `${(index / (evidence.bathymetry.length - 1)) * 100},${depth * 2}`).join(" ");

  return (
    <section className="border border-line bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm text-fg">Bathymetry profile</h2>
        <span className="font-mono text-xs text-muted">along-track</span>
      </div>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-36 w-full bg-surface2" role="img" aria-label="Bathymetry depth profile">
        <polyline points={points} fill="none" stroke="#E8A33D" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="mt-3 font-mono text-xs text-muted">Depth protrusion detected near target track</div>
    </section>
  );
}