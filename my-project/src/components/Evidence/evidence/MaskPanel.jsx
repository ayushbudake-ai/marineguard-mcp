export default function MaskPanel({ evidence, detection }) {
  return (
    <section className="border border-line bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm text-fg">Segmentation mask</h2>
        <span className="font-mono text-xs text-muted">SAM2</span>
      </div>
      <div className="relative aspect-[4/3] overflow-hidden bg-surface2">
        <svg viewBox="0 0 300 180" className="h-full w-full" role="img" aria-label={`${detection.objectClass} segmentation mask`}>
          <path d={evidence.maskPath} fill="rgba(63,184,175,0.35)" stroke="#3FB8AF" strokeWidth="2" />
        </svg>
      </div>
      <div className="mt-3 font-mono text-xs text-muted">Irregular target contour</div>
    </section>
  );
}