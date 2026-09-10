export const MOCK_DETECTIONS = [
  {
    id: "MG-001",
    type: "Plastic Debris",
    category: "Plastic",
    confidence: 96,
    risk: "High",

    location: {
      latitude: 18.5204,
      longitude: 73.8567,
    },

    depth: 42,
    size: "Large",
    quantity: 12,

    sensor: "SONAR-AUV-01",

    timestamp: "2026-09-09T20:42:00Z",

    status: "Confirmed",

    description:
      "Large concentration of floating and submerged plastic debris detected by sonar and optical sensors.",

    evidence: {
      sonar: true,
      optical: true,
      bathymetry: true,
    },
  },

  {
    id: "MG-002",
    type: "Fishing Net",
    category: "Fishing Gear",
    confidence: 91,
    risk: "Medium",

    location: {
      latitude: 18.5181,
      longitude: 73.8422,
    },

    depth: 31,
    size: "Medium",
    quantity: 4,

    sensor: "SONAR-AUV-01",

    timestamp: "2026-09-09T20:36:00Z",

    status: "Confirmed",

    description:
      "Abandoned fishing net detected on the seabed with elongated acoustic signature.",

    evidence: {
      sonar: true,
      optical: true,
      bathymetry: false,
    },
  },

  {
    id: "MG-003",
    type: "Metal Object",
    category: "Metal",
    confidence: 87,
    risk: "Medium",

    location: {
      latitude: 18.529,
      longitude: 73.8511,
    },

    depth: 57,
    size: "Medium",
    quantity: 1,

    sensor: "SONAR-AUV-01",

    timestamp: "2026-09-09T20:30:00Z",

    status: "Review",

    description:
      "High-density object detected beneath the seabed surface. Classification requires further review.",

    evidence: {
      sonar: true,
      optical: false,
      bathymetry: true,
    },
  },

  {
    id: "MG-004",
    type: "Unknown Object",
    category: "Unknown",
    confidence: 76,
    risk: "Low",

    location: {
      latitude: 18.5145,
      longitude: 73.8612,
    },

    depth: 24,
    size: "Small",
    quantity: 2,

    sensor: "SONAR-AUV-01",

    timestamp: "2026-09-09T20:22:00Z",

    status: "Review",

    description:
      "Low-confidence acoustic signature detected. Object classification is currently uncertain.",

    evidence: {
      sonar: true,
      optical: false,
      bathymetry: false,
    },
  },

  {
    id: "MG-005",
    type: "Glass Bottle",
    category: "Glass",
    confidence: 94,
    risk: "Low",

    location: {
      latitude: 18.5232,
      longitude: 73.8484,
    },

    depth: 18,
    size: "Small",
    quantity: 8,

    sensor: "OPTICAL-CAM-01",

    timestamp: "2026-09-09T20:16:00Z",

    status: "Confirmed",

    description:
      "Multiple glass containers detected using optical imagery near the seabed.",

    evidence: {
      sonar: false,
      optical: true,
      bathymetry: true,
    },
  },

  {
    id: "MG-006",
    type: "Plastic Container",
    category: "Plastic",
    confidence: 89,
    risk: "Medium",

    location: {
      latitude: 18.5168,
      longitude: 73.8542,
    },

    depth: 36,
    size: "Medium",
    quantity: 6,

    sensor: "SONAR-AUV-01",

    timestamp: "2026-09-09T20:09:00Z",

    status: "Confirmed",

    description:
      "Several plastic containers identified within a localized debris field.",

    evidence: {
      sonar: true,
      optical: true,
      bathymetry: true,
    },
  },
];

export const MOCK_METRICS = {
  f1: 0.89,
  precision: 0.91,
  recall: 0.87,
  falsePositiveRate: 0.06,
  falseNegativeRate: null,
  latencyMs: 214,
  sampleCount: 480,
};

export const MOCK_REPORTS = [
  {
    id: "RPT-2026-09-05",
    label: "Survey - Goa coastal transect",
    createdAt: "2026-09-05T06:20:00Z",
    detections: 6,
    formats: ["pdf", "geojson"],
  },
  {
    id: "RPT-2026-09-03",
    label: "Survey - Mandovi estuary pass",
    createdAt: "2026-09-03T09:04:00Z",
    detections: 11,
    formats: ["pdf", "geojson"],
  },
];

/* -------------------------------------------------- */
/* GET ALL DETECTIONS */
/* -------------------------------------------------- */

export function getMockDetections() {
  return MOCK_DETECTIONS;
}

/* -------------------------------------------------- */
/* GET SINGLE DETECTION */
/* -------------------------------------------------- */

export function getMockDetectionById(id) {
  return MOCK_DETECTIONS.find(
    (detection) => detection.id === id
  );
}

/* -------------------------------------------------- */
/* FILTER BY RISK */
/* -------------------------------------------------- */

export function getDetectionsByRisk(risk) {
  return MOCK_DETECTIONS.filter(
    (detection) =>
      detection.risk.toLowerCase() === risk.toLowerCase()
  );
}

/* -------------------------------------------------- */
/* FILTER BY CATEGORY */
/* -------------------------------------------------- */

export function getDetectionsByCategory(category) {
  return MOCK_DETECTIONS.filter(
    (detection) =>
      detection.category.toLowerCase() ===
      category.toLowerCase()
  );
}

/* -------------------------------------------------- */
/* HIGH RISK DETECTIONS */
/* -------------------------------------------------- */

export function getHighRiskDetections() {
  return MOCK_DETECTIONS.filter(
    (detection) => detection.risk === "High"
  );
}

/* -------------------------------------------------- */
/* DETECTION STATISTICS */
/* -------------------------------------------------- */

export function getDetectionStats() {
  const total = MOCK_DETECTIONS.length;

  const high = MOCK_DETECTIONS.filter(
    (detection) => detection.risk === "High"
  ).length;

  const medium = MOCK_DETECTIONS.filter(
    (detection) => detection.risk === "Medium"
  ).length;

  const low = MOCK_DETECTIONS.filter(
    (detection) => detection.risk === "Low"
  ).length;

  const confirmed = MOCK_DETECTIONS.filter(
    (detection) => detection.status === "Confirmed"
  ).length;

  const review = MOCK_DETECTIONS.filter(
    (detection) => detection.status === "Review"
  ).length;

  const averageConfidence =
    total === 0
      ? 0
      : Math.round(
          MOCK_DETECTIONS.reduce(
            (sum, detection) => sum + detection.confidence,
            0
          ) / total
        );

  return {
    total,
    high,
    medium,
    low,
    confirmed,
    review,
    averageConfidence,
  };
}

/* -------------------------------------------------- */
/* CONVERT FOR SONAR VISUALIZER */
/* -------------------------------------------------- */

export function getSonarDetections() {
  return MOCK_DETECTIONS.map((detection, index) => ({
    id: detection.id,
    label: detection.type,
    confidence: detection.confidence,

    // Visual positions for sonar screen
    x: [28, 67, 55, 78, 38, 62][index] ?? 50,
    y: [35, 27, 68, 72, 48, 58][index] ?? 50,

    size:
      detection.risk === "High"
        ? 13
        : detection.risk === "Medium"
          ? 10
          : 8,
  }));
}

/* -------------------------------------------------- */
/* SIMULATE DETECTION PROCESS */
/* -------------------------------------------------- */

export function runMockDetection() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        message: "Detection completed successfully.",
        detections: MOCK_DETECTIONS,
        statistics: getDetectionStats(),
      });
    }, 1200);
  });
}

/* -------------------------------------------------- */
/* DEFAULT EXPORT */
/* -------------------------------------------------- */

export default MOCK_DETECTIONS;