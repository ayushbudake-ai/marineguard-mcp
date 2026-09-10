import {
  Download,
  FileJson,
  FileText,
  FileSpreadsheet,
  Database,
  CheckCircle2,
} from "lucide-react";

const ICONS = {
  csv: FileSpreadsheet,
  json: FileJson,
  pdf: FileText,
  report: FileText,
  data: Database,
};

const FILE_TYPES = {
  csv: ".csv",
  json: ".json",
  pdf: ".pdf",
  report: ".pdf",
  data: ".json",
};

export default function ExportCard({
  title = "Detection Data",
  description = "Export detection results and sensor data",
  type = "csv",
  count = 0,
  onExport,
  disabled = false,
}) {
  const Icon = ICONS[type] || Download;
  const fileType = FILE_TYPES[type] || "";

  const handleExport = () => {
    if (disabled) return;

    if (onExport) {
      onExport(type);
      return;
    }

    // Default demo export
    const content = {
      marineguard: true,
      exportType: type,
      exportedAt: new Date().toISOString(),
      detections: count,
    };

    const blob = new Blob(
      [JSON.stringify(content, null, 2)],
      { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `marineguard-${type}-export.json`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="group rounded-lg border border-line bg-surface p-5 transition-all duration-200 hover:border-teal/40 hover:bg-surface2">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-teal/10 transition-colors group-hover:bg-teal/15">
            <Icon size={20} className="text-teal" />
          </div>

          <div>
            <h3 className="font-mono text-sm font-semibold tracking-wide text-fg">
              {title}
            </h3>

            <p className="mt-1 text-xs text-muted">
              {description}
            </p>
          </div>
        </div>

        <span className="rounded border border-line bg-surface2 px-2 py-1 font-mono text-[10px] uppercase text-muted">
          {type}
        </span>
      </div>

      {/* Information */}
      <div className="mt-5 flex items-center justify-between border-t border-line pt-4">
        <div>
          <p className="font-mono text-[10px] tracking-wider text-muted">
            RECORDS
          </p>

          <p className="mt-1 font-mono text-lg text-fg">
            {count}
          </p>
        </div>

        <div className="text-right">
          <p className="font-mono text-[10px] tracking-wider text-muted">
            FORMAT
          </p>

          <p className="mt-1 font-mono text-xs uppercase text-teal">
            {fileType || type}
          </p>
        </div>
      </div>

      {/* Export Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={handleExport}
        className="
          mt-5 flex w-full items-center justify-center gap-2
          rounded-md border border-teal/30
          bg-teal/5 px-4 py-2.5
          font-mono text-xs font-medium tracking-wide text-teal
          transition-all
          hover:bg-teal/10 hover:border-teal/60
          disabled:cursor-not-allowed disabled:opacity-40
        "
      >
        <Download size={15} />

        {disabled ? "EXPORT DISABLED" : "EXPORT DATA"}
      </button>

      {/* Status */}
      <div className="mt-3 flex items-center justify-center gap-1.5">
        <CheckCircle2 size={12} className="text-teal" />

        <span className="text-[10px] text-muted">
          Ready for export
        </span>
      </div>
    </div>
  );
}