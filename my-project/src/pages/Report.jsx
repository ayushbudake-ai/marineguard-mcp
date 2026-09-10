import React, { useEffect, useState } from "react";
import { fetchReports, generateReport } from "./marineguard";
import { FileText, Download, CheckCircle2 } from "lucide-react";

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [generatingFormat, setGeneratingFormat] = useState(null);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    fetchReports().then(setReports);
  }, []);

  async function handleGenerate(format) {
    setGeneratingFormat(format);
    setMsg(null);
    try {
      const res = await generateReport({ format });
      setMsg(`Generated ${format} report: ${res.filename}`);
      const updated = await fetchReports();
      setReports(updated);
    } catch (err) {
      setMsg(`Generation failed: ${err.message}`);
    } finally {
      setGeneratingFormat(null);
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-fg">Official Survey Reports & GIS Data Exports</h1>
      <p className="mt-1 text-sm text-muted">
        Role 4 publication-grade documentation and spatial GIS datasets generated directly from active SSS detections.
      </p>

      {/* Export Generation Cards */}
      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
        {/* PDF Card */}
        <div className="border border-line bg-surface p-5 rounded-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-teal mb-2">
              <FileText size={20} />
              <h3 className="text-base font-bold text-fg">MoES Survey PDF Report</h3>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Official executive survey report with target classification tables, confidence scores, and MoES sign-off metadata.
            </p>
          </div>
          <button
            onClick={() => handleGenerate("PDF")}
            disabled={generatingFormat !== null}
            className="mt-6 w-full border border-teal/60 bg-teal/15 py-2 text-xs font-semibold text-teal rounded hover:bg-teal/25 disabled:opacity-50"
          >
            {generatingFormat === "PDF" ? "Generating PDF…" : "Generate MoES PDF Report"}
          </button>
        </div>

        {/* GeoJSON Card */}
        <div className="border border-line bg-surface p-5 rounded-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 mb-2">
              <FileText size={20} />
              <h3 className="text-base font-bold text-fg">GeoJSON GIS Dataset</h3>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Standard WGS84 GeoJSON FeatureCollection containing geotagged debris locations and properties for QGIS / ArcGIS.
            </p>
          </div>
          <button
            onClick={() => handleGenerate("GEOJSON")}
            disabled={generatingFormat !== null}
            className="mt-6 w-full border border-cyan-500/60 bg-cyan-500/15 py-2 text-xs font-semibold text-cyan-400 rounded hover:bg-cyan-500/25 disabled:opacity-50"
          >
            {generatingFormat === "GEOJSON" ? "Generating GeoJSON…" : "Generate GeoJSON Export"}
          </button>
        </div>

        {/* IHO S-100 Card */}
        <div className="border border-line bg-surface p-5 rounded-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 mb-2">
              <FileText size={20} />
              <h3 className="text-base font-bold text-fg">IHO S-100 Catalogue</h3>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              IHO S-100 / S-124 compliant electronic hydrographic navigation feature catalogue for maritime safety systems.
            </p>
          </div>
          <button
            onClick={() => handleGenerate("S100")}
            disabled={generatingFormat !== null}
            className="mt-6 w-full border border-indigo-500/60 bg-indigo-500/15 py-2 text-xs font-semibold text-indigo-400 rounded hover:bg-indigo-500/25 disabled:opacity-50"
          >
            {generatingFormat === "S100" ? "Generating S-100…" : "Generate IHO S-100 Export"}
          </button>
        </div>
      </div>

      {msg && (
        <div className="mt-6 p-4 rounded-md border border-teal/40 bg-teal/10 text-xs font-mono text-teal flex items-center gap-2">
          <CheckCircle2 size={16} />
          {msg}
        </div>
      )}

      {/* Available Reports Table */}
      <div className="mt-8 border border-line bg-surface rounded-lg overflow-hidden">
        <div className="px-5 py-4 border-b border-line">
          <h3 className="text-sm font-bold uppercase tracking-wide text-muted font-mono">
            Generated Official Artifacts & Downloads
          </h3>
        </div>

        {reports.length === 0 ? (
          <div className="px-5 py-8 text-sm text-muted text-center">
            No reports generated yet. Click a generator button above to produce official survey files.
          </div>
        ) : (
          <ul className="divide-y divide-line/60">
            {reports.map((r) => (
              <li key={r.id} className="flex items-center justify-between px-5 py-4 hover:bg-surface2 transition-colors">
                <div>
                  <div className="text-sm font-semibold text-fg flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-surface2 border border-line text-teal">
                      {r.format}
                    </span>
                    {r.title}
                  </div>
                  <div className="mt-1 font-mono text-xs text-muted">
                    File Size: {r.fileSize} · Generated: {r.createdAt}
                  </div>
                </div>

                <div>
                  <a
                    href={r.downloadUrl}
                    download
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-teal/15 text-teal border border-teal/40 hover:bg-teal/25 transition-all"
                  >
                    <Download size={14} /> Download
                  </a>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
