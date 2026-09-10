// -----------------------------------------------------------------------
// MarineGuard Real API Client Layer
// Connects React UI to FastAPI Backend Bridge (http://127.0.0.1:8000)
// -----------------------------------------------------------------------

const API_BASE = "/api";

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
    return await res.json();
  } catch (err) {
    return {
      status: "unavailable",
      service: "MarineGuard MCP",
      sss_model: "offline",
      message: err.message,
      roles: {},
    };
  }
}

export async function fetchDemoSamples() {
  try {
    const res = await fetch(`${API_BASE}/demo-samples`);
    if (!res.ok) {
      // Fallback to /api/samples if needed
      const fallbackRes = await fetch(`${API_BASE}/samples`);
      if (!fallbackRes.ok) throw new Error(`HTTP error: ${res.status}`);
      const data = await fallbackRes.json();
      return data.samples || [];
    }
    const data = await res.json();
    return data.samples || [];
  } catch (err) {
    console.error("Failed to fetch demo samples:", err);
    return [];
  }
}

export async function uploadSurveyFile(file, confidenceThreshold = 0.75) {
  const form = new FormData();
  form.append("file", file);
  form.append("confidenceThreshold", confidenceThreshold.toString());

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    let detail = `Upload failed with HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) detail = errJson.detail;
    } catch (_) {}
    throw new Error(detail);
  }

  return await res.json();
}

export async function runDetection({ fileId, sampleKey, confidenceThreshold = 0.75 }) {
  const res = await fetch(`${API_BASE}/detect`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fileId,
      sampleKey,
      confidenceThreshold,
    }),
  });

  if (!res.ok) {
    throw new Error(`Detection pipeline failed with HTTP ${res.status}`);
  }

  return await res.json();
}

export async function getCurrentDetections() {
  try {
    const res = await fetch(`${API_BASE}/detections/current`);
    if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch current detections:", err);
    return null;
  }
}

export async function getDetectionById(detectionId) {
  const res = await fetch(`${API_BASE}/detections/${detectionId}`);
  if (!res.ok) {
    throw new Error(`Detection ${detectionId} not found`);
  }
  return await res.json();
}

export async function fetchMetrics() {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch metrics:", err);
    return null;
  }
}

export async function fetchReports() {
  try {
    const res = await fetch(`${API_BASE}/reports`);
    if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch reports:", err);
    return [];
  }
}

export async function generateReport({ format = "PDF" }) {
  const res = await fetch(`${API_BASE}/reports`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ format }),
  });

  if (!res.ok) {
    throw new Error(`Report generation failed with HTTP ${res.status}`);
  }

  return await res.json();
}