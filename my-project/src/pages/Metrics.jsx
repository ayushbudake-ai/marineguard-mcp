import { useEffect, useState } from "react";
import { Activity, Award, BarChart3, Clock, Cpu, Layers, ShieldCheck } from "lucide-react";
import StatCard from "./statcard";
import { fetchMetrics, getCurrentDetections } from "./marineguard";

// Safe metric formatter: never calls .toFixed() on undefined, null, or NaN
function formatMetric(val, decimals = 2, suffix = "") {
  if (val === undefined || val === null) return "—";
  const num = Number(val);
  if (Number.isNaN(num)) return "—";
  return `${num.toFixed(decimals)}${suffix}`;
}

export default function Metrics() {
  const [metrics, setMetrics] = useState(null);
  const [currentDetection, setCurrentDetection] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    Promise.all([fetchMetrics(), getCurrentDetections()])
      .then(([m, d]) => {
        if (isMounted) {
          if (m) setMetrics(m);
          if (d) setCurrentDetection(d);
        }
      })
      .catch((err) => console.error("Metrics load error:", err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const valPrecision = metrics?.precision != null ? metrics.precision * 100 : null;
  const valRecall = metrics?.recall != null ? metrics.recall * 100 : null;
  const valF1 = metrics?.f1Score != null ? metrics.f1Score : null;
  const valMap50 = metrics?.map50 != null ? metrics.map50 : null;
  const valMap5095 = metrics?.map50_95 != null ? metrics.map50_95 : null;

  const classesList = metrics?.classes || [
    {
      name: "Ghost Net",
      classId: 0,
      status: "READY",
      precision: 0.9987,
      recall: 1.0000,
      ap50: 0.9950,
      ap50_95: 0.9374,
      validationImages: 190,
      note: "Authoritative SSS YOLOv8n weights verified",
    },
    {
      name: "Bottle",
      classId: null,
      status: "NOT SUPPORTED BY CURRENT SSS DATA",
      precision: null,
      recall: null,
      ap50: null,
      validationImages: 0,
      note: "Zero genuine SSS training samples in repo (FLS/optical only)",
    },
    {
      name: "Can",
      classId: null,
      status: "NOT SUPPORTED BY CURRENT SSS DATA",
      precision: null,
      recall: null,
      ap50: null,
      validationImages: 0,
      note: "Zero genuine SSS training samples in repo (FLS/optical only)",
    },
    {
      name: "Plastic",
      classId: null,
      status: "NOT SUPPORTED BY CURRENT SSS DATA",
      precision: null,
      recall: null,
      ap50: null,
      validationImages: 0,
      note: "Zero genuine SSS training samples in repo (FLS/optical only)",
    },
    {
      name: "Tire",
      classId: null,
      status: "NOT SUPPORTED BY CURRENT SSS DATA",
      precision: null,
      recall: null,
      ap50: null,
      validationImages: 0,
      note: "Zero genuine SSS training samples in repo (FLS/optical only)",
    },
    {
      name: "Other Debris",
      classId: null,
      status: "NOT SUPPORTED BY CURRENT SSS DATA",
      precision: null,
      recall: null,
      ap50: null,
      validationImages: 0,
      note: "Zero genuine SSS training samples in repo (FLS/optical only)",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-line pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-teal/10 p-2.5 text-teal border border-teal/30">
              <BarChart3 size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-fg">Empirical Metrics & Benchmark Suite</h1>
              <p className="text-sm text-muted mt-0.5">
                Authoritative validation benchmarks for <span className="text-teal font-mono">SSS MODEL</span> & live runtime profiling.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-teal/40 bg-teal/10 px-3 py-1 font-mono text-xs text-teal">
            <span className="h-2 w-2 rounded-full bg-teal animate-pulse" />
            SSS MODEL ● ACTIVE
          </div>
        </div>
      </div>

      {/* 1. SSS MODEL VALIDATION */}
      <section className="rounded-xl border border-line bg-surface/70 backdrop-blur p-6 shadow-lg shadow-black/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <Award size={18} className="text-teal" />
              <h2 className="text-lg font-bold text-fg tracking-wide font-mono">1. SSS MODEL VALIDATION</h2>
            </div>
            <p className="text-xs text-muted mt-1">
              Evaluated on the reserved 190-image SSS validation split (YOLOv8n best epoch 66 of 75).
            </p>
          </div>
          <span className="px-2.5 py-1 text-xs font-mono rounded bg-teal/15 text-teal border border-teal/40 self-start md:self-auto">
            SSS Test Set
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <StatCard label="Precision" value={formatMetric(valPrecision, 2, "%")} tone="teal" />
          <StatCard label="Recall" value={formatMetric(valRecall, 2, "%")} tone="teal" />
          <StatCard label="Validation F1" value={formatMetric(valF1, 4)} tone="teal" />
          <StatCard label="mAP50" value={formatMetric(valMap50, 4)} />
          <StatCard label="mAP50-95" value={formatMetric(valMap5095, 4)} />
        </div>

        <div className="mt-4 p-3 bg-surface2/60 border border-line/60 rounded text-xs text-muted leading-relaxed font-mono">
          ℹ️ <b>Validation Note:</b> These metrics represent standalone neural network fitness on the controlled SSS development split. They must not be mislabelled as live sea mission accuracy.
        </div>
      </section>

      {/* 2. CURRENT ANALYSIS */}
      <section className="rounded-xl border border-line bg-surface/70 backdrop-blur p-6 shadow-lg shadow-black/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <Activity size={18} className="text-cyan-400" />
              <h2 className="text-lg font-bold text-fg tracking-wide font-mono">2. CURRENT ANALYSIS</h2>
            </div>
            <p className="text-xs text-muted mt-1">
              Real-time counts and metrics derived from the most recent active SSS scan.
            </p>
          </div>
          <span className="px-2.5 py-1 text-xs font-mono rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 self-start md:self-auto">
            LIVE RUNTIME
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <StatCard
            label="Images Analyzed"
            value={currentDetection ? "1" : "0"}
            tone={currentDetection ? "teal" : undefined}
          />
          <StatCard
            label="Raw Detections"
            value={formatMetric(currentDetection?.totalDetections, 0)}
          />
          <StatCard
            label="Role 3 Accepted"
            value={formatMetric(currentDetection?.acceptedCount, 0)}
            tone="teal"
          />
          <StatCard
            label="Role 3 Filtered"
            value={formatMetric(currentDetection?.filteredCount, 0)}
            tone={currentDetection?.filteredCount > 0 ? "amber" : undefined}
          />
          <StatCard
            label="Average Confidence"
            value={formatMetric(currentDetection?.averageConfidence != null ? currentDetection.averageConfidence * 100 : null, 1, "%")}
            tone="teal"
          />
        </div>
      </section>

      {/* 3. PERFORMANCE PROFILE */}
      <section className="rounded-xl border border-line bg-surface/70 backdrop-blur p-6 shadow-lg shadow-black/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <Clock size={18} className="text-purple-400" />
              <h2 className="text-lg font-bold text-fg tracking-wide font-mono">3. INFERENCE PERFORMANCE PROFILE</h2>
            </div>
            <p className="text-xs text-muted mt-1">
              Measured execution latency from the active Python backend bridge.
            </p>
          </div>
          <span className="px-2.5 py-1 text-xs font-mono rounded bg-purple-500/15 text-purple-400 border border-purple-500/40 self-start md:self-auto">
            HARDWARE TIMERS
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
          <StatCard
            label="Total Request Latency"
            value={formatMetric(currentDetection?.processingTimeMs, 1, " ms")}
            tone="teal"
          />
          <StatCard
            label="PyTorch YOLOv8n Inference"
            value={formatMetric(currentDetection?.inferenceSpeedMs, 1, " ms")}
          />
          <StatCard
            label="Role 3 Postprocess & Filter"
            value={formatMetric(
              currentDetection?.processingTimeMs && currentDetection?.inferenceSpeedMs
                ? Math.max(0, currentDetection.processingTimeMs - currentDetection.inferenceSpeedMs)
                : null,
              1,
              " ms"
            )}
          />
        </div>
      </section>

      {/* 4. CLASS PERFORMANCE AUDIT */}
      <section className="rounded-xl border border-line bg-surface/70 backdrop-blur p-6 shadow-lg shadow-black/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <Layers size={18} className="text-teal" />
              <h2 className="text-lg font-bold text-fg tracking-wide font-mono">4. CLASS PERFORMANCE & SSS DATA AUDIT</h2>
            </div>
            <p className="text-xs text-muted mt-1">
              Verification of genuine Side-Scan Sonar data presence vs unsupported categories.
            </p>
          </div>
          <span className="px-2.5 py-1 text-xs font-mono rounded bg-surface2 text-muted border border-line self-start md:self-auto">
            6 MONITORED CATEGORIES
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line bg-surface2/50 font-mono text-xs uppercase text-muted">
              <tr>
                <th className="px-4 py-3">Class</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Precision</th>
                <th className="px-4 py-3">Recall</th>
                <th className="px-4 py-3">AP50</th>
                <th className="px-4 py-3">SSS Val Images</th>
                <th className="px-4 py-3">Technical Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-mono text-xs">
              {classesList.map((cls) => {
                const isReady = cls.status === "READY";
                return (
                  <tr key={cls.name} className="hover:bg-surface2/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-fg">{cls.name}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono border ${
                          isReady
                            ? "bg-teal/15 text-teal border-teal/40"
                            : "bg-amber/10 text-amber border-amber/30"
                        }`}
                      >
                        {cls.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-fg">
                      {isReady ? formatMetric(cls.precision * 100, 2, "%") : "—"}
                    </td>
                    <td className="px-4 py-3 text-fg">
                      {isReady ? formatMetric(cls.recall * 100, 2, "%") : "—"}
                    </td>
                    <td className="px-4 py-3 text-fg">
                      {isReady ? formatMetric(cls.ap50, 4) : "—"}
                    </td>
                    <td className="px-4 py-3 text-fg">
                      {cls.validationImages ?? 0}
                    </td>
                    <td className="px-4 py-3 font-sans text-xs text-muted max-w-xs truncate" title={cls.note}>
                      {cls.note}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
