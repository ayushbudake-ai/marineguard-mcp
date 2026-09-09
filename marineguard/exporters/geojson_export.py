"""
Role 4 — GeoJSON FeatureCollection Exporter for MarineGuard MCP

Exports DetectionResult (Role 3 output) to standard GeoJSON format.

Coordinate handling:
    If real coordinates are available in detection.metadata:
        geometry = {"type": "Point", "coordinates": [longitude, latitude]}
        (GeoJSON order: longitude first, per RFC 7946 §3.1.1)
    If coordinates are unavailable:
        geometry = null
        (Valid GeoJSON per RFC 7946 §3.2 — a Feature with null geometry
         is permitted and preserves detection properties without fabricating location.)

Coordinate Reference System:
    WGS84 geographic coordinates are assumed when coordinates are present.
    No CRS conversion is performed. If the coordinate reference system of
    input data is unknown, no conversion is silently claimed.

Only accepted detections are exported as primary features.
Rejected detections appear in a separate "rejected_detections" property on
the FeatureCollection for audit purposes, but are never mixed into the
primary feature list.

No coordinates, timestamps, sensor values, or metadata are fabricated.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.exporters.geotagging import Geotagger, GeoCoordinate


class GeoJSONExporter:
    """Exports DetectionResult to standard GeoJSON FeatureCollection.

    Consumes the frozen Role 3 DetectionResult output.
    Does NOT accept the legacy ClassifiedTarget schema.
    """

    def __init__(self):
        self._geotagger = Geotagger()

    def export(
        self,
        result: DetectionResult,
        output_file: Optional[str] = None,
        mission_metadata: Optional[Dict[str, Any]] = None,
        include_rejected: bool = True,
    ) -> Dict[str, Any]:
        """Export DetectionResult to a GeoJSON FeatureCollection.

        Args:
            result: Role 3 DetectionResult (accepted detections in .detections,
                    all detections with rejection info in .all_detections).
            output_file: Optional file path to write JSON output.
            mission_metadata: Optional real mission metadata dict that may
                              provide coordinates. Must come from actual data.
            include_rejected: If True, rejected detections are included in a
                              separate FeatureCollection property for audit.

        Returns:
            GeoJSON FeatureCollection dict.
        """
        features: List[Dict[str, Any]] = []

        # Build accepted detection features
        for i, det in enumerate(result.detections):
            coord = self._geotagger.geotag(det, mission_metadata)
            feature = self._build_feature(
                detection_id=i,
                det=det,
                coord=coord,
                filter_status="accepted",
            )
            features.append(feature)

        collection: Dict[str, Any] = {
            "type": "FeatureCollection",
            # CRS annotation — WGS84 assumed; no conversion performed
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
            },
            "features": features,
            "properties": {
                "generator": "MarineGuard MCP — Role 4 GeoJSON Exporter",
                "coordinate_note": (
                    "Coordinates are taken from detection metadata only. "
                    "null geometry indicates coordinates were not available "
                    "in the source data. No coordinates were fabricated."
                ),
                "accepted_count": len(result.detections),
                "role3_summary": result.role3_summary,
            },
        }

        # Include rejected detection audit entries if available and requested
        if include_rejected and result.all_detections:
            rejected_entries = [
                d for d in result.all_detections
                if isinstance(d, dict) and d.get("role3", {}).get("filter_status") == "rejected"
            ]
            if rejected_entries:
                collection["properties"]["rejected_count"] = len(rejected_entries)
                collection["properties"]["rejected_audit"] = rejected_entries

        if output_file:
            import os
            os.makedirs(os.path.dirname(output_file), exist_ok=True) if os.path.dirname(output_file) else None
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(collection, f, indent=2)

        return collection

    def _build_feature(
        self,
        detection_id: int,
        det: Detection,
        coord: GeoCoordinate,
        filter_status: str,
    ) -> Dict[str, Any]:
        """Build a single GeoJSON Feature from a Detection."""
        meta = det.metadata or {}

        # Geometry: Point with [lon, lat] if coords available; null otherwise
        if coord.is_available:
            geometry: Optional[Dict[str, Any]] = {
                "type": "Point",
                "coordinates": coord.to_geojson_coordinates(),  # [lon, lat]
            }
        else:
            geometry = None

        # Extract Role 3 metadata if present
        role3 = meta.get("role3", {}) or {}
        calibrated_conf = meta.get("calibrated_confidence") or role3.get("calibrated_confidence")
        source_sensor = meta.get("source_sensor", "unknown")
        timestamp = meta.get("timestamp")

        properties: Dict[str, Any] = {
            "detection_id": detection_id,
            "class_id": det.class_id,
            "class_name": det.class_name,
            "raw_confidence": round(det.confidence, 6),
            "calibrated_confidence": calibrated_conf,
            "source_sensor": source_sensor,
            "bbox": list(det.bbox),  # [x1, y1, x2, y2] pixel coords
            "filter_status": filter_status,
            "latitude": coord.latitude,
            "longitude": coord.longitude,
        }

        if timestamp is not None:
            properties["timestamp"] = timestamp

        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        }
