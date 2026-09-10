import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import { getDetectionById, getCurrentDetections } from "./marineguard";

export default function EvidenceReview() {
  const { detectionId } = useParams();
  const [detection, setDetection] = useState(null);
  const [currentResult, setCurrentResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCurrentDetections().then((data) => {
      setCurrentResult(data);
      if (data && data.detections) {
        const found = data.detections.find((d) => d.id === detectionId) || data.detections[0];
        setDetection(found);
      }
      setLoading(false);
    });
  }, [detectionId]);

  if (loading) {
    return <div className="max-w-4xl p-6 text-sm text-muted">Loading real evidence trace…</div>;
  }

  if (!detection) {
    return (
      <div className="max-w-2xl">
        <Link to="/" className="text-sm text-teal underline decoration-teal/40 underline-offset-2">
          ← Back to Analyze
        </Link>
        <div className="mt-6 border border-line bg-surface px-5 py-6 text-sm text-muted">
          No detection found for id "{detectionId}". Run SSS detection on Analyze page first.
        </div>
      </div>
    );
  }

  const isAccepted = detection.status === "accepted";

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/" className="text-sm text-teal underline decoration-teal/40 underline-offset-2">
        ← Back to Analyze
      </Link>

      <div className="mt-6 flex items-start justify-between border-b border-line pb-4">
        <div>
          <div className="font-mono text-xs text-muted">{detection.id}</div>
          <h1 className="mt-1 text-2xl font-bold text-fg">{detection.objectClass}</h1>
          <div className="mt-1 font-mono text-xs text-muted">
            Coordinates: {detection.lat && detection.lng ? `${detection.lat.toFixed(4)}, ${detection.lng.toFixed(4)}` : "Unavailable from recorded SSS data"}
          </div>
        </div>

        <span className={`px-3 py-1.5 rounded text-xs font-mono font-bold ${
          isAccepted ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/40" : "bg-rose-500/15 text-rose-400 border border-rose-500/40"
        }`}>
          {detection.status.toUpperCase()}
        </span>
      </div>

      {/* Real Visual Evidence Container */}
      <div className="mt-8 border border-line bg-surface p-6 rounded-lg">
        <h2 className="text-sm font-bold uppercase tracking-wide text-muted font-mono mb-4">
          Real Side-Scan Sonar Visual Evidence
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="text-xs font-mono text-muted mb-2">Original SSS Image</div>
            {currentResult?.originalImageUrl ? (
              <img
                src={currentResult.originalImageUrl}
                alt="Original SSS"
                className="w-full h-auto rounded border border-line bg-black object-contain max-h-80"
              />
            ) : (
              <div className="h-48 border border-line bg-surface2 flex items-center justify-center text-xs text-muted">
                Original image unavailable
              </div>
            )}
          </div>

          <div>
            <div className="text-xs font-mono text-muted mb-2">YOLOv8n Neural Detection Overlay</div>
            {currentResult?.annotatedImageUrl ? (
              <img
                src={currentResult.annotatedImageUrl}
                alt="Annotated SSS"
                className="w-full h-auto rounded border border-line bg-black object-contain max-h-80"
              />
            ) : (
              <div className="h-48 border border-line bg-surface2 flex items-center justify-center text-xs text-muted">
                Annotated overlay unavailable
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Real Evidence Audit Trace */}
      <div className="mt-8 border border-line bg-surface p-6 rounded-lg space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wide text-muted font-mono">
          Explainable Neural Detection Trace
        </h2>

        <div className="p-4 bg-surface2 rounded-md border border-line space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-muted font-mono">STAGE: SSS_YOLO_INFERENCE</span>
            <span className="text-teal font-mono">CONF: {detection.confidencePct || `${(detection.confidence * 100).toFixed(1)}%`}</span>
          </div>
          <p className="text-sm text-fg">
            <b>Inference Output:</b> Detected class <code>{detection.rawClass}</code> (mapped to <code>{detection.species}</code>) at bounding box <code>{detection.bboxCoords}</code>.
          </p>
          <p className="text-xs text-muted">
            <b>Role 3 Gating Verdict:</b> {detection.rejectionReason}
          </p>
        </div>

        <div className="p-4 bg-surface2 rounded-md border border-line space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-muted font-mono">STAGE: METADATA_VERIFICATION</span>
            <span className="text-muted font-mono">GEODETIC INTEGRITY</span>
          </div>
          <p className="text-sm text-fg">
            <b>Coordinates:</b> {detection.lat && detection.lng ? `${detection.lat.toFixed(4)}, ${detection.lng.toFixed(4)}` : "Unavailable from recorded SSS data (No GPS fabrication)"}
          </p>
          <p className="text-xs text-muted">
            <b>Depth:</b> {detection.depthM ? `${detection.depthM} m` : "Unavailable from recorded SSS data"}
          </p>
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={() => window.print()}
          className="border border-line px-4 py-2 text-xs text-muted hover:border-teal/60 hover:text-teal rounded"
        >
          Print Evidence Packet
        </button>
      </div>
    </div>
  );
}
