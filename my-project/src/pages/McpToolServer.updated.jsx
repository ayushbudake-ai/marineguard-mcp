import React, { useEffect, useState } from "react";
import { Link } from "react-router";
import { checkHealth } from "./marineguard";
import McpToolRow from "../components/Evidence/McpToolRow";
import { MCP_TOOLS } from "../data/mcptools";
import { PLATFORMS } from "../data/platform";

export default function McpToolServer() {
  const [health, setHealth] = useState({ status: "checking" });
  const [platformId, setPlatformId] = useState("sagar_netra");
  const platform = PLATFORMS.find((p) => p.id === platformId) || PLATFORMS[0];

  useEffect(() => {
    checkHealth().then(setHealth);
  }, []);

  const connected = health.status === "ok";

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-fg">MCP Tool Server Status</h1>
          <p className="mt-1 text-sm text-muted">
            Model Context Protocol tools emitted dynamically by <code>marineguard/mcp_server.py</code>.
          </p>
        </div>

        <div className="flex items-center gap-2 border border-line bg-surface px-4 py-2 rounded-md">
          <span className={`inline-block h-2.5 w-2.5 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-rose-400"}`} />
          <span className="font-mono text-xs font-semibold text-fg">
            {connected ? "BACKEND CONNECTED" : "BACKEND UNAVAILABLE"}
          </span>
        </div>
      </div>

      {/* Health Info Callout */}
      <div className={`mt-6 p-4 rounded-lg border ${connected ? "border-teal/40 bg-teal/10 text-teal" : "border-rose-500/40 bg-rose-500/10 text-rose-300"} text-xs font-mono`}>
        {connected ? (
          <div>
            ✅ <b>Real Backend Active:</b> Model <code>{health.model_name}</code> loaded (SHA: <code>{health.model_sha256?.substring(0, 16)}...</code>).
          </div>
        ) : (
          <div>
            ❌ <b>Backend Disconnected:</b> Start Python FastAPI bridge with <code>python api_server.py</code> on port 8000.
          </div>
        )}
      </div>

      <div className="mt-6 border border-line bg-surface p-5 rounded-lg">
        <div className="text-xs uppercase tracking-wide text-muted font-mono">Compiled Sensor Platform</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {PLATFORMS.map((p) => (
            <button
              key={p.id}
              onClick={() => setPlatformId(p.id)}
              className={`border px-3.5 py-2 text-xs rounded font-medium transition-all ${
                platformId === p.id ? "border-teal bg-teal/15 text-teal font-semibold" : "border-line text-muted hover:text-fg bg-surface2"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="mt-3 font-mono text-xs text-muted">
          Active Sensors: {platform.sensors.map((s) => s.name).join(", ")}
        </div>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="border border-line bg-surface px-5 py-4 rounded-lg">
          <div className="text-xs uppercase tracking-wide text-muted font-mono">Tools Emitted</div>
          <div className="mt-2 font-mono text-2xl text-fg">{MCP_TOOLS.length}</div>
        </div>
        <div className="border border-line bg-surface px-5 py-4 rounded-lg">
          <div className="text-xs uppercase tracking-wide text-muted font-mono">Active Tools</div>
          <div className="mt-2 font-mono text-2xl text-teal">{connected ? MCP_TOOLS.length : 0}</div>
        </div>
        <div className="border border-line bg-surface px-5 py-4 rounded-lg">
          <div className="text-xs uppercase tracking-wide text-muted font-mono">Server Module</div>
          <div className="mt-2 truncate font-mono text-xs text-fg">mcp_server.py</div>
        </div>
        <div className="border border-line bg-surface px-5 py-4 rounded-lg">
          <div className="text-xs uppercase tracking-wide text-muted font-mono">Protocol Interface</div>
          <div className="mt-2 font-mono text-xs text-teal">FastAPI / MCP JSON-RPC</div>
        </div>
      </div>

      <div className="mt-8">
        <div className="mb-2 text-xs uppercase tracking-wide text-muted font-mono">Emitted Tool Catalog</div>
        <ul className="border border-line bg-surface rounded-lg divide-y divide-line/60">
          {MCP_TOOLS.map((tool) => (
            <McpToolRow key={tool.name} tool={tool} connected={connected} />
          ))}
        </ul>
      </div>
    </div>
  );
}
