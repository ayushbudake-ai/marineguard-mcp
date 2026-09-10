import { useState } from "react";
import { Link } from "react-router";
import McpToolRow from "../components/Evidence/McpToolRow";
import { MCP_TOOLS } from "../data/mcptools";
import { PLATFORMS } from "../data/platform";

// TODO: this page has no real transport to marineguard/mcp_server.py — a
// browser can't speak MCP's stdio/SSE transport directly. Once there's a
// backend status endpoint (e.g. a lightweight GET /api/mcp/status that
// pings the server and reports per-tool health), replace the `connected`
// simulation below with that fetch. The tool catalog itself (src/data/mcpTools.js)
// is sourced from the README and can stay as the display fallback even
// once live status exists.

export default function McpToolServer() {
  const [connected, setConnected] = useState(false);
  const [platformId, setPlatformId] = useState("sagar_netra");
  const platform = PLATFORMS.find((p) => p.id === platformId);

  return (
    <div className="max-w-4xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl text-fg">MCP Tool Server</h1>
          <p className="mt-1 text-sm text-muted">
            Tools compiled and exposed by marineguard/mcp_server.py to any MCP-compatible agent.
          </p>
        </div>
        <div className="flex items-center gap-2 border border-line bg-surface px-3 py-1.5">
          <span className={`inline-block h-2 w-2 rounded-full ${connected ? "bg-teal" : "bg-muted"}`} />
          <span className="font-mono text-xs text-muted">{connected ? "Connected" : "Not connected"}</span>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3 border border-line bg-surface px-4 py-3">
        <span className="text-xs uppercase tracking-wide text-muted">Simulation controls</span>
        <button
          onClick={() => setConnected((v) => !v)}
          className={`border px-3 py-1.5 text-xs ${
            connected ? "border-teal/60 text-teal" : "border-line text-fg hover:border-teal/60 hover:text-teal"
          }`}
        >
          {connected ? "Disconnect" : "Connect"} (simulated)
        </button>
        <span className="text-xs text-muted">
          No real MCP transport is wired up yet — this toggle only simulates tool availability below.
        </span>
      </div>

      <div className="mt-6 border border-line bg-surface px-4 py-3">
        <div className="text-xs uppercase tracking-wide text-muted">Compiled for platform</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {PLATFORMS.map((p) => (
            <button
              key={p.id}
              onClick={() => setPlatformId(p.id)}
              className={`border px-3 py-1.5 text-xs ${
                platformId === p.id ? "border-teal/60 bg-teal/10 text-teal" : "border-line text-muted hover:text-fg"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="mt-2 font-mono text-xs text-muted">
          Sensors: {platform.sensors.map((s) => s.name).join(", ")}
        </div>
        <Link to="/sensor-suite" className="mt-3 inline-block text-xs text-teal underline decoration-teal/40 underline-offset-2 hover:decoration-teal">
          View sensor suite compiler →
        </Link>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="border border-line bg-surface px-5 py-4">
          <div className="text-xs uppercase tracking-wide text-muted">Tools compiled</div>
          <div className="mt-2 font-mono text-2xl text-fg">{MCP_TOOLS.length}</div>
        </div>
        <div className="border border-line bg-surface px-5 py-4">
          <div className="text-xs uppercase tracking-wide text-muted">Available</div>
          <div className="mt-2 font-mono text-2xl text-teal">{connected ? MCP_TOOLS.length : 0}</div>
        </div>
        <div className="border border-line bg-surface px-5 py-4">
          <div className="text-xs uppercase tracking-wide text-muted">Server module</div>
          <div className="mt-2 truncate font-mono text-xs text-fg">mcp_server.py</div>
        </div>
        <div className="border border-line bg-surface px-5 py-4">
          <div className="text-xs uppercase tracking-wide text-muted">Transport</div>
          <div className="mt-2 font-mono text-xs text-muted">Not specified in repo</div>
        </div>
      </div>

      <div className="mt-8">
        <div className="mb-2 text-xs uppercase tracking-wide text-muted">Tool catalog</div>
        <ul className="border border-line bg-surface">
          {MCP_TOOLS.map((tool) => (
            <McpToolRow key={tool.name} tool={tool} connected={connected} />
          ))}
        </ul>
      </div>
    </div>
  );
}
