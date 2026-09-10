// Mock detection results, shaped to match what marineguard/schemas.py + the
// inference pipeline should return in production. Swap the api layer's
// implementation (src/api/marineguard.js) once real endpoints exist —
// nothing in the components needs to change, they just consume this shape.

export const MOCK_DETECTIONS = [
  { id: "DET-0001", objectClass: "Fishing net", confidence: 0.94, lat: 15.372, lng: 73.812, status: "accepted", timestamp: "2026-09-05T06:12:04Z" },
  { id: "DET-0002", objectClass: "Metal drum", confidence: 0.88, lat: 15.379, lng: 73.828, status: "accepted", timestamp: "2026-09-05T06:12:41Z" },
  { id: "DET-0003", objectClass: "Tarpaulin sheet", confidence: 0.61, lat: 15.365, lng: 73.819, status: "accepted", timestamp: "2026-09-05T06:13:02Z" },
  { id: "DET-0004", objectClass: "Unidentified debris", confidence: 0.42, lat: 15.381, lng: 73.803, status: "filtered", timestamp: "2026-09-05T06:13:47Z" },
  { id: "DET-0005", objectClass: "Rope bundle", confidence: 0.77, lat: 15.358, lng: 73.831, status: "accepted", timestamp: "2026-09-05T06:14:15Z" },
  { id: "DET-0006", objectClass: "Plastic container", confidence: 0.35, lat: 15.374, lng: 73.839, status: "filtered", timestamp: "2026-09-05T06:14:52Z" },
];

export const MOCK_METRICS = {
  f1: 0.89,
  precision: 0.91,
  recall: 0.87,
  falsePositiveRate: 0.06,
  falseNegativeRate: null, // not yet computed by eval.py — label as unavailable, don't invent it
  latencyMs: 214,
  sampleCount: 480,
};

export const MOCK_REPORTS = [
  { id: "RPT-2026-09-05", label: "Survey — Goa coastal transect", createdAt: "2026-09-05T06:20:00Z", detections: 6, formats: ["pdf", "geojson"] },
  { id: "RPT-2026-09-03", label: "Survey — Mandovi estuary pass", createdAt: "2026-09-03T09:04:00Z", detections: 11, formats: ["pdf", "geojson"] },
];