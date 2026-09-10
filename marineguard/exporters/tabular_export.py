"""
Role 4 — Tabular Export (CSV / JSON) for MarineGuard MCP

Exports DetectionResult (Role 3 output) to structured tabular formats.

Supported formats:
    CSV  — comma-separated values, null fields as empty string
    JSON — structured JSON array, null fields as JSON null

Both formats include:
    - Accepted detections (primary output, filter_status="accepted")
    - Rejected detections (audit trail, filter_status="rejected") from all_detections

Fields exported (where available in actual data):
    detection_id         — sequential ID within the result
    class_id             — MarineGuard numeric class ID (null if unknown)
    class_name           — canonical class name from taxonomy
    raw_confidence       — raw model confidence [0.0-1.0]
    calibrated_confidence— Role 3 calibrated score [0-100] (null if unavailable)
    source_sensor        — "optical" | "side-scan sonar" | "unknown"
    bbox_x1              — bounding box left pixel coord
    bbox_y1              — bounding box top pixel coord
    bbox_x2              — bounding box right pixel coord
    bbox_y2              — bounding box bottom pixel coord
    latitude             — real latitude from metadata (null if unavailable)
    longitude            — real longitude from metadata (null if unavailable)
    timestamp            — timestamp from metadata (null if unavailable)
    filter_status        — "accepted" | "rejected"
    rejection_rule       — rule that caused rejection (null if accepted)
    rejection_reason     — human-readable reason (null if accepted)

No data is fabricated. Missing values are null/empty.
"""

from __future__ import annotations

import csv
import io
import json
import os
from typing import Any, Dict, List, Optional

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.exporters.geotagging import Geotagger


# Column order for CSV header
TABULAR_FIELDS = [
    "detection_id",
    "class_id",
    "class_name",
    "raw_confidence",
    "calibrated_confidence",
    "source_sensor",
    "bbox_x1",
    "bbox_y1",
    "bbox_x2",
    "bbox_y2",
    "latitude",
    "longitude",
    "timestamp",
    "filter_status",
    "rejection_rule",
    "rejection_reason",
]


class TabularExporter:
    """Exports DetectionResult to CSV or JSON tabular format.

    Consumes the frozen Role 3 DetectionResult output.
    Includes accepted detections as primary data and rejected detections
    as audit entries. No data is fabricated.
    """

    def __init__(self):
        self._geotagger = Geotagger()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_csv(
        self,
        result: DetectionResult,
        output_file: Optional[str] = None,
        mission_metadata: Optional[Dict[str, Any]] = None,
        include_rejected: bool = True,
    ) -> str:
        """Export DetectionResult to CSV string.

        Args:
            result: Role 3 DetectionResult.
            output_file: Optional path to write CSV file.
            mission_metadata: Optional real external metadata (coordinates, etc.)
            include_rejected: If True, rejected detections are appended with
                              their rejection info clearly set.

        Returns:
            CSV string.
        """
        rows = self._build_rows(result, mission_metadata, include_rejected)
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=TABULAR_FIELDS,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            # Convert None → empty string for CSV
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})
        csv_str = output.getvalue()

        if output_file:
            dirname = os.path.dirname(output_file)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(output_file, "w", encoding="utf-8", newline="") as f:
                f.write(csv_str)

        return csv_str

    def export_json(
        self,
        result: DetectionResult,
        output_file: Optional[str] = None,
        mission_metadata: Optional[Dict[str, Any]] = None,
        include_rejected: bool = True,
    ) -> str:
        """Export DetectionResult to JSON string.

        Args:
            result: Role 3 DetectionResult.
            output_file: Optional path to write JSON file.
            mission_metadata: Optional real external metadata.
            include_rejected: If True, rejected detections are included.

        Returns:
            JSON string. null values are JSON null.
        """
        rows = self._build_rows(result, mission_metadata, include_rejected)
        payload = {
            "schema": TABULAR_FIELDS,
            "generator": "MarineGuard MCP — Role 4 Tabular Exporter",
            "accepted_count": sum(1 for r in rows if r.get("filter_status") == "accepted"),
            "rejected_count": sum(1 for r in rows if r.get("filter_status") == "rejected"),
            "role3_summary": result.role3_summary,
            "detections": rows,
        }
        json_str = json.dumps(payload, indent=2)

        if output_file:
            dirname = os.path.dirname(output_file)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_rows(
        self,
        result: DetectionResult,
        mission_metadata: Optional[Dict[str, Any]],
        include_rejected: bool,
    ) -> List[Dict[str, Any]]:
        """Build list of row dicts for all detections."""
        rows: List[Dict[str, Any]] = []

        # Accepted detections — primary data
        for i, det in enumerate(result.detections):
            coord = self._geotagger.geotag(det, mission_metadata)
            rows.append(self._build_accepted_row(i, det, coord))

        # Rejected detections — from all_detections audit list
        if include_rejected and result.all_detections:
            for entry in result.all_detections:
                if not isinstance(entry, dict):
                    continue
                role3 = entry.get("role3", {}) or {}
                if role3.get("filter_status") != "rejected":
                    continue
                rows.append(self._build_rejected_row(entry, role3))

        return rows

    def _build_accepted_row(
        self,
        detection_id: int,
        det: Detection,
        coord,
    ) -> Dict[str, Any]:
        """Build a row dict for an accepted detection."""
        meta = det.metadata or {}
        role3 = meta.get("role3", {}) or {}
        calibrated_conf = meta.get("calibrated_confidence") or role3.get("calibrated_confidence")
        source_sensor = meta.get("source_sensor", "unknown")
        timestamp = meta.get("timestamp")

        return {
            "detection_id": detection_id,
            "class_id": det.class_id,
            "class_name": det.class_name,
            "raw_confidence": round(det.confidence, 6),
            "calibrated_confidence": calibrated_conf,
            "source_sensor": source_sensor,
            "bbox_x1": round(det.bbox[0], 2) if det.bbox else None,
            "bbox_y1": round(det.bbox[1], 2) if det.bbox else None,
            "bbox_x2": round(det.bbox[2], 2) if det.bbox else None,
            "bbox_y2": round(det.bbox[3], 2) if det.bbox else None,
            "latitude": coord.latitude,
            "longitude": coord.longitude,
            "timestamp": timestamp,
            "filter_status": "accepted",
            "rejection_rule": None,
            "rejection_reason": None,
        }

    def _build_rejected_row(
        self,
        entry: Dict[str, Any],
        role3: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a row dict for a rejected detection from all_detections audit."""
        bbox = entry.get("bbox") or []
        return {
            "detection_id": None,
            "class_id": entry.get("class_id"),
            "class_name": entry.get("class") or entry.get("class_name"),
            "raw_confidence": role3.get("raw_confidence"),
            "calibrated_confidence": role3.get("calibrated_confidence"),
            "source_sensor": (entry.get("metadata") or {}).get("source_sensor", "unknown"),
            "bbox_x1": round(bbox[0], 2) if len(bbox) >= 4 else None,
            "bbox_y1": round(bbox[1], 2) if len(bbox) >= 4 else None,
            "bbox_x2": round(bbox[2], 2) if len(bbox) >= 4 else None,
            "bbox_y2": round(bbox[3], 2) if len(bbox) >= 4 else None,
            "latitude": None,
            "longitude": None,
            "timestamp": None,
            "filter_status": "rejected",
            "rejection_rule": role3.get("rejection_rule"),
            "rejection_reason": role3.get("filter_reason"),
        }
