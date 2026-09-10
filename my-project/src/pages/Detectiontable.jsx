const statusStyles = {
  accepted: "text-teal",
  filtered: "text-muted",
};

export default function DetectionTable({ detections, onInspect }) {
  if (!detections?.length) {
    return <div className="border border-line bg-surface px-4 py-6 text-sm text-muted">No detections to show yet. Run detection to populate this table.</div>;
  }

  return (
    <div className="overflow-x-auto border border-line bg-surface">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-line text-xs uppercase tracking-wide text-muted">
            <th className="px-4 py-3 font-normal">ID</th>
            <th className="px-4 py-3 font-normal">Object class</th>
            <th className="px-4 py-3 font-normal">Confidence</th>
            <th className="px-4 py-3 font-normal">Coordinates</th>
            <th className="px-4 py-3 font-normal">Status</th>
            <th className="px-4 py-3 font-normal"></th>
          </tr>
        </thead>
        <tbody>
          {detections.map((d) => (
            <tr key={d.id} className="border-b border-line/60 last:border-0 hover:bg-surface2">
              <td className="px-4 py-3 font-mono text-xs text-muted">{d.id}</td>
              <td className="px-4 py-3">{d.objectClass}</td>
              <td className="px-4 py-3 font-mono">{d.confidence.toFixed(2)}</td>
              <td className="px-4 py-3 font-mono text-xs text-muted">
                {d.lat.toFixed(4)}, {d.lng.toFixed(4)}
              </td>
              <td className={`px-4 py-3 font-mono text-xs uppercase ${statusStyles[d.status]}`}>{d.status}</td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => onInspect?.(d)}
                  className="text-xs text-teal underline decoration-teal/40 underline-offset-2 hover:decoration-teal"
                >
                  Inspect
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}