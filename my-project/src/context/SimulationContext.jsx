import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";

const DEBRIS_TYPES = [
  "Fishing Net Fragment", "Plastic Container", "Metal Drum", "Rope Bundle",
  "Unknown Object", "Anchor Chain", "Trawl Door", "Derelict Trap"
];
const SENSORS = ["SSS+Optical", "SSS+Bathy", "SAS+Optical", "SSS+SAS+Optical"];

const SimulationContext = createContext(null);

export function SimulationProvider({ children }) {
  const [telemetry, setTelemetry] = useState({
    depth: 48.2, battery: 74, speed: 1.4, heading: 247, altitude: 12.3,
    lat: 12.3, lon: 74.5, ping: 0,
  });
  const [missionSecs, setMissionSecs] = useState(0);
  const [detections, setDetections] = useState([]);
  const [riskCounts, setRiskCounts] = useState({ LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 });
  const [logEntries, setLogEntries] = useState([]);
  const [trackPoints, setTrackPoints] = useState([]);
  const [clock, setClock] = useState("");
  const [fwStatus, setFwStatus] = useState("ACTIVE");
  const [fwLastEvent, setFwLastEvent] = useState("No events yet");
  const [activeRisk, setActiveRisk] = useState(null);

  const detCountRef = useRef(0);
  const telRef = useRef(telemetry);
  telRef.current = telemetry;

  // Add log entry
  const addLog = useCallback((tag, msg) => {
    const now = new Date().toTimeString().slice(0, 8);
    setLogEntries(prev => {
      const next = [...prev, { time: now, tag, msg }];
      return next.length > 60 ? next.slice(-60) : next;
    });
  }, []);

  // Generate detection
  const generateDetection = useCallback(() => {
    const t = telRef.current;
    const conf = 0.45 + Math.random() * 0.52;
    const risk = conf > 0.88 ? "CRITICAL" : conf > 0.72 ? "HIGH" : conf > 0.52 ? "MEDIUM" : "LOW";
    const type = DEBRIS_TYPES[Math.floor(Math.random() * DEBRIS_TYPES.length)];
    const sensor = SENSORS[Math.floor(Math.random() * SENSORS.length)];
    detCountRef.current++;

    const det = {
      id: `TGT-${String(detCountRef.current).padStart(3, "0")}`,
      type, conf, risk, sensor,
      lat: t.lat.toFixed(4), lon: t.lon.toFixed(4),
      depth: t.depth.toFixed(1),
      time: new Date().toTimeString().slice(0, 8),
      trackPt: { x: t.lon, y: t.lat },
      sensorConfs: {
        "Side-Scan": (conf * 0.85 + Math.random() * 0.15).toFixed(2),
        "Optical": (conf * 0.78 + Math.random() * 0.15).toFixed(2),
        "Bathymetry": (conf * 0.60 + Math.random() * 0.15).toFixed(2),
      },
    };

    setDetections(prev => [...prev, det]);
    setRiskCounts(prev => ({ ...prev, [risk]: prev[risk] + 1 }));
    setActiveRisk(risk);

    addLog(
      risk === "CRITICAL" || risk === "HIGH" ? "ALERT" : risk === "MEDIUM" ? "WARN" : "OK",
      `${det.id} detected — ${type} | conf=${(conf * 100).toFixed(0)}% | ${risk}`
    );

    if (risk === "CRITICAL") {
      addLog("ALERT", "⚠ FIREWALL: CRITICAL — Emergency ascent protocol activated!");
      setFwStatus("⚠ TRIGGERED");
      setTimeout(() => setFwStatus("ACTIVE"), 4000);
    }
    setFwLastEvent(`Last: ${det.id} → ${risk} at ${det.time}`);

    return det;
  }, [addLog]);

  // Clock
  useEffect(() => {
    const interval = setInterval(() => {
      setClock(new Date().toTimeString().slice(0, 8) + " IST");
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Mission timer
  useEffect(() => {
    const interval = setInterval(() => {
      setMissionSecs(prev => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Telemetry simulation (500ms)
  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetry(prev => {
        let depth = prev.depth + (Math.random() - 0.5) * 0.8;
        depth = Math.max(30, Math.min(80, depth));
        let battery = prev.battery - 0.004;
        let speed = prev.speed + (Math.random() - 0.5) * 0.05;
        speed = Math.max(0.8, Math.min(2.2, speed));
        let heading = prev.heading + (Math.random() - 0.5) * 1.5;
        heading = ((heading % 360) + 360) % 360;
        let altitude = prev.altitude + (Math.random() - 0.5) * 0.3;
        altitude = Math.max(8, Math.min(20, altitude));
        let lat = prev.lat + 0.00002 + (Math.random() - 0.5) * 0.000005;
        let lon = prev.lon + 0.000015 + (Math.random() - 0.5) * 0.000005;
        const ping = prev.ping + 1;
        return { depth, battery, speed, heading, altitude, lat, lon, ping };
      });
      setTrackPoints(prev => {
        const t = telRef.current;
        const next = [...prev, { x: t.lon, y: t.lat }];
        return next.length > 400 ? next.slice(-400) : next;
      });
    }, 500);
    return () => clearInterval(interval);
  }, []);

  // Detection scheduler
  useEffect(() => {
    let timeout;
    function schedule() {
      const delay = 8000 + Math.random() * 12000;
      timeout = setTimeout(() => { generateDetection(); schedule(); }, delay);
    }
    schedule();
    return () => clearTimeout(timeout);
  }, [generateDetection]);

  // Boot logs
  useEffect(() => {
    addLog("INFO", "MarineGuard MCP v1.0 — System online");
    addLog("INFO", "Platform: Sagar Netra (AUV-01) · Sector-7W · Arabian Sea");
    addLog("OK", "All 6 sensors initialized and streaming");
    addLog("OK", "MCP Tool Server: 9 tools compiled and registered");
    addLog("INFO", "Mission Firewall: ACTIVE — thresholds loaded");
    addLog("INFO", "Sonar waterfall streaming at 400 kHz / 150m swath");
  }, [addLog]);

  const missionTime = (() => {
    const h = String(Math.floor(missionSecs / 3600)).padStart(2, "0");
    const m = String(Math.floor((missionSecs % 3600) / 60)).padStart(2, "0");
    const s = String(missionSecs % 60).padStart(2, "0");
    return `${h}:${m}:${s}`;
  })();

  const value = {
    telemetry, missionSecs, missionTime, detections, riskCounts,
    logEntries, trackPoints, clock, fwStatus, fwLastEvent, activeRisk,
    addLog, generateDetection,
  };

  return (
    <SimulationContext.Provider value={value}>
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error("useSimulation must be used within SimulationProvider");
  return ctx;
}
