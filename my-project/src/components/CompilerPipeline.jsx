const STAGES = [
  { file: "sensor_parser.py", role: "Reads the platform's YAML spec" },
  { file: "geometry_solver.py", role: "Computes swath, range, altitude from sensor physics" },
  { file: "pipeline_generator.py", role: "Generates ordered sensor pipeline config" },
  { file: "mcp_emitter.py", role: "Emits executable @mcp.tool stubs per sensor" },
];

export default function CompilerPipeline({ specFile }) {
  const nodes = [
    { label: specFile, sublabel: "Platform spec", accent: true },
    ...STAGES.map((s) => ({ label: s.file, sublabel: s.role, accent: false })),
    { label: "MCP tool stubs", sublabel: "Compiled output", accent: true },
  ];

  return (
    <div className="flex flex-col gap-0 overflow-x-auto md:flex-row md:items-stretch">
      {nodes.map((node, i) => (
        <div key={node.label} className="flex items-center">
          <PipelineNode {...node} />
          {i < nodes.length - 1 && (
            <>
              <span className="mx-1 hidden shrink-0 text-muted md:block">→</span>
              <span className="my-1 block shrink-0 text-center text-muted md:hidden">↓</span>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

function PipelineNode({ label, sublabel, accent }) {
  return (
    <div
      className={`min-w-[150px] border px-3 py-3 md:min-w-[130px] ${
        accent ? "border-teal/50 bg-teal/10" : "border-line bg-surface"
      }`}
    >
      <div className={`font-mono text-xs ${accent ? "text-teal" : "text-fg"}`}>{label}</div>
      <div className="mt-1 text-[11px] leading-snug text-muted">{sublabel}</div>
    </div>
  );
}
