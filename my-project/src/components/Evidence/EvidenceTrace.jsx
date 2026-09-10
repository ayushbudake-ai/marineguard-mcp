import { useState } from "react";
import RiskBadge from "../RiskBadge";

export default function ExplainableTrace({ detection, evidence, risk }) {
  const [showRaw, setShowRaw] = useState(false);
  const { traceSteps } = evidence;

  const rawTrace = {
    detection_id: detection.id,
    timestamp: detection.timestamp,
    steps: traceSteps.map((s) => ({
      module: s.title,
      detail: s.detail,
      confidence: Number(s.confidence.toFixed(3)),
    })),
    fused_confidence: detection.confidence,
    risk_level: risk.level,
    firewall_action: risk.action,
  };

  return (
    <div className="border border-line bg-surface">
      <div className="border-b border-line px-4 py-3">
        <div className="text-sm text-fg">Explainable trace</div>
        <div className="text-xs text-muted">Step-by-step reasoning from sensor detection to fused verdict</div>
      </div>

      <ol className="divide-y divide-line/60">
        {traceSteps.map((step, i) => (
          <li key={step.title} className="px-4 py-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-xs text-muted">Step {i + 1}</div>
                <div className="mt-0.5 text-sm text-fg">{step.title}</div>
                <div className="mt-0.5 font-mono text-xs text-muted">{step.detail}</div>
              </div>
              <div className="w-20 shrink-0 text-right font-mono text-sm text-teal">
                {step.confidence.toFixed(2)}
              </div>
            </div>
            <div className="mt-2 h-1 w-full bg-line">
              <div className="h-1 bg-teal" style={{ width: `${step.confidence * 100}%` }} />
            </div>
          </li>
        ))}
      </ol>

      <div className="flex items-center justify-between border-t border-line bg-surface2 px-4 py-3">
        <div>
          <div className="text-xs text-muted">Fused confidence</div>
          <div className="font-mono text-lg text-fg">{detection.confidence.toFixed(2)}</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted">Firewall verdict</div>
          <div className="mt-1 flex items-center gap-2">
            <RiskBadge level={risk.level} size="sm" />
            <span className="text-sm text-fg">{risk.action}</span>
          </div>
        </div>
      </div>

      <div className="border-t border-line px-4 py-3">
        <button
          onClick={() => setShowRaw((v) => !v)}
          className="text-xs text-teal underline decoration-teal/40 underline-offset-2 hover:decoration-teal"
        >
          {showRaw ? "Hide raw trace JSON" : "View raw trace JSON"}
        </button>
        {showRaw && (
          <pre className="mt-3 overflow-x-auto bg-ink px-3 py-3 font-mono text-xs text-muted">
            {JSON.stringify(rawTrace, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
