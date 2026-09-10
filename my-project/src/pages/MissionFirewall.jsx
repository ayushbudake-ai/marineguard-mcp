import { useEffect, useRef, useState } from "react";
import RiskBadge from "../components/RiskBadge";
import FirewallTaxonomyTable from "../components/FirewallTaxonomyTables";
import FirewallEventFeed from "../components/FirewallEventFeed";
import StatCard from "./statcard.jsx";
import { MOCK_DETECTIONS } from "./mockdetection";
import { evaluateRisk } from "../utils/firewall";

// TODO: once marineguard/firewall/operator_ui.py has a real interface,
// replace the interval-driven simulation below with a subscription to the
// actual firewall event stream (e.g. a websocket from the MCP tool server).
// evaluateRisk() in src/utils/firewall.js can stay as-is either way — it's
// the same policy the backend enforces, just re-expressed for the UI.

let eventCounter = 0;

export default function MissionFirewall() {
  const [battery, setBattery] = useState(84);
  const [commsDegraded, setCommsDegraded] = useState(false);
  const [live, setLive] = useState(true);
  const [events, setEvents] = useState([]);
  const cursorRef = useRef(0);

  useEffect(() => {
    if (!live) return;
    const interval = setInterval(() => {
      const detection = MOCK_DETECTIONS[cursorRef.current % MOCK_DETECTIONS.length];
      cursorRef.current += 1;

      const currentBattery = Math.max(5, battery - Math.floor(Math.random() * 2));
      const { level, action } = evaluateRisk({
        confidence: detection.confidence,
        battery: currentBattery,
        commsDegraded,
      });

      eventCounter += 1;
      const event = {
        id: `evt-${eventCounter}`,
        sourceId: detection.id,
        level,
        action,
        detail: `conf=${detection.confidence.toFixed(2)} battery=${currentBattery}% comms=${commsDegraded ? "degraded" : "nominal"}`,
        timestamp: new Date().toISOString(),
      };

      setBattery(currentBattery);
      setEvents((prev) => [event, ...prev].slice(0, 30));
    }, 4000);

    return () => clearInterval(interval);
  }, [live, battery, commsDegraded]);

  const currentLevel = events[0]?.level ?? "LOW";

  return (
    <div className="max-w-4xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl text-fg">Mission Firewall</h1>
          <p className="mt-1 text-sm text-muted">
            Formal risk taxonomy enforcement before any vehicle action is executed.
          </p>
        </div>
        <RiskBadge level={currentLevel} />
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Battery" value={battery} unit="%" tone={battery < 20 ? "coral" : "default"} />
        <StatCard label="Comms" value={commsDegraded ? "Degraded" : "Nominal"} tone={commsDegraded ? "coral" : "teal"} />
        <StatCard label="Current state" value={currentLevel} tone={currentLevel === "LOW" ? "teal" : currentLevel === "MEDIUM" ? "amber" : "coral"} />
        <StatCard label="Events logged" value={events.length} />
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3 border border-line bg-surface px-4 py-3">
        <span className="text-xs uppercase tracking-wide text-muted">Simulation controls</span>
        <button
          onClick={() => setLive((v) => !v)}
          className="border border-line px-3 py-1.5 text-xs text-fg hover:border-teal/60 hover:text-teal"
        >
          {live ? "Pause" : "Resume"} live feed
        </button>
        <button
          onClick={() => setCommsDegraded((v) => !v)}
          className={`border px-3 py-1.5 text-xs ${
            commsDegraded ? "border-coral/60 text-coral" : "border-line text-fg hover:border-coral/40 hover:text-coral"
          }`}
        >
          {commsDegraded ? "Restore comms" : "Simulate degraded comms"}
        </button>
        <span className="text-xs text-muted">Drives the CRITICAL / emergency-ascent path for demo purposes.</span>
      </div>

      <div className="mt-10">
        <div className="mb-2 text-xs uppercase tracking-wide text-muted">Risk taxonomy</div>
        <FirewallTaxonomyTable activeLevel={currentLevel} />
      </div>

      <div className="mt-10">
        <div className="mb-2 text-xs uppercase tracking-wide text-muted">Event feed</div>
        <FirewallEventFeed events={events} />
      </div>
    </div>
  );
}
