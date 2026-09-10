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
          {detections.map((d) => {
            const lat = typeof d.lat === "number" ? d.lat : typeof d.latitude === "number" ? d.latitude : d.location?.latitude;
            const lng = typeof d.lng === "number" ? d.lng : typeof d.longitude === "number" ? d.longitude : d.location?.longitude;
            const rawConf = typeof d.confidence === "number" ? d.confidence : null;
            const confNorm = rawConf != null ? (rawConf > 1 ? rawConf / 100 : rawConf) : null;
            const label = d.objectClass || d.type || d.category || "Marine Debris";

            return (
              <tr key={d.id} className="border-b border-line/60 last:border-0 hover:bg-surface2">
                <td className="px-4 py-3 font-mono text-xs text-muted">{d.id}</td>
                <td className="px-4 py-3">{label}</td>
                <td className="px-4 py-3 font-mono">{confNorm != null ? confNorm.toFixed(2) : "N/A"}</td>
                <td className="px-4 py-3 font-mono text-xs text-muted">
                  {typeof lat === "number" && typeof lng === "number"
                    ? `${lat.toFixed(4)}, ${lng.toFixed(4)}`
                    : "Location unavailable"}
                </td>
                <td className={`px-4 py-3 font-mono text-xs uppercase ${statusStyles[d.status] || "text-muted"}`}>{d.status}</td>
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