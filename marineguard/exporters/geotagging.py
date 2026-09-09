"""
Role 4 — Geotagging for MarineGuard MCP

Attaches coordinate information to detections from REAL available data only.

Coordinate sources (in priority order):
    1. detection.metadata["latitude"] + detection.metadata["longitude"]
    2. detection.metadata["coordinates"] as {"lat": ..., "lon": ...}
    3. mission_metadata supplied externally

If no real coordinates are available:
    latitude = None
    longitude = None

NEVER fabricated. Pixel bounding-box coordinates are NOT geographic coordinates
and are never converted to latitude/longitude here.

Synthetic values are only allowed in clearly marked tests/fixtures.
"""

from __future__ import annotations

from typing import Optional, Tuple, Dict, Any

from marineguard.detection.schema import Detection, DetectionResult


# ---------------------------------------------------------------------------
# GeoCoordinate
# ---------------------------------------------------------------------------

class GeoCoordinate:
    """A geographic coordinate pair with explicit null support."""

    def __init__(self, latitude: Optional[float], longitude: Optional[float]):
        self.latitude = latitude
        self.longitude = longitude

    @property
    def is_available(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

    def to_geojson_coordinates(self) -> Optional[list]:
        """Returns GeoJSON-ordered [longitude, latitude] or None if unavailable.

        GeoJSON Point coordinates MUST be [longitude, latitude] per RFC 7946 §3.1.1.
        """
        if self.is_available:
            return [self.longitude, self.latitude]
        return None

    def __repr__(self) -> str:
        if self.is_available:
            return f"GeoCoordinate(lat={self.latitude}, lon={self.longitude})"
        return "GeoCoordinate(unavailable)"


# ---------------------------------------------------------------------------
# Geotagger
# ---------------------------------------------------------------------------

class Geotagger:
    """Extracts REAL coordinate information from Detection metadata.

    This class ONLY reads coordinates from actual available data fields.
    It NEVER generates, calculates, or fabricates coordinates.

    Valid coordinate sources:
        - detection.metadata["latitude"] + detection.metadata["longitude"]
        - detection.metadata["coordinates"]["lat"] + ["lon"]
        - External mission_metadata (if caller provides it and it was real data)

    Pixel bounding boxes are NEVER treated as geographic coordinates.
    """

    def geotag(
        self,
        detection: Detection,
        mission_metadata: Optional[Dict[str, Any]] = None,
    ) -> GeoCoordinate:
        """Extract coordinate from a Detection object.

        Args:
            detection: The Detection to geotag.
            mission_metadata: Optional external metadata dict that may contain
                              real coordinates from navigation logs or ping headers.
                              Must originate from actual instrument data.

        Returns:
            GeoCoordinate — with lat/lon filled if available, or both None.
        """
        meta = detection.metadata or {}

        # Source 1: flat lat/lon keys in detection metadata
        if "latitude" in meta and "longitude" in meta:
            lat = meta["latitude"]
            lon = meta["longitude"]
            if self._is_valid_coord(lat) and self._is_valid_coord(lon):
                return GeoCoordinate(float(lat), float(lon))

        # Source 2: nested coordinates dict in detection metadata
        coords = meta.get("coordinates")
        if isinstance(coords, dict):
            lat = coords.get("lat") or coords.get("latitude")
            lon = coords.get("lon") or coords.get("longitude")
            if self._is_valid_coord(lat) and self._is_valid_coord(lon):
                return GeoCoordinate(float(lat), float(lon))

        # Source 3: external mission metadata (caller asserts it is real data)
        if mission_metadata:
            lat = mission_metadata.get("latitude")
            lon = mission_metadata.get("longitude")
            if self._is_valid_coord(lat) and self._is_valid_coord(lon):
                return GeoCoordinate(float(lat), float(lon))

        # No real coordinates available
        return GeoCoordinate(None, None)

    def geotag_result(
        self,
        result: DetectionResult,
        mission_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, GeoCoordinate]:
        """Geotag all detections in a DetectionResult.

        Returns a dict mapping detection index to GeoCoordinate.
        Indices correspond to result.detections list positions.
        """
        return {
            i: self.geotag(det, mission_metadata)
            for i, det in enumerate(result.detections)
        }

    @staticmethod
    def _is_valid_coord(value: Any) -> bool:
        """Return True if value is a finite number usable as a coordinate."""
        if value is None:
            return False
        try:
            f = float(value)
        except (TypeError, ValueError):
            return False
        import math
        return math.isfinite(f)
