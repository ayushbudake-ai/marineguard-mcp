import React, { useState } from "react";
import { SimulationProvider, useSimulation } from "./context/SimulationContext";
import Dashboard from "./pages/Dashboard";
import SensorsPage from "./pages/SensorSuite";
import TargetsPage from "./pages/Targets";
import AboutPage from "./pages/About";

function Topbar({ page, setPage }) {
  const { clock } = useSimulation();
  const tabs = [
    { key: "dashboard", label: "📡 Dashboard" },
    { key: "sensors", label: "🔊 Sensors" },
    { key: "targets", label: "🎯 Targets" },
    { key: "about", label: "ℹ About" },
  ];

  return (
    <div className="topbar">
      <div className="tb-brand">
        <div className="sonar-dot" />
        MarineGuard MCP
        <span style={{ fontWeight: 400, color: "var(--muted)", fontSize: ".75rem" }}>
          | Mission Control
        </span>
      </div>
      <div className="nav-tabs">
        {tabs.map(tab => (
          <button
            key={tab.key}
            className={`nav-tab${page === tab.key ? " active" : ""}`}
            onClick={() => setPage(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tb-status">
        <span className="status-pill pill-green">
          <span className="pulse pulse-green" />AUV Online
        </span>
        <span className="status-pill pill-cyan">
          <span className="pulse pulse-amber" />Mission Active
        </span>
        <span className="tb-time">{clock}</span>
      </div>
    </div>
  );
}

function Footer() {
  return (
    <div className="footbar">
      <span>MarineGuard MCP · SIH26057 · Ministry of Earth Sciences</span>
      <span>
        <a href="https://github.com/ayushbudake-ai/marineguard-mcp" target="_blank" rel="noreferrer">GitHub</a>
        {" · "}
        <a href="https://ayushbudake-ai.github.io/marineguard-mcp/" target="_blank" rel="noreferrer">Landing Page</a>
      </span>
      <span style={{ color: "var(--teal)" }}>Sim running</span>
    </div>
  );
}

function AppContent() {
  const [page, setPage] = useState("dashboard");

  return (
    <>
      <Topbar page={page} setPage={setPage} />
      <div className="app-root">
        {page === "dashboard" && <Dashboard />}
        {page === "sensors" && <SensorsPage />}
        {page === "targets" && <TargetsPage />}
        {page === "about" && <AboutPage />}
      </div>
      <Footer />
    </>
  );
}

export default function App() {
  return (
    <SimulationProvider>
      <AppContent />
    </SimulationProvider>
  );
}
