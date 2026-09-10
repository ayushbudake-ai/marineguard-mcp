import { useState } from "react";
import { Link } from "react-router";
import { PLATFORMS } from "../data/platform";
import CompilerPipeline from "../components/CompilerPipeline";
import SensorCard from "../components/SensorCard";

function buildIllustrativeYaml(platform) {
  const lines = [
    `platform: ${platform.id}`,
    `display_name: "${platform.label}"`,
    `sensors:`,
    ...platform.sensors.flatMap((s) => [`  - name: ${s.name.toLowerCase().replace(/\s+/g, "_")}`, `    detail: "${s.detail}"`]),
  ];
  return lines.join("\n");
}

export default function SensorSuite() {
  const [platformId, setPlatformId] = useState("sagar_netra");
  const platform = PLATFORMS.find((p) => p.id === platformId);

  return (
    <div className="max-w-4xl">
      <h1 className="text-xl text-fg">Sensor Suite Compiler</h1>
      <p className="mt-1 text-sm text-muted">
        Parses AUV/ROV spec YAML files and emits MCP tool stubs — no per-platform manual coding needed.
      </p>

      <div className="mt-6 border border-line bg-surface px-4 py-3">
        <div className="text-xs uppercase tracking-wide text-muted">Platform</div>
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
      </div>

      <div className="mt-10">
        <div className="mb-2 text-xs uppercase tracking-wide text-muted">Compiler pipeline</div>
        <CompilerPipeline specFile={platform.specFile} />
      </div>

      <div className="mt-10">
        <div className="mb-2 text-xs uppercase tracking-wide text-muted">
          Sensors — {platform.label}
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {platform.sensors.map((sensor) => (
            <SensorCard key={sensor.name} sensor={sensor} />
          ))}
        </div>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-2">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs uppercase tracking-wide text-muted">{platform.specFile}</span>
            <span className="font-mono text-[10px] uppercase tracking-wide text-amber">Illustrative format</span>
          </div>
          <pre className="overflow-x-auto border border-line bg-surface px-4 py-4 font-mono text-xs text-fg">
            {buildIllustrativeYaml(platform)}
          </pre>
          <p className="mt-2 text-xs text-muted">
            The actual spec file wasn't available to read — this shows a plausible format based on the
            README, not the real file contents.
          </p>
        </div>

        <div className="flex flex-col justify-between border border-line bg-surface px-5 py-5">
          <div>
            <div className="text-xs uppercase tracking-wide text-muted">Compiled output</div>
            <div className="mt-2 font-mono text-2xl text-teal">{platform.toolsCompiled}</div>
            <div className="mt-1 text-xs text-muted">MCP tool stubs emitted for {platform.label}</div>
          </div>
          <Link
            to="/mcp-tools"
            className="mt-6 inline-block text-xs text-teal underline decoration-teal/40 underline-offset-2 hover:decoration-teal"
          >
            View MCP tool server →
          </Link>
        </div>
      </div>
    </div>
  );
}
