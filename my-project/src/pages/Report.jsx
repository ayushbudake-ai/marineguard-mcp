import { useEffect, useState } from "react";
import { fetchReports, generateReport } from "./marineguard";

export default function Reports() {
  const [reports, setReports] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchReports().then(setReports);
  }, []);

  async function handleGenerate(format) {
    setGenerating(true);
    const report = await generateReport({ format });
    setReports((prev) => [
      { id: report.id, label: `Generated packet (${format})`, createdAt: report.createdAt, detections: 0, formats: [format] },
      ...(prev ?? []),
    ]);
    setGenerating(false);
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-xl text-fg">Reports</h1>
      <p className="mt-1 text-sm text-muted">
        Evidence packets exported from completed surveys — PDF, GeoJSON, and S-100 formats.
      </p>

      <div className="mt-6 flex flex-wrap gap-3 border border-line bg-surface px-4 py-3">
        <span className="text-xs uppercase tracking-wide text-muted">Generate</span>
        {["pdf", "geojson", "s-100"].map((format) => (
          <button
            key={format}
            onClick={() => handleGenerate(format)}
            disabled={generating}
            className="border border-line px-3 py-1.5 text-xs uppercase text-fg hover:border-teal/60 hover:text-teal disabled:opacity-50"
          >
            {format}
          </button>
        ))}
        {generating && <span className="text-xs text-muted">Generating…</span>}
      </div>

      <div className="mt-8">
        {!reports ? (
          <div className="text-sm text-muted">Loading reports…</div>
        ) : reports.length === 0 ? (
          <div className="border border-line bg-surface px-4 py-6 text-sm text-muted">No reports yet.</div>
        ) : (
          <ul className="divide-y divide-line/60 border border-line bg-surface">
            {reports.map((r) => (
              <li key={r.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <div className="text-sm text-fg">{r.label}</div>
                  <div className="mt-0.5 font-mono text-xs text-muted">
                    {r.id} — {new Date(r.createdAt).toLocaleString()}
                    {r.detections ? ` — ${r.detections} detections` : ""}
                  </div>
                </div>
                <div className="flex gap-2">
                  {r.formats.map((f) => (
                    <span key={f} className="border border-line px-2 py-1 font-mono text-[10px] uppercase text-muted">
                      {f}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="mt-4 text-xs text-muted">
        No real files are produced yet — export_report (Module 5/6) isn't wired to a backend, so generated
        entries have no downloadUrl until that exists.
      </p>
    </div>
  );
}
