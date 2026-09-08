"""
Multibeam Bathymetry Surface Anomaly Pipeline for MarineGuard MCP — Role 2: AI Inference & Integration
"""

from typing import Dict, Any, List, Optional
import numpy as np
from marineguard.schemas import DebrisContact
from marineguard.detection.model_loader import MarineDebrisModel


class BathymetryDetector:
    """MBES Bathymetry Seafloor Anomaly Extraction Engine.

    Bathymetry currently uses the depth-protrusion anomaly heuristic because
    the repository does not contain a dedicated bathymetry-trained ML model.

    The generic MarineGuard model may be an optical or sonar model and must
    not be applied to MBES grids unless a dedicated bathymetry model is
    explicitly supplied.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.50,
        model: Optional[MarineDebrisModel] = None,
    ):
        self.confidence_threshold = confidence_threshold

        # A dedicated bathymetry model may be injected in the future.
        # Do not automatically load the shared MarineGuard model here because
        # that model may be trained for optical/sonar imagery rather than MBES.
        self.model = model

    @property
    def is_model_loaded(self) -> bool:
        return self.model is not None and self.model.is_loaded

    def process_bathymetry_grid(
        self,
        ping_payload: Dict[str, Any],
        allow_dev_fallback: bool = True,
    ) -> List[DebrisContact]:
        """Extract bathymetric anomalies and return structured contacts.

        A dedicated bathymetry model is used only when explicitly injected.
        Otherwise the existing depth-anomaly heuristic is used.
        """
        meta = ping_payload.get("target_meta", {})
        grid = ping_payload.get("bathymetry_grid")

        # Use a dedicated bathymetry model only when one is explicitly
        # provided. The generic MarineGuard model must not be applied to
        # bathymetry grids.
        if (
            self.model is not None
            and self.model.is_loaded
            and isinstance(grid, np.ndarray)
        ):
            normalized = (
                (grid - grid.min())
                / (np.ptp(grid) + 1e-6)
                * 255
            ).astype(np.uint8)

            detections = self.model.predict(normalized)
            contacts = []

            for i, det in enumerate(detections):
                contacts.append(
                    DebrisContact(
                        contact_id=f"BATHY_{meta.get('id', f'Contact_{i:02d}')}",
                        sensor_id="mbes_01",
                        sensor_type="bathymetry",
                        raw_confidence=round(det["confidence"], 3),
                        bbox=det["bbox"],
                        label_candidate=det["class_name"],
                        estimated_dimensions_m=meta.get(
                            "dimensions_m",
                            (10.0, 5.0, 0.5),
                        ),
                        lat_lon=meta.get(
                            "lat_lon",
                            (13.0835, 80.2715),
                        ),
                        depth_m=meta.get("depth_m", 24.3),
                    )
                )

            return contacts

        # Development/replay bathymetry path.
        # This is the correct path for the current synthetic MBES data
        # because no dedicated bathymetry-trained model is available.
        if not allow_dev_fallback:
            return []

        anomaly_m = meta.get("bathymetry_anomaly_m")

        # If metadata does not provide an anomaly value, try to estimate the
        # anomaly directly from the bathymetry grid.
        if anomaly_m is None and isinstance(grid, np.ndarray):
            if grid.size > 0:
                median_depth = float(np.median(grid))
                minimum_depth = float(np.min(grid))
                anomaly_m = abs(median_depth - minimum_depth)

        if anomaly_m is None:
            return []

        anomaly_m = float(anomaly_m)

        if anomaly_m <= 0:
            return []

        confidence = min(
            0.95,
            round(0.50 + (anomaly_m * 0.30), 3),
        )

        if confidence < self.confidence_threshold:
            return []

        contact = DebrisContact(
            contact_id=f"BATHY_{meta.get('id', 'Contact_01')}",
            sensor_id="mbes_01",
            sensor_type="bathymetry",
            raw_confidence=confidence,
            bbox=(12.0, 12.0, 20.0, 20.0),
            label_candidate=meta.get("type", "ghost_net"),
            estimated_dimensions_m=meta.get(
                "dimensions_m",
                (10.0, 5.0, 0.5),
            ),
            lat_lon=meta.get(
                "lat_lon",
                (13.0835, 80.2715),
            ),
            depth_m=meta.get("depth_m", 24.3),
        )

        return [contact]
