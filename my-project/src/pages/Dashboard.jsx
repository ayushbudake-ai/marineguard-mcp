import React, { useEffect, useState } from "react";
import { Link } from "react-router";
import { getCurrentDetections, checkHealth } from "./marineguard";
import StatCard from "./statcard";
import {
  ScanSearch,
  ShieldCheck,
  BarChart3,
  FileText,
  Activity,
  Cpu,
  Layers,
  ArrowRight,
  Sparkles,
} from "lucide-react";

export default function Dashboard() {
  const [currentResult, setCurrentResult] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCurrentDetections(), checkHealth()]).then(([det, h]) => {
      setCurrentResult(det);
      setHealth(h);
      setLoading(false);
    });
  }, []);

  const isConnected = health?.status === "ok";

  const totalDetections = currentResult?.totalDetections ?? 0;
  const acceptedCount = currentResult?.acceptedCount ?? 0;
  const filteredCount = currentResult?.filteredCount ?? 0;
  const avgConf = currentResult?.averageConfidence != null ? (currentResult.averageConfidence * 100).toFixed(1) : "—";
  const latency = currentResult?.processingTimeMs != null ? `${currentResult.processingTimeMs.toFixed(1)} ms` : "—";

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-line pb-6">
        <div>
          <div className="flex items-center gap-2 font-mono text-xs text-teal uppercase tracking-wider mb-1">
            <Sparkles size={14} /> MarineGuard Command Center
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-fg">Side-Scan Sonar Intelligence</h1>
          <p className="mt-1 text-sm text-muted">
            Autonomous marine debris identification, spatial evidence review & mission telemetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-teal/40 bg-teal/10 px-3.5 py-1.5 font-mono text-xs text-teal">
            <span className="h-2 w-2 rounded-full bg-teal animate-pulse" />
            <span className="font-bold">SSS MODEL</span> ● READY
          </div>
        </div>
      </div>

      {/* Primary KPI Metrics */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Images Analyzed"
          value={currentResult ? "1" : "0"}
          tone={currentResult ? "teal" : undefined}
        />
        <StatCard
          label="Raw Detections"
          value={currentResult ? totalDetections : "—"}
        />
        <StatCard
          label="Accepted (Role 3)"
          value={currentResult ? acceptedCount : "—"}
          tone="teal"
        />
        <StatCard
          label="Filtered (Role 3)"
          value={currentResult ? filteredCount : "—"}
          tone={filteredCount > 0 ? "amber" : undefined}
        />
      </div>

      {/* Subsystems Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* SSS MODEL */}
        <div className="border border-line/80 bg-surface/70 backdrop-blur p-5 rounded-xl flex flex-col justify-between shadow-lg shadow-black/20">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase font-mono tracking-widest text-teal bg-teal/10 border border-teal/30 px-2 py-0.5 rounded">
                Product Core
              </span>
              <Cpu size={16} className="text-teal" />
            </div>
            <h3 className="text-base font-bold text-fg">SSS MODEL</h3>
            <p className="text-xs text-muted mt-1 leading-relaxed">
              Unified Side-Scan Sonar Detection Engine running Ultralytics YOLOv8n inference on acoustic sonar imagery.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-line/60 font-mono text-[11px] text-muted flex justify-between">
            <span>Status:</span>
            <span className="text-emerald-400 font-semibold">Active & Verified</span>
          </div>
        </div>

        {/* Detection Engine */}
        <div className="border border-line/80 bg-surface/70 backdrop-blur p-5 rounded-xl flex flex-col justify-between shadow-lg shadow-black/20">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase font-mono tracking-widest text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 rounded">
                Neural Backbone
              </span>
              <Layers size={16} className="text-cyan-400" />
            </div>
            <h3 className="text-base font-bold text-fg">Detection Engine</h3>
            <p className="text-xs text-muted mt-1 leading-relaxed">
              Exp #2 augmented model weights (<code className="text-cyan-300">best.pt</code>) trained on SSS waterfall imagery.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-line/60 font-mono text-[11px] text-muted flex justify-between">
            <span>Validation F1:</span>
            <span className="text-cyan-300 font-semibold">0.9993</span>
          </div>
        </div>

        {/* Role 3 Filter */}
        <div className="border border-line/80 bg-surface/70 backdrop-blur p-5 rounded-xl flex flex-col justify-between shadow-lg shadow-black/20">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase font-mono tracking-widest text-purple-400 bg-purple-500/10 border border-purple-500/30 px-2 py-0.5 rounded">
                Mission Gate
              </span>
              <ShieldCheck size={16} className="text-purple-400" />
            </div>
            <h3 className="text-base font-bold text-fg">Role 3 Filter</h3>
            <p className="text-xs text-muted mt-1 leading-relaxed">
              Post-inference confidence filtering, non-zero geometry verification, and out-of-bounds safety checks.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-line/60 font-mono text-[11px] text-muted flex justify-between">
            <span>Threshold:</span>
            <span className="text-purple-300 font-semibold">
              {currentResult ? `${(currentResult.confidenceThreshold * 100).toFixed(0)}%` : "75%"}
            </span>
          </div>
        </div>

        {/* Export Engine */}
        <div className="border border-line/80 bg-surface/70 backdrop-blur p-5 rounded-xl flex flex-col justify-between shadow-lg shadow-black/20">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase font-mono tracking-widest text-amber bg-amber/10 border border-amber/30 px-2 py-0.5 rounded">
                Role 4 Deliverable
              </span>
              <FileText size={16} className="text-amber" />
            </div>
            <h3 className="text-base font-bold text-fg">Export Engine</h3>
            <p className="text-xs text-muted mt-1 leading-relaxed">
              Automated MoES survey dossier generation: PDF survey reports, GeoJSON packets, and IHO S-100/S-124 catalogs.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-line/60 font-mono text-[11px] text-muted flex justify-between">
            <span>Formats:</span>
            <span className="text-amber font-semibold">PDF · GeoJSON · S-100</span>
          </div>
        </div>
      </div>

      {/* Latest SSS Detection Showcase */}
      {currentResult && (
        <section className="rounded-xl border border-line bg-surface/70 backdrop-blur p-6 shadow-lg shadow-black/20 space-y-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 border-b border-line/60 pb-4">
            <div>
              <h2 className="text-lg font-bold text-fg tracking-wide font-mono">
                LATEST SSS SCAN: {currentResult.sampleName || currentResult.fileId}
              </h2>
              <p className="text-xs text-muted mt-0.5">
                Processed with <span className="text-teal font-mono">SSS MODEL</span> · Latency: {latency} · Confidence: {avgConf}%
              </p>
            </div>
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-xs text-teal font-mono border border-teal/40 bg-teal/10 px-3 py-1.5 rounded hover:bg-teal/20 transition-colors"
            >
              Analyze SSS Data <ArrowRight size={14} />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs font-mono text-muted">
                <span>INPUT SIDE-SCAN SONAR</span>
                {currentResult.imageShape && (
                  <span>{currentResult.imageShape[1]} × {currentResult.imageShape[0]} px</span>
                )}
              </div>
              <div className="rounded-lg border border-line bg-black/60 overflow-hidden flex items-center justify-center p-2 min-h-64">
                {currentResult.originalImageUrl ? (
                  <img
                    src={currentResult.originalImageUrl}
                    alt="Original SSS"
                    className="max-h-72 w-auto object-contain rounded"
                  />
                ) : (
                  <span className="text-xs text-muted font-mono">No raw image loaded</span>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs font-mono text-muted">
                <span>NEURAL BOUNDING BOX OVERLAY</span>
                <span className="text-teal">{acceptedCount} targets accepted</span>
              </div>
              <div className="rounded-lg border border-line bg-black/60 overflow-hidden flex items-center justify-center p-2 min-h-64">
                {currentResult.annotatedImageUrl ? (
                  <img
                    src={currentResult.annotatedImageUrl}
                    alt="Annotated SSS"
                    className="max-h-72 w-auto object-contain rounded"
                  />
                ) : (
                  <span className="text-xs text-muted font-mono">No detections annotated</span>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-line">
        <Link
          to="/"
          className="group flex flex-col justify-between p-4 rounded-xl border border-line bg-surface/50 hover:bg-surface hover:border-teal/50 transition-all shadow"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2.5 rounded-lg bg-teal/10 text-teal group-hover:bg-teal group-hover:text-ink transition-colors">
              <ScanSearch size={20} />
            </div>
            <ArrowRight size={16} className="text-muted group-hover:text-teal group-hover:translate-x-1 transition-all" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-fg">SSS Analysis</h4>
            <p className="text-xs text-muted mt-0.5">Run interactive demo scans or upload survey waterfall data</p>
          </div>
        </Link>

        <Link
          to="/evidence"
          className="group flex flex-col justify-between p-4 rounded-xl border border-line bg-surface/50 hover:bg-surface hover:border-cyan-500/50 transition-all shadow"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400 group-hover:bg-cyan-400 group-hover:text-ink transition-colors">
              <ShieldCheck size={20} />
            </div>
            <ArrowRight size={16} className="text-muted group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-fg">Evidence Review</h4>
            <p className="text-xs text-muted mt-0.5">Audit verified detections, coordinates & Role 3 reasons</p>
          </div>
        </Link>

        <Link
          to="/metrics"
          className="group flex flex-col justify-between p-4 rounded-xl border border-line bg-surface/50 hover:bg-surface hover:border-purple-500/50 transition-all shadow"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-400 group-hover:bg-purple-400 group-hover:text-ink transition-colors">
              <BarChart3 size={20} />
            </div>
            <ArrowRight size={16} className="text-muted group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-fg">Metrics Suite</h4>
            <p className="text-xs text-muted mt-0.5">Model development benchmarks, AP50 & latency profiles</p>
          </div>
        </Link>

        <Link
          to="/reports"
          className="group flex flex-col justify-between p-4 rounded-xl border border-line bg-surface/50 hover:bg-surface hover:border-amber/50 transition-all shadow"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2.5 rounded-lg bg-amber/10 text-amber group-hover:bg-amber group-hover:text-ink transition-colors">
              <FileText size={20} />
            </div>
            <ArrowRight size={16} className="text-muted group-hover:text-amber group-hover:translate-x-1 transition-all" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-fg">Exports & Reports</h4>
            <p className="text-xs text-muted mt-0.5">Download MoES survey PDF, GeoJSON, CSV & S-100 packets</p>
          </div>
        </Link>
      </div>
    </div>
  );
}