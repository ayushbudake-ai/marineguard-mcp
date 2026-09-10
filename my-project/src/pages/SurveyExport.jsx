import {
  Download,
  FileArchive,
  FileJson,
  FileSpreadsheet,
  FileText,
  Radio,
  RefreshCw,
} from "lucide-react";

import ExportCard from "../components/ExportCard";
import {
  getDetectionStats,
  getMockDetections,
} from "./mockdetection";

export default function SurveyExport() {
  const detections = getMockDetections();
  const stats = getDetectionStats();

  const exportDetectionsAsCSV = () => {
    const headers = [
      "ID",
      "Type",
      "Category",
      "Confidence",
      "Risk",
      "Latitude",
      "Longitude",
      "Depth",
      "Size",
      "Quantity",
      "Sensor",
      "Status",
      "Timestamp",
    ];

    const rows = detections.map((detection) => [
      detection.id,
      detection.type,
      detection.category,
      detection.confidence,
      detection.risk,
      detection.location.latitude,
      detection.location.longitude,
      detection.depth,
      detection.size,
      detection.quantity,
      detection.sensor,
      detection.status,
      detection.timestamp,
    ]);

    const csv = [
      headers.join(","),
      ...rows.map((row) =>
        row
          .map((value) => `"${String(value).replace(/"/g, '""')}"`)
          .join(",")
      ),
    ].join("\n");

    downloadFile(
      csv,
      "marineguard-detections.csv",
      "text/csv"
    );
  };

  const exportDetectionsAsJSON = () => {
    const data = {
      project: "MarineGuard",
      exportType: "Detection Data",
      exportedAt: new Date().toISOString(),
      totalDetections: detections.length,
      statistics: stats,
      detections,
    };

    downloadFile(
      JSON.stringify(data, null, 2),
      "marineguard-detections.json",
      "application/json"
    );
  };

  const exportMissionReport = () => {
    const report = {
      title: "MarineGuard Mission Report",

      mission: {
        vehicle: "AUV-01",
        sensor: "SONAR-AUV-01",
        status: "Completed",
      },

      summary: {
        totalDetections: stats.total,
        highRisk: stats.high,
        mediumRisk: stats.medium,
        lowRisk: stats.low,
        confirmed: stats.confirmed,
        requiringReview: stats.review,
        averageConfidence:
          `${stats.averageConfidence}%`,
      },

      detections,
    };

    downloadFile(
      JSON.stringify(report, null, 2),
      "marineguard-mission-report.json",
      "application/json"
    );
  };

  const exportCompleteArchive = () => {
    const archiveData = {
      marineguard: {
        version: "1.0",
        exportedAt: new Date().toISOString(),
      },

      mission: {
        id: "MG-MISSION-001",
        vehicle: "Sagar Netra",
        platform: "AUV-01",
        sensor: "SONAR-AUV-01",
      },

      statistics: stats,

      detections,

      system: {
        sonar: "Operational",
        optical: "Operational",
        depthSensor: "Operational",
        detectionEngine: "Operational",
      },
    };

    downloadFile(
      JSON.stringify(archiveData, null, 2),
      "marineguard-complete-survey.json",
      "application/json"
    );
  };

  return (
    <div className="space-y-6">
      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-3">
            <div className="rounded-md bg-teal/10 p-2">
              <Download
                size={20}
                className="text-teal"
              />
            </div>

            <div>
              <h1 className="font-mono text-xl font-semibold tracking-wide text-fg">
                SURVEY EXPORT
              </h1>

              <p className="mt-1 text-sm text-muted">
                Export MarineGuard survey and detection data
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-md border border-line bg-surface px-4 py-2">
          <span className="h-2 w-2 rounded-full bg-teal" />

          <span className="font-mono text-xs text-teal">
            DATA READY
          </span>
        </div>
      </div>

      {/* ================================================= */}
      {/* MISSION SUMMARY */}
      {/* ================================================= */}

      <section className="rounded-lg border border-line bg-surface">
        <div className="border-b border-line px-5 py-4">
          <div className="flex items-center gap-2">
            <Radio
              size={16}
              className="text-teal"
            />

            <h2 className="font-mono text-sm font-semibold tracking-wide text-fg">
              CURRENT SURVEY
            </h2>
          </div>

          <p className="mt-1 text-xs text-muted">
            Data available for export
          </p>
        </div>

        <div className="grid grid-cols-2 gap-px bg-line md:grid-cols-4">
          <SummaryItem
            label="MISSION"
            value="MG-001"
          />

          <SummaryItem
            label="PLATFORM"
            value="AUV-01"
          />

          <SummaryItem
            label="DETECTIONS"
            value={stats.total}
          />

          <SummaryItem
            label="CONFIDENCE"
            value={`${stats.averageConfidence}%`}
          />
        </div>
      </section>

      {/* ================================================= */}
      {/* EXPORT CARDS */}
      {/* ================================================= */}

      <div>
        <div className="mb-4">
          <h2 className="font-mono text-sm font-semibold tracking-wide text-fg">
            EXPORT OPTIONS
          </h2>

          <p className="mt-1 text-xs text-muted">
            Select the format required for your survey data
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <ExportCard
            title="Detection CSV"
            description="Tabular detection data for analysis"
            type="csv"
            count={detections.length}
            onExport={exportDetectionsAsCSV}
          />

          <ExportCard
            title="Detection JSON"
            description="Structured detection and sensor data"
            type="json"
            count={detections.length}
            onExport={exportDetectionsAsJSON}
          />

          <ExportCard
            title="Mission Report"
            description="Complete mission detection report"
            type="report"
            count={detections.length}
            onExport={exportMissionReport}
          />
        </div>
      </div>

      {/* ================================================= */}
      {/* COMPLETE EXPORT */}
      {/* ================================================= */}

      <section className="rounded-lg border border-line bg-surface">
        <div className="flex flex-col justify-between gap-4 p-5 md:flex-row md:items-center">
          <div className="flex items-center gap-4">
            <div className="rounded-md bg-teal/10 p-3">
              <FileArchive
                size={22}
                className="text-teal"
              />
            </div>

            <div>
              <h2 className="font-mono text-sm font-semibold tracking-wide text-fg">
                COMPLETE SURVEY PACKAGE
              </h2>

              <p className="mt-1 text-xs text-muted">
                Export all available MarineGuard mission data
                in one package
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={exportCompleteArchive}
            className="
              flex items-center justify-center gap-2
              rounded-md border border-teal/30
              bg-teal/5 px-5 py-3
              font-mono text-xs font-medium
              tracking-wide text-teal
              transition-all
              hover:border-teal/60
              hover:bg-teal/10
            "
          >
            <Download size={15} />

            EXPORT COMPLETE DATA
          </button>
        </div>
      </section>

      {/* ================================================= */}
      {/* DATA INFORMATION */}
      {/* ================================================= */}

      <section className="rounded-lg border border-line bg-surface">
        <div className="border-b border-line px-5 py-4">
          <div className="flex items-center gap-2">
            <FileText
              size={16}
              className="text-teal"
            />

            <h2 className="font-mono text-sm font-semibold tracking-wide text-fg">
              EXPORT INFORMATION
            </h2>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-3">
          <InfoItem
            icon={FileSpreadsheet}
            title="CSV"
            description="Compatible with Excel and data analysis tools"
          />

          <InfoItem
            icon={FileJson}
            title="JSON"
            description="Machine-readable structured survey data"
          />

          <InfoItem
            icon={RefreshCw}
            title="Live Data"
            description="Generated from the current survey session"
          />
        </div>
      </section>
    </div>
  );
}

/* ===================================================== */
/* SUMMARY ITEM */
/* ===================================================== */

function SummaryItem({ label, value }) {
  return (
    <div className="bg-surface p-5">
      <p className="font-mono text-[10px] tracking-widest text-muted">
        {label}
      </p>

      <p className="mt-2 font-mono text-lg text-fg">
        {value}
      </p>
    </div>
  );
}

/* ===================================================== */
/* INFO ITEM */
/* ===================================================== */

function InfoItem({
  icon: Icon,
  title,
  description,
}) {
  return (
    <div className="flex gap-3 rounded-md border border-line bg-surface2 p-4">
      <div className="shrink-0">
        <Icon
          size={17}
          className="text-teal"
        />
      </div>

      <div>
        <p className="font-mono text-xs text-fg">
          {title}
        </p>

        <p className="mt-1 text-[11px] leading-relaxed text-muted">
          {description}
        </p>
      </div>
    </div>
  );
}

/* ===================================================== */
/* DOWNLOAD HELPER */
/* ===================================================== */

function downloadFile(
  content,
  filename,
  mimeType
) {
  const blob = new Blob([content], {
    type: mimeType,
  });

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);

  link.click();

  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}