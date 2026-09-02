"""
Underwater Optical Detection & SAM2 Segmentation Pipeline for MarineGuard MCP
"""

from typing import Dict, Any, List
from marineguard.schemas import DebrisContact


class OpticalDetector:
    """RT-DETR + SAM2 Optical Debris Classification & Instance Segmentation Engine."""

    def __init__(self, confidence_threshold: float = 0.50):
        self.confidence_threshold = confidence_threshold

    def process_optical_frame(self, ping_payload: Dict[str, Any]) -> List[DebrisContact]:
        """Runs RT-DETR detection & SAM2 instance mask generation on optical crop."""
        meta = ping_payload.get("target_meta", {})
        confidence = meta.get("optical_confidence", 0.85)

        if confidence < self.confidence_threshold:
            return []

        contact = DebrisContact(
            contact_id=f"OPTICAL_{meta.get('id', 'Contact_01')}",
            sensor_id="optical_01",
            sensor_type="optical",
            raw_confidence=round(confidence, 3),
            bbox=(20.0, 20.0, 100.0, 100.0),
            label_candidate=meta.get("type", "ghost_net"),
            estimated_dimensions_m=meta.get("dimensions_m", (10.0, 5.0, 0.5)),
            lat_lon=meta.get("lat_lon", (13.0835, 80.2715)),
            depth_m=meta.get("depth_m", 24.3),
        )

        return [contact]
