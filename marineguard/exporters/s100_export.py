"""
Role 4 — S-100/S-124-Inspired Exporter for MarineGuard MCP

IMPORTANT — SCOPE DISCLAIMER:
    This is a PARTIAL IMPLEMENTATION of an S-100-inspired export format.
    It is NOT a certified IHO S-100 / S-124 product.
    It does NOT claim hydrographic survey accuracy.
    It does NOT claim navigational safety compliance.

What IS supported (from available DetectionResult data):
    - Detection identity (class_id, class_name)
    - Raw confidence score
    - Calibrated confidence score (0-100 scale)
    - Bounding box in pixel coordinates
    - Source sensor (optical / side-scan sonar)
    - Filter status (accepted / rejected)
    - Coordinates if present in metadata (null if unavailable)

What IS NOT supported (unavailable in the data pipeline):
    - Real depth / bathymetry measurements
    - Horizontal accuracy metrics
    - Sonar survey geometry (slant range, grazing angle)
    - Vessel / platform navigation track
    - S-124 navigational warning attributes
    - Hydrographic feature type hierarchy
    - Geometric quality indicators

Fields that are unavailable are represented as null, NOT fabricated.

Validation:
    If the result has no accepted detections, the exporter still produces
    a valid empty output with a clear zero-detection note.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.exporters.geotagging import Geotagger


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class S100ExportValidationError(ValueError):
    """Raised when export input fails pre-export validation."""
    pass


# ---------------------------------------------------------------------------
# S100Exporter
# ---------------------------------------------------------------------------

class S100Exporter:
    """Exports DetectionResult to an S-100-inspired JSON structure.

    PARTIAL IMPLEMENTATION — see module docstring for scope.
    Consumes the frozen Role 3 DetectionResult output.
    Does NOT accept the legacy ClassifiedTarget schema.
    """

    SUPPORTED_FIELDS = [
        "detection_id",
        "class_id",
        "class_name",
        "raw_confidence",
        "calibrated_confidence",
        "source_sensor",
        "bbox_pixels",
        "filter_status",
        "latitude",
        "longitude",
    ]

    UNSUPPORTED_FIELDS = [
        "depth_m",
        "bathymetry",
        "horizontal_accuracy_m",
        "slant_range_m",
        "grazing_angle_deg",
        "navigation_track",
        "vessel_info",
        "s124_hazard_attributes",
        "quality_of_sounding",
    ]

    def __init__(self):
        self._geotagger = Geotagger()

    def validate(self, result: DetectionResult) -> None:
        """Validate the DetectionResult before export.

        Raises:
            S100ExportValidationError if the result is not in an exportable state.
        """
        if not isinstance(result, DetectionResult):
            raise S100ExportValidationError(
                f"Expected DetectionResult, got {type(result).__name__}"
            )
        # Zero detections is valid (produces empty features list)
        # No other blocking validation at this point

    def export(
        self,
        result: DetectionResult,
        output_file: Optional[str] = None,
        mission_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Export DetectionResult to S-100-inspired JSON catalog.

        Args:
            result: Role 3 DetectionResult.
            output_file: Optional file path to write JSON.
            mission_metadata: Optional real mission metadata (coordinates, etc.)

        Returns:
            S-100-inspired dict. See module docstring for supported/unsupported fields.

        Raises:
            S100ExportValidationError: If input is invalid.
        """
        self.validate(result)

        features: List[Dict[str, Any]] = []

        for i, det in enumerate(result.detections):
            coord = self._geotagger.geotag(det, mission_metadata)
            features.append(self._build_feature(i, det, coord))

        catalog: Dict[str, Any] = {
            "s100Header": {
                "specification": "IHO S-100 — MarineGuard PARTIAL IMPLEMENTATION",
                "complianceStatement": (
                    "This output is NOT a certified IHO S-100 or S-124 product. "
                    "It uses an S-100-inspired structure to represent MarineGuard "
                    "detection results. It does NOT claim hydrographic accuracy, "
                    "navigational safety compliance, or full S-100/S-124 conformance."
                ),
                "generator": "MarineGuard MCP — Role 4 S-100 Exporter",
                "supportedFields": self.SUPPORTED_FIELDS,
                "unsupportedFields": self.UNSUPPORTED_FIELDS,
                "unsupportedFieldsNote": (
                    "Fields listed in unsupportedFields are unavailable in the "
                    "current data pipeline and are represented as null. "
                    "They are NOT fabricated."
                ),
            },
            "detectionSummary": {
                "totalAccepted": len(result.detections),
                "role3Summary": result.role3_summary,
            },
            "features": features,
        }

        if output_file:
            dirname = os.path.dirname(output_file)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(catalog, f, indent=2)

        return catalog

    def _build_feature(
        self,
        detection_id: int,
        det: Detection,
        coord,
    ) -> Dict[str, Any]:
        """Build a single S-100-inspired feature entry from a Detection."""
        meta = det.metadata or {}
        role3 = meta.get("role3", {}) or {}
        calibrated_conf = meta.get("calibrated_confidence") or role3.get("calibrated_confidence")
        source_sensor = meta.get("source_sensor", "unknown")

        return {
            "detectionId": detection_id,
            "classId": det.class_id,
            "className": det.class_name,
            "rawConfidence": round(det.confidence, 6),
            "calibratedConfidence": calibrated_conf,     # 0-100 scale; null if unavailable
            "sourceSensor": source_sensor,               # "optical" | "side-scan sonar" | "unknown"
            "bboxPixels": {
                "x1": round(det.bbox[0], 2),
                "y1": round(det.bbox[1], 2),
                "x2": round(det.bbox[2], 2),
                "y2": round(det.bbox[3], 2),
            },
            "filterStatus": "accepted",
            # Geographic position — null if unavailable (NOT fabricated)
            "position": {
                "latitude": coord.latitude,
                "longitude": coord.longitude,
                "coordSource": (
                    "detection_metadata"
                    if coord.is_available
                    else "unavailable — not present in source data"
                ),
            },
            # Fields unavailable in current data pipeline — null, not fabricated
            "depthMeters": None,
            "bathymetry": None,
            "horizontalAccuracyMeters": None,
            "qualityOfSounding": None,
        }
