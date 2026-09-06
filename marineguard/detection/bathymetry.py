"""
Multibeam Bathymetry Surface Anomaly Pipeline for MarineGuard MCP — Role 2: AI Inference & Integration
"""

from typing import Dict, Any, List, Optional
import numpy as np
from marineguard.schemas import DebrisContact
from marineguard.detection.model_loader import MarineDebrisModel


class BathymetryDetector:
    """MBES Bathymetry Seafloor Anomaly Extraction Engine.

    When best.pt is loaded and fine-tuned for depth grids, runs the model on normalized grid.
    In development mode or when uncalibrated, uses depth-protrusion anomaly heuristics.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.50,
        model: Optional[MarineDebrisModel] = None,
    ):
        self.confidence_threshold = confidence_threshold
        self.model = model if model is not None else MarineDebrisModel.get(confidence_threshold=confidence_threshold)

    @property
    def is_model_loaded(self) -> bool:
        return self.model.is_loaded

    def process_bathymetry_grid(self, ping_payload: Dict[str, Any], allow_dev_fallback: bool = True) -> List[DebrisContact]:
        """Cross-references bathymetric depth grid anomalies against contacts."""
        meta = ping_payload.get("target_meta", {})
        grid = ping_payload.get("bathymetry_grid")

        if self.model.is_loaded and isinstance(grid, np.ndarray):
            normalized = ((grid - grid.min()) / (np.ptp(grid) + 1e-6) * 255).astype(np.uint8)
            detections = self.model.predict(normalized)
            contacts = []
            for i, det in enumerate(detections):
                contacts.append(DebrisContact(
                    contact_id=f"BATHY_{meta.get('id', f'Contact_{i:02d}')}",
                    sensor_id="mbes_01",
                    sensor_type="bathymetry",
                    raw_confidence=round(det["confidence"], 3),
                    bbox=det["bbox"],
                    label_candidate=det["class_name"],
                    estimated_dimensions_m=meta.get("dimensions_m", (10.0, 5.0, 0.5)),
                    lat_lon=meta.get("lat_lon", (13.0835, 80.2715)),
                    depth_m=meta.get("depth_m", 24.3),
                ))
            return contacts

        # Development test replay fallback (active while best.pt is pending from Member 1)
        if not allow_dev_fallback:
            return []

        anomaly_m = meta.get("bathymetry_anomaly_m", 0.5)
        confidence = min(0.95, round(0.50 + (anomaly_m * 0.3), 3))

        contact = DebrisContact(
            contact_id=f"BATHY_{meta.get('id', 'Contact_01')}",
            sensor_id="mbes_01",
            sensor_type="bathymetry",
            raw_confidence=confidence,
            bbox=(12.0, 12.0, 20.0, 20.0),
            label_candidate=meta.get("type", "ghost_net"),
            estimated_dimensions_m=meta.get("dimensions_m", (10.0, 5.0, 0.5)),
            lat_lon=meta.get("lat_lon", (13.0835, 80.2715)),
            depth_m=meta.get("depth_m", 24.3),
        )
        return [contact]
