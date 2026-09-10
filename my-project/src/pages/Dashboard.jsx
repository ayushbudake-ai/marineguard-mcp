import React, { useEffect, useRef, useState, useCallback } from "react";
import { useSimulation } from "../context/SimulationContext";

/* ═══════════════════════════════════════════════════
   DASHBOARD — 3-column Mission Control grid
   Ports all demo.html dashboard features
═══════════════════════════════════════════════════ */

export default function Dashboard() {
  return (
    <div className="dashboard-grid">
      <div className="col-left">
        <TelemetryPanel />
        <FirewallPanel />
      </div>
      <div className="col-center">
        <SonarWaterfall />
        <TrackMap />
      </div>
      <div className="col-right">
        <DetectionFeed />
        <EvidenceOverlay />
        <SystemLog />
      </div>
    </div>
  );
}

/* ─────────── TELEMETRY PANEL ─────────── */
function TelemetryPanel() {
  const { telemetry, missionTime, detections } = useSimulation();
  const { depth, battery, speed, heading, altitude, lat, lon } = telemetry;

  const batColor = battery > 50 ? "var(--green)" : battery > 25 ? "var(--amber)" : "var(--red)";

  return (
    <div className="panel">
      <div className="panel-header">
        ⚙ AUV Telemetry
        <span style={{ color: "var(--teal)" }}>Sagar Netra</span>
      </div>
      <div className="panel-body">
        <div className="telem-grid">
          <GaugeBox value={depth.toFixed(1)} unit="metres" label="Depth" fill={depth / 100 * 100} />
          <GaugeBox value={Math.max(0, battery).toFixed(0)} unit="%" label="Battery" fill={battery} color={batColor} gradientOverride={`linear-gradient(90deg, ${batColor}, var(--teal))`} />
          <GaugeBox value={speed.toFixed(1)} unit="m/s" label="Speed" fill={speed / 2.5 * 100} />
          <GaugeBox value={Math.round(heading)} unit="°" label="Heading" fill={heading / 360 * 100} />
        </div>

        <div className="mission-status-list" style={{ marginTop: 10 }}>
          <MsItem k="Platform" v="Sagar Netra" vColor="var(--teal)" />
          <MsItem k="Survey Area" v="Sector-7W" />
          <MsItem k="Altitude" v={`${altitude.toFixed(1)} m`} />
          <MsItem k="Comms" v="ACOUSTIC ✓" vColor="var(--green)" />
          <MsItem k="Detections" v={String(detections.length)} vColor={detections.length > 5 ? "var(--red)" : "var(--amber)"} />
          <MsItem k="Mission Time" v={missionTime} vColor="var(--cyan)" />
        </div>
      </div>
    </div>
  );
}

function GaugeBox({ value, unit, label, fill, color, gradientOverride }) {
  return (
    <div className="gauge-box">
      <div className="gauge-val" style={color ? { color } : undefined}>{value}</div>
      <div className="gauge-unit">{unit}</div>
      <div className="gauge-label">{label}</div>
      <div className="gauge-bar">
        <div className="gauge-fill" style={{ width: `${Math.min(100, Math.max(0, fill))}%`, ...(gradientOverride ? { background: gradientOverride } : {}) }} />
      </div>
    </div>
  );
}

function MsItem({ k, v, vColor }) {
  return (
    <div className="ms-item">
      <span className="ms-key">{k}</span>
      <span className="ms-val" style={vColor ? { color: vColor } : undefined}>{v}</span>
    </div>
  );
}

/* ─────────── FIREWALL PANEL ─────────── */
function FirewallPanel() {
  const { riskCounts, fwStatus, fwLastEvent, activeRisk } = useSimulation();
  const risks = [
    { level: "LOW", label: "LOW — Continue Survey", glow: "rgba(74,222,128,.3)" },
    { level: "MEDIUM", label: "MEDIUM — Close Inspect", glow: "rgba(251,191,36,.3)" },
    { level: "HIGH", label: "HIGH — Alert Operator", glow: "rgba(248,113,113,.3)" },
    { level: "CRITICAL", label: "CRITICAL — Abort Mission", glow: "rgba(220,38,38,.5)" },
  ];

  return (
    <div className="panel">
      <div className="panel-header">
        🔥 Mission Firewall
        <span style={{ color: fwStatus === "ACTIVE" ? "var(--green)" : "var(--red)" }}>{fwStatus}</span>
      </div>
      <div className="panel-body">
        <div className="risk-levels">
          {risks.map(r => (
            <div
              key={r.level}
              className={`risk-row-item risk-${r.level}${activeRisk === r.level ? " active-risk" : ""}`}
              style={activeRisk === r.level ? { "--glow-color": r.glow } : undefined}
            >
              <div className={`risk-dot risk-dot-${r.level}`} />
              {r.label}
              <span className="risk-count">{riskCounts[r.level]}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 10, fontSize: ".72rem", color: "var(--muted)", textAlign: "center" }}>
          {fwLastEvent}
        </div>
      </div>
    </div>
  );
}

/* ─────────── SONAR WATERFALL (Canvas) ─────────── */
function SonarWaterfall() {
  const canvasRef = useRef(null);
  const { telemetry } = useSimulation();
  const linesRef = useRef([]);
  const pingRef = useRef(0);
  const animRef = useRef(null);

  const generateRow = useCallback((w) => {
    const row = new Uint8ClampedArray(w * 4);
    for (let x = 0; x < w; x++) {
      const center = w / 2;
      const dist = Math.abs(x - center) / center;
      let intensity = Math.random() * 40 + 10;
      if (dist > 0.85) intensity = 120 + Math.random() * 80;
      if (dist < 0.03) intensity = 5;
      if (Math.random() < 0.003) intensity = 200 + Math.random() * 55;
      const v = Math.floor(Math.min(255, intensity));
      row[x * 4] = Math.floor(v * 0.1);
      row[x * 4 + 1] = Math.floor(v * 0.7);
      row[x * 4 + 2] = Math.floor(v * 0.9);
      row[x * 4 + 3] = 255;
    }
    return row;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    function draw() {
      const wrap = canvas.parentElement;
      const w = wrap.clientWidth;
      const h = wrap.clientHeight;
      if (w === 0 || h === 0) { animRef.current = requestAnimationFrame(draw); return; }
      canvas.width = w;
      canvas.height = h;
      pingRef.current++;

      const row = generateRow(w);
      linesRef.current.push(row);
      if (linesRef.current.length > h) linesRef.current.shift();

      const imgData = ctx.createImageData(w, h);
      const startIdx = Math.max(0, linesRef.current.length - h);
      for (let y = 0; y < h; y++) {
        const rowIdx = startIdx + y;
        if (rowIdx < linesRef.current.length) {
          const srcRow = linesRef.current[rowIdx];
          const srcW = srcRow.length / 4;
          for (let x = 0; x < w; x++) {
            const di = (y * w + x) * 4;
            const sx = Math.min(Math.floor(x * srcW / w), srcW - 1);
            const si = sx * 4;
            imgData.data[di] = srcRow[si];
            imgData.data[di + 1] = srcRow[si + 1];
            imgData.data[di + 2] = srcRow[si + 2];
            imgData.data[di + 3] = 255;
          }
        }
      }
      ctx.putImageData(imgData, 0, 0);

      // Scan line
      ctx.fillStyle = "rgba(56,189,248,0.4)";
      ctx.fillRect(0, h - 2, w, 2);

      // Center nadir
      ctx.strokeStyle = "rgba(56,189,248,0.15)";
      ctx.beginPath(); ctx.moveTo(w / 2, 0); ctx.lineTo(w / 2, h); ctx.stroke();

      animRef.current = requestAnimationFrame(draw);
    }
    animRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animRef.current);
  }, [generateRow]);

  return (
    <div className="panel" style={{ flex: 2 }}>
      <div className="panel-header">
        🔊 Side-Scan Sonar Waterfall — 400 kHz
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: ".68rem", color: "var(--muted)" }}>Swath: 150m</span>
          <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--green)", animation: "blink 1s infinite" }} />
        </div>
      </div>
      <div className="sonar-wrap" style={{ flex: 1, minHeight: 260 }}>
        <canvas ref={canvasRef} />
        <div className="sonar-info">
          <div className="si-row"><span className="si-key">Range</span><span className="si-val">75 m</span></div>
          <div className="si-row"><span className="si-key">Freq</span><span className="si-val">400 kHz</span></div>
          <div className="si-row"><span className="si-key">Ping#</span><span className="si-val">{pingRef.current}</span></div>
          <div className="si-row"><span className="si-key">Pos</span><span className="si-val">{telemetry.lat.toFixed(4)}N {telemetry.lon.toFixed(4)}E</span></div>
        </div>
      </div>
    </div>
  );
}

/* ─────────── TRACK MAP (Canvas) ─────────── */
function TrackMap() {
  const canvasRef = useRef(null);
  const { trackPoints, detections, telemetry } = useSimulation();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const wrap = canvas.parentElement;
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext("2d");
    const pts = trackPoints;

    // Background grid
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(56,189,248,0.05)";
    for (let i = 0; i < w; i += 30) { ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, h); ctx.stroke(); }
    for (let i = 0; i < h; i += 30) { ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(w, i); ctx.stroke(); }

    if (pts.length < 2) return;

    const minX = Math.min(...pts.map(p => p.x)), maxX = Math.max(...pts.map(p => p.x));
    const minY = Math.min(...pts.map(p => p.y)), maxY = Math.max(...pts.map(p => p.y));
    const rx = maxX - minX || 0.001, ry = maxY - minY || 0.001;
    const pad = 20;
    const toX = p => pad + (p.x - minX) / rx * (w - pad * 2);
    const toY = p => h - pad - (p.y - minY) / ry * (h - pad * 2);

    // Track gradient
    for (let i = 1; i < pts.length; i++) {
      const t = i / pts.length;
      ctx.strokeStyle = `rgba(${Math.floor(56 + t * 100)},${Math.floor(189 - t * 50)},248,${0.3 + t * 0.6})`;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(toX(pts[i - 1]), toY(pts[i - 1]));
      ctx.lineTo(toX(pts[i]), toY(pts[i]));
      ctx.stroke();
    }

    // Detection dots
    detections.forEach(d => {
      if (!d.trackPt) return;
      const col = d.risk === "CRITICAL" ? "#dc2626" : d.risk === "HIGH" ? "#f87171" : d.risk === "MEDIUM" ? "#fbbf24" : "#4ade80";
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.arc(toX(d.trackPt), toY(d.trackPt), 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // AUV position
    const last = pts[pts.length - 1];
    ctx.fillStyle = "#38bdf8";
    ctx.beginPath(); ctx.arc(toX(last), toY(last), 6, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = "rgba(56,189,248,0.4)";
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(toX(last), toY(last), 10, 0, Math.PI * 2); ctx.stroke();

    // Legend
    ctx.fillStyle = "rgba(56,189,248,.8)"; ctx.font = "10px monospace";
    ctx.fillText(`Track: ${pts.length} pts`, 6, 14);
    ctx.fillStyle = "rgba(148,163,184,.6)";
    ctx.fillText(`${telemetry.lat.toFixed(4)}N ${telemetry.lon.toFixed(4)}E`, 6, h - 6);
  }, [trackPoints, detections, telemetry]);

  return (
    <div className="panel" style={{ flex: "0 0 auto" }}>
      <div className="panel-header">
        🗺 Mission Track Plot
        <span style={{ color: "var(--muted)", fontSize: ".68rem" }}>Sector-7W · Arabian Sea</span>
      </div>
      <div className="map-wrap"><canvas ref={canvasRef} /></div>
    </div>
  );
}

/* ─────────── DETECTION FEED ─────────── */
function DetectionFeed() {
  const { detections } = useSimulation();
  const recent = detections.slice(-8).reverse();

  return (
    <div className="panel" style={{ flex: "0 0 auto" }}>
      <div className="panel-header">
        🎯 Detection Feed
        <span style={{ color: "var(--green)", fontSize: ".68rem" }}>● LIVE</span>
      </div>
      <div className="panel-body" style={{ padding: 8 }}>
        <div className="det-feed">
          {recent.length === 0 ? (
            <div className="empty-state">Scanning… No targets yet</div>
          ) : recent.map(d => <DetCard key={d.id} d={d} />)}
        </div>
      </div>
    </div>
  );
}

function DetCard({ d }) {
  const confClass = d.conf > 0.75 ? "conf-high" : d.conf > 0.5 ? "conf-med" : "conf-low";
  return (
    <div className="det-card new-det">
      <div className="det-top">
        <span className="det-id">{d.id}</span>
        <span className="det-time">{d.time}</span>
      </div>
      <div className="det-type">{d.type}</div>
      <div className="det-sensor">Sensors: {d.sensor}</div>
      <div className="conf-bar">
        <div className={`conf-fill ${confClass}`} style={{ width: `${(d.conf * 100).toFixed(0)}%` }} />
      </div>
      <div className="det-footer">
        <span className={`risk-badge rb-${d.risk}`}>{d.risk}</span>
        <span className="det-coords">{(d.conf * 100 | 0)}% · {d.lat}N {d.lon}E</span>
      </div>
    </div>
  );
}

/* ─────────── EVIDENCE OVERLAY ─────────── */
function EvidenceOverlay() {
  const { detections } = useSimulation();
  const latest = detections.length > 0 ? detections[detections.length - 1] : null;
  const sonarRef = useRef(null);
  const opticalRef = useRef(null);
  const samRef = useRef(null);
  const bathyRef = useRef(null);

  useEffect(() => {
    if (!latest) return;
    drawEvSonar(sonarRef.current);
    drawEvOptical(opticalRef.current);
    drawEvSAM(samRef.current);
    drawEvBathy(bathyRef.current);
  }, [latest]);

  return (
    <div className="panel" style={{ flex: "0 0 auto" }}>
      <div className="panel-header">
        🔬 Evidence Overlay
        <span style={{ color: "var(--amber)", fontSize: ".68rem" }}>
          {latest ? `${latest.id} — ${latest.type}` : "--"}
        </span>
      </div>
      <div className="panel-body" style={{ padding: 8 }}>
        <div className="evidence-panel">
          <div className="ev-img-row">
            <div className="ev-img"><canvas ref={sonarRef} /><div className="ev-label">SSS Waterfall</div></div>
            <div className="ev-img"><canvas ref={opticalRef} /><div className="ev-label">Optical</div></div>
            <div className="ev-img"><canvas ref={samRef} /><div className="ev-label">SAM2 Mask</div></div>
            <div className="ev-img"><canvas ref={bathyRef} /><div className="ev-label">Bathymetry</div></div>
          </div>
          <div style={{ textAlign: "center", fontSize: ".72rem", color: "var(--muted)", marginTop: 4 }}>
            {latest
              ? `Fused conf: ${(latest.conf * 100).toFixed(0)}% · Risk: ${latest.risk} · ${latest.depth}m depth`
              : "Select a target to view evidence"}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────── SYSTEM LOG ─────────── */
function SystemLog() {
  const { logEntries } = useSimulation();
  const feedRef = useRef(null);

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [logEntries]);

  return (
    <div className="panel" style={{ flex: 1 }}>
      <div className="panel-header">📋 System Log</div>
      <div className="panel-body" style={{ padding: 6 }}>
        <div className="log-feed" ref={feedRef}>
          {logEntries.map((entry, i) => (
            <div className="log-line" key={i}>
              <span className="log-ts">{entry.time}</span>
              <span className={`log-tag log-${entry.tag}`}>[{entry.tag}]</span>
              <span className="log-msg">{entry.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─────────── EVIDENCE CANVAS DRAW HELPERS ─────────── */
function drawEvSonar(canvas) {
  if (!canvas) return;
  const wrap = canvas.parentElement;
  const w = wrap.clientWidth || 120, h = wrap.clientHeight || 80;
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const v = Math.random() * 60 + 10;
      const bv = Math.floor(Math.min(255, v));
      ctx.fillStyle = `rgb(${Math.floor(bv * 0.1)},${Math.floor(bv * 0.7)},${Math.floor(bv * 0.9)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  }
  const tx = w * 0.45, ty = h * 0.55;
  ctx.fillStyle = "rgba(255,220,50,0.9)";
  ctx.fillRect(tx - 3, ty - 8, 6, 8);
  ctx.fillStyle = "rgba(0,0,0,0.85)";
  ctx.fillRect(tx + 3, ty - 5, 12, 5);
  ctx.strokeStyle = "rgba(251,191,36,.8)"; ctx.lineWidth = 1.5;
  ctx.strokeRect(tx - 4, ty - 9, 8, 10);
}

function drawEvOptical(canvas) {
  if (!canvas) return;
  const wrap = canvas.parentElement;
  const w = wrap.clientWidth || 120, h = wrap.clientHeight || 80;
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, "#0a2540"); g.addColorStop(1, "#062010");
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "rgba(180,150,80,0.2)"; ctx.lineWidth = 1;
  for (let i = 0; i < h; i += 6) { ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(w, i + (Math.random() - .5) * 4); ctx.stroke(); }
  ctx.fillStyle = "rgba(200,180,100,0.7)";
  ctx.beginPath(); ctx.ellipse(w * 0.45, h * 0.55, w * 0.08, h * 0.06, 0.3, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = "rgba(251,191,36,0.9)"; ctx.lineWidth = 1.5;
  ctx.strokeRect(w * 0.32, h * 0.42, w * 0.26, h * 0.26);
  ctx.fillStyle = "rgba(251,191,36,0.8)"; ctx.font = `${Math.max(7, w * 0.08)}px monospace`;
  ctx.fillText("TGT", w * 0.33, h * 0.38);
}

function drawEvSAM(canvas) {
  if (!canvas) return;
  const wrap = canvas.parentElement;
  const w = wrap.clientWidth || 120, h = wrap.clientHeight || 80;
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#000"; ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "rgba(56,189,248,0.25)";
  ctx.beginPath(); ctx.ellipse(w * 0.45, h * 0.55, w * 0.12, h * 0.1, 0.3, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = "rgba(56,189,248,0.9)"; ctx.lineWidth = 1.5;
  ctx.stroke();
  for (let i = 0; i < 200; i++) {
    const px = w * 0.33 + Math.random() * w * 0.24, py = h * 0.44 + Math.random() * h * 0.22;
    ctx.fillStyle = `rgba(56,189,248,${0.4 + Math.random() * 0.5})`;
    ctx.fillRect(px, py, 1.5, 1.5);
  }
}

function drawEvBathy(canvas) {
  if (!canvas) return;
  const wrap = canvas.parentElement;
  const w = wrap.clientWidth || 120, h = wrap.clientHeight || 80;
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#000"; ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "rgba(45,212,191,0.8)"; ctx.lineWidth = 1.5;
  ctx.beginPath();
  for (let x = 0; x <= w; x += 2) {
    let y = h * 0.6 + Math.sin(x * 0.1) * h * 0.05 + (Math.random() - .5) * h * 0.03;
    if (x > w * 0.35 && x < w * 0.55) y -= h * 0.25 + Math.sin((x - w * 0.35) / (w * 0.2) * Math.PI) * h * 0.15;
    if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.fillStyle = "rgba(45,212,191,0.08)";
  ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = "rgba(251,191,36,0.8)"; ctx.lineWidth = 1;
  ctx.setLineDash([2, 2]);
  ctx.beginPath(); ctx.moveTo(w * 0.45, 0); ctx.lineTo(w * 0.45, h); ctx.stroke();
  ctx.setLineDash([]);
}