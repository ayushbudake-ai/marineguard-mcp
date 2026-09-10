const MODULES = [
  { n: "1", name: "Sensor Suite Compiler", detail: "Parses AUV/ROV YAML specs, emits MCP tool stubs per platform." },
  { n: "2", name: "Detection & Fusion Engine", detail: "Sonar, optical, and bathymetry detectors combined via Dempster-Shafer fusion." },
  { n: "3", name: "Mission Firewall", detail: "LOW/MEDIUM/HIGH/CRITICAL risk taxonomy gating vehicle actions." },
  { n: "4", name: "Explainable Trace Engine", detail: "Per-target evidence composite and structured reasoning log." },
  { n: "5", name: "MCP Tool Server", detail: "Exposes 9 compiled tools to any MCP-compatible agent." },
  { n: "6", name: "Report Exporters", detail: "PDF, GeoJSON, and S-100 evidence packet generation." },
];

export default function About() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-xl text-fg">About MarineGuard</h1>
      <p className="mt-2 text-sm text-muted">
        MarineGuard is a marine debris detection and reporting pipeline for autonomous underwater
        vehicles, built for the Ministry of Earth Sciences (SIH26057). This dashboard is the operator
        console for the pipeline — six modules, each with its own dedicated view.
      </p>

      <div className="mt-8 divide-y divide-line border border-line bg-surface">
        {MODULES.map((m) => (
          <div key={m.n} className="flex gap-4 px-5 py-4">
            <div className="font-mono text-sm text-teal">{m.n}</div>
            <div>
              <div className="text-sm text-fg">{m.name}</div>
              <div className="mt-0.5 text-xs text-muted">{m.detail}</div>
            </div>
          </div>
        ))}
      </div>

      <a
        href="https://github.com/ayushbudake-ai/marineguard-mcp"
        target="_blank"
        rel="noreferrer"
        className="mt-6 inline-block text-sm text-teal underline decoration-teal/40 underline-offset-2 hover:decoration-teal"
      >
        View source on GitHub →
      </a>

      <div className="mt-6 border border-teal/40 bg-teal/10 px-4 py-3 text-xs text-teal">
        Connected to MarineGuard live inference backend (FastAPI bridge). Operating with verified YOLOv8n Side-Scan Sonar detection pipeline and Role 3 post-processing.
      </div>
    </div>
  );
}
