import { useParams, Link } from "react-router";
import { MOCK_DETECTIONS } from "./mockdetection";
import { buildMockEvidence } from "../utils/mockEvidence";
import { evaluateRisk } from "../utils/firewall";
import EvidenceOverlay from "../components/Evidence/EvidenceOverlay";
import ExplainableTrace from "../components/Evidence/EvidenceTrace";
import RiskBadge from "../components/RiskBadge";

// TODO: once evidence_overlay.py / tracer.py expose real output, fetch by
// detection id instead of reading from the static mock array, e.g.
// GET /api/detections/:id/evidence — keep buildMockEvidence()'s return
// shape as the contract so EvidenceOverlay/ExplainableTrace don't change.

export default function EvidenceReview() {
  const { detectionId } = useParams();
  const detection = MOCK_DETECTIONS.find((d) => d.id === detectionId);

  if (!detection) {
    return (
      <div className="max-w-2xl">
        <Link to="/" className="text-sm text-teal underline decoration-teal/40 underline-offset-2">
          ← Back to Analyze
        </Link>
        <div className="mt-6 border border-line bg-surface px-5 py-6 text-sm text-muted">
          No detection found for id "{detectionId}".
        </div>
      </div>
    );
  }

  const evidence = buildMockEvidence(detection);
  // Reviewed outside live mission context, so telemetry is assumed nominal
  // (battery 80%, comms nominal) rather than pulled from a real feed.
  const risk = evaluateRisk({ confidence: detection.confidence, battery: 80, commsDegraded: false });

  return (
    <div className="max-w-4xl">
      <Link to="/" className="text-sm text-teal underline decoration-teal/40 underline-offset-2">
        ← Back to Analyze
      </Link>

      <div className="mt-4 border border-amber/40 bg-amber/10 px-4 py-2.5 text-xs text-amber">
        Simulated evidence — this view is not yet connected to the real sensor pipeline. Do not use for
        reporting or audit purposes until wired to evidence_overlay.py / tracer.py.
      </div>

      <div className="mt-6 flex items-start justify-between">
        <div>
          <div className="font-mono text-xs text-muted">{detection.id}</div>
          <h1 className="mt-1 text-xl text-fg">{detection.objectClass}</h1>
          <div className="mt-1 font-mono text-xs text-muted">
            {detection.lat.toFixed(4)}, {detection.lng.toFixed(4)} — {new Date(detection.timestamp).toLocaleString()}
          </div>
        </div>
        <RiskBadge level={risk.level} />
      </div>

      <div className="mt-8">
        <div className="mb-2 text-xs uppercase tracking-wide text-muted">Evidence composite</div>
        <EvidenceOverlay detection={detection} evidence={evidence} />
      </div>

      <div className="mt-8">
        <ExplainableTrace detection={detection} evidence={evidence} risk={risk} />
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={() => window.print()}
          className="border border-line px-4 py-2 text-xs text-muted hover:border-teal/60 hover:text-teal"
        >
          Print evidence packet
        </button>
      </div>
    </div>
  );
}
