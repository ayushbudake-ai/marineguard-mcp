// -----------------------------------------------------------------------
// MarineGuard API layer
// -----------------------------------------------------------------------
// The marineguard-mcp repo currently exposes the pipeline through an MCP
// tool server (marineguard/mcp_server.py) and a Streamlit app — there is
// no REST API yet for this React UI to call. Every function below is
// mocked so the dashboard is fully clickable today.
//
// TODO when the backend exists: replace each function body with a
// `fetch("/api/...")` call. Keep the same function names and return
// shapes so no component code has to change. A minimal FastAPI wrapper
// around marineguard/pipeline/inference.py would map naturally to these
// four endpoints: POST /upload, POST /detect, GET /metrics, POST /reports
// -----------------------------------------------------------------------

import { MOCK_DETECTIONS, MOCK_METRICS, MOCK_REPORTS } from "./mockdetection";

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function uploadSurveyFile(file) {
  await delay(600);
  // TODO: const form = new FormData(); form.append("file", file);
  // return fetch("/api/upload", { method: "POST", body: form }).then(r => r.json());
  return { fileId: "mock-file-" + Date.now(), filename: file.name, sizeBytes: file.size };
}

export async function runDetection({ fileId, confidenceThreshold }) {
  await delay(1400);
  // TODO: return fetch("/api/detect", {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ fileId, confidenceThreshold }),
  // }).then(r => r.json());

  const total = MOCK_DETECTIONS.length;
  const accepted = MOCK_DETECTIONS.filter((d) => d.confidence >= confidenceThreshold);
  const filtered = total - accepted.length;
  const avgConfidence =
    accepted.reduce((sum, d) => sum + d.confidence, 0) / (accepted.length || 1);

  return {
    fileId,
    confidenceThreshold,
    totalDetections: total,
    acceptedCount: accepted.length,
    filteredCount: filtered,
    averageConfidence: Number(avgConfidence.toFixed(2)),
    processingTimeMs: 1180,
    detections: MOCK_DETECTIONS.map((d) => ({
      ...d,
      status: d.confidence >= confidenceThreshold ? "accepted" : "filtered",
    })),
  };
}

export async function fetchMetrics() {
  await delay(400);
  // TODO: return fetch("/api/metrics").then(r => r.json());
  return MOCK_METRICS;
}

export async function fetchReports() {
  await delay(300);
  // TODO: return fetch("/api/reports").then(r => r.json());
  return MOCK_REPORTS;
}

export async function generateReport({ format }) {
  await delay(900);
  // TODO: return fetch("/api/reports", {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ format }),
  // }).then(r => r.json());
  return {
    id: "RPT-" + Date.now(),
    format,
    createdAt: new Date().toISOString(),
    downloadUrl: null, // no real file until the backend generates one
  };
}