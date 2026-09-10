const statusStyles = {
  accepted: "text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded",
  filtered: "text-rose-400 bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 rounded",
};

export default function DetectionTable({ detections, onInspect }) {
  if (!detections?.length) {
    return (
      <div className="border border-line bg-surface px-4 py-6 text-sm text-muted">
        No YOLO detections found in this SSS image.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto border border-line bg-surface">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-line text-xs uppercase tracking-wide text-muted">
            <th className="px-4 py-3 font-normal">ID</th>
            <th className="px-4 py-3 font-normal">Object Class</th>
            <th className="px-4 py-3 font-normal">Raw YOLO Conf.</th>
            <th className="px-4 py-3 font-normal">Bounding Box [x1, y1, x2, y2]</th>
            <th className="px-4 py-3 font-normal">Coordinates</th>
            <th className="px-4 py-3 font-normal">Role 3 Status</th>
            <th className="px-4 py-3 font-normal">Verdict Reason</th>
            <th className="px-4 py-3 font-normal"></th>
          </tr>
        </thead>
        <tbody>
          {detections.map((d) => {
            const lat = typeof d.lat === "number" ? d.lat : typeof d.latitude === "number" ? d.latitude : d.location?.latitude;
            const lng = typeof d.lng === "number" ? d.lng : typeof d.longitude === "number" ? d.longitude : d.location?.longitude;
            const rawConf = typeof d.confidence === "number" ? d.confidence : null;
            const confNorm = rawConf != null ? (rawConf > 1 ? rawConf / 100 : rawConf) : null;
            const label = d.objectClass || d.species || d.type || "Marine Debris";
            const bboxStr = d.bboxCoords || (d.bbox ? `[${d.bbox.map(c => typeof c === "number" ? c.toFixed(1) : c).join(", ")}]` : "N/A");
            const reason = d.rejectionReason || (d.status === "accepted" ? "Meets confidence threshold" : "Filtered");

            return (
              <tr key={d.id} className="border-b border-line/60 last:border-0 hover:bg-surface2">
                <td className="px-4 py-3 font-mono text-xs text-muted">{d.id}</td>
                <td className="px-4 py-3 font-medium text-fg">{label}</td>
                <td className="px-4 py-3 font-mono text-teal">
                  {confNorm != null ? `${(confNorm * 100).toFixed(1)}%` : "N/A"}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-muted">{bboxStr}</td>
                <td className="px-4 py-3 font-mono text-xs text-muted">
                  {typeof lat === "number" && typeof lng === "number"
                    ? `${lat.toFixed(4)}, ${lng.toFixed(4)}`
                    : "Location unavailable"}
                </td>
                <td className="px-4 py-3 font-mono text-xs uppercase">
                  <span className={statusStyles[d.status] || "text-muted"}>{d.status}</span>
                </td>
                <td className="px-4 py-3 text-xs text-muted max-w-xs truncate" title={reason}>
                  {reason}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onInspect?.(d)}
                    className="text-xs text-teal underline decoration-teal/40 underline-offset-2 hover:decoration-teal"
                  >
                    Inspect
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}