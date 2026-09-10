import { useState } from "react";

export default function McpToolRow({ tool, connected }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <li className="border-b border-line/60 last:border-0">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-surface2"
      >
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm text-fg">{tool.name}</span>
            <span className="border border-line px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-muted">
              {tool.category}
            </span>
          </div>
          <div className="mt-1 text-xs text-muted">{tool.description}</div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span className={`font-mono text-xs ${connected ? "text-teal" : "text-muted"}`}>
            {connected ? "Available" : "Unreachable"}
          </span>
          <span className="text-muted">{expanded ? "−" : "+"}</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-line bg-ink px-4 py-3">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-wide text-amber">
            Example only — not a confirmed schema
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <div className="mb-1 text-xs text-muted">Request</div>
              <pre className="overflow-x-auto bg-surface px-3 py-2 font-mono text-xs text-fg">
                {JSON.stringify(tool.example.request, null, 2)}
              </pre>
            </div>
            <div>
              <div className="mb-1 text-xs text-muted">Response</div>
              <pre className="overflow-x-auto bg-surface px-3 py-2 font-mono text-xs text-fg">
                {JSON.stringify(tool.example.response, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </li>
  );
}
