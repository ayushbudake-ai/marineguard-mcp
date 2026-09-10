// Tool names, categories, and descriptions are paraphrased from the
// Module 5 table in the repo README (marineguard/mcp_server.py). The
// request/response examples are illustrative only — they are not
// confirmed against marineguard/schemas.py, so don't treat them as a
// locked contract. Mark them clearly as examples in the UI.

export const MCP_TOOLS = [
  {
    name: "marine_debris_survey",
    category: "Orchestration",
    description: "Runs a full autonomous survey end-to-end: acquisition, detection, fusion, firewall evaluation, and reporting.",
    example: {
      request: { platform: "sagar_netra", survey_area: { lat: 15.372, lng: 73.819, radius_m: 500 }, confidence_threshold: 0.5 },
      response: { mission_id: "mission-0182", status: "completed", detections_found: 6, report_id: "RPT-2026-09-05" },
    },
  },
  {
    name: "start_side_scan_survey",
    category: "Acquisition",
    description: "Starts side-scan sonar (100/400 kHz) acquisition for the current mission.",
    example: {
      request: { platform: "sagar_netra", frequency_khz: 400 },
      response: { survey_id: "sss-0091", status: "acquiring" },
    },
  },
  {
    name: "detect_debris_sonar",
    category: "Detection",
    description: "Runs the side-scan sonar detection pipeline — shadow and highlight analysis — over acquired data.",
    example: {
      request: { survey_id: "sss-0091" },
      response: { detections: [{ id: "DET-0001", confidence: 0.94, range_bin: 132 }] },
    },
  },
  {
    name: "start_sas_survey",
    category: "Acquisition",
    description: "Starts Synthetic Aperture Sonar acquisition, for Kongsberg HUGIN 3000 platforms.",
    example: {
      request: { platform: "hugin_3000" },
      response: { survey_id: "sas-0034", status: "acquiring" },
    },
  },
  {
    name: "detect_debris_optical",
    category: "Detection",
    description: "Runs the YOLOv8-style optical detection pass over 4K stereo imagery.",
    example: {
      request: { survey_id: "sss-0091" },
      response: { detections: [{ id: "DET-0002", bbox: [70, 50, 150, 110], confidence: 0.88 }] },
    },
  },
  {
    name: "start_bathymetry_mapping",
    category: "Acquisition",
    description: "Starts MBES bathymetry mapping for depth-anomaly and protrusion detection.",
    example: {
      request: { survey_id: "sss-0091" },
      response: { survey_id: "mbes-0021", status: "mapping" },
    },
  },
  {
    name: "classify_target",
    category: "Fusion",
    description: "Fuses all sensor detections for a target using Dempster-Shafer evidence combination and returns the final classification.",
    example: {
      request: { target_id: "DET-0002" },
      response: { target_id: "DET-0002", fused_confidence: 0.88, object_class: "Metal drum" },
    },
  },
  {
    name: "trigger_close_inspection",
    category: "Mission control",
    description: "Directs the vehicle to approach and re-image a flagged target at closer range.",
    example: {
      request: { target_id: "DET-0003" },
      response: { status: "approaching", eta_seconds: 45 },
    },
  },
  {
    name: "export_report",
    category: "Export",
    description: "Generates the PDF / GeoJSON / S-100 evidence package for a completed mission.",
    example: {
      request: { mission_id: "mission-0182", formats: ["pdf", "geojson"] },
      response: { report_id: "RPT-2026-09-05", download_urls: { pdf: null, geojson: null } },
    },
  },
];
