import { useEffect, useState } from "react";
import StatCard from "./statcard";
import { fetchMetrics } from "./marineguard";

export default function Metrics() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    fetchMetrics().then(setMetrics);
  }, []);

  return (
    <div className="max-w-4xl">
      <h1 className="text-xl text-fg">Metrics</h1>
      <p className="mt-1 text-sm text-muted">
        Evaluation stats from the detection pipeline, computed against labeled survey data.
      </p>

      {!metrics ? (
        <div className="mt-8 text-sm text-muted">Loading metrics…</div>
      ) : (
        <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="F1 score" value={typeof metrics.f1 === "number" ? metrics.f1.toFixed(2) : "Unavailable"} tone="teal" />
          <StatCard label="Precision" value={typeof metrics.precision === "number" ? metrics.precision.toFixed(2) : "Unavailable"} />
          <StatCard label="Recall" value={typeof metrics.recall === "number" ? metrics.recall.toFixed(2) : "Unavailable"} />
          <StatCard label="False positive rate" value={typeof metrics.falsePositiveRate === "number" ? metrics.falsePositiveRate.toFixed(2) : "Unavailable"} tone="amber" />
          <StatCard label="False negative rate" unavailable={metrics.falseNegativeRate == null} value={metrics.falseNegativeRate} />
          <StatCard label="Latency" value={metrics.latencyMs} unit="ms" />
          <StatCard label="Sample count" value={metrics.sampleCount} />
        </div>
      )}

      <p className="mt-6 text-xs text-muted">
        Metrics not yet computed by eval.py are labeled "not yet computed" rather than estimated — see the
        roadmap doc's note on not inventing evaluation numbers.
      </p>
    </div>
  );
}
