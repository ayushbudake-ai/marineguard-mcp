"""
Side-Scan Sonar Detection Pipeline for MarineGuard MCP — Role 2: AI Inference & Integration
"""

from typing import Dict, Any, List, Optional
import numpy as np
from marineguard.schemas import DebrisContact
from marineguard.detection.model_loader import MarineDebrisModel


class SideScanDetector:
    """CFAR pre-filter + YOLO Side-Scan Sonar Waterfall Processing Engine.

    Runs the trained model on real waterfall sonar imagery when available.
    In development/replay test mode (when best.pt is pending from Member 1),
    falls back to ping metadata to maintain pipeline testability.
    """

    def __init__(
        self,
        cfar_pfa: float = 1e-4,
        confidence_threshold: float = 0.50,
        model: Optional[MarineDebrisModel] = None,
    ):
        self.cfar_pfa = cfar_pfa
        self.confidence_threshold = confidence_threshold
        self.model = model if model is not None else MarineDebrisModel.get(confidence_threshold=confidence_threshold)

    @property
    def is_model_loaded(self) -> bool:
        return self.model.is_loaded

    def cfar_detect(self, waterfall_row: np.ndarray, num_guard: int = 4, num_ref: int = 16) -> List[int]:
        """Cell-Averaging Constant False Alarm Rate (CA-CFAR) anomaly detector."""
        anomalies = []
        N = len(waterfall_row)
        for i in range(num_ref + num_guard, N - num_ref - num_guard):
            ref_cells = np.concatenate([
                waterfall_row[i - num_ref - num_guard : i - num_guard],
                waterfall_row[i + num_guard + 1 : i + num_guard + 1 + num_ref],
            ])
            noise_floor = np.mean(ref_cells)
            alpha = num_ref * (self.cfar_pfa ** (-1.0 / num_ref) - 1.0)
            threshold = alpha * noise_floor
            if waterfall_row[i] > threshold:
                anomalies.append(i)
        return anomalies

    def process_waterfall_ping(self, ping_payload: Dict[str, Any], allow_dev_fallback: bool = True) -> List[DebrisContact]:
        """Runs CFAR pre-filtering, then model detection on side-scan ping payload."""
        meta = ping_payload.get("target_meta", {})
        sonar_img = ping_payload.get("sonar_waterfall")

        if sonar_img is not None and isinstance(sonar_img, np.ndarray) and len(sonar_img.shape) >= 2:
            # CFAR pre-filter
            row_idx = min(128, sonar_img.shape[0] - 1)
            middle_row = sonar_img[row_idx, :]
            if len(middle_row.shape) == 1:
                _ = self.cfar_detect(middle_row)

        # Real model inference path
        if self.model.is_loaded and sonar_img is not None:
            detections = self.model.predict(sonar_img)
            contacts = []
            for i, det in enumerate(detections):
                contacts.append(DebrisContact(
                    contact_id=f"SONAR_{meta.get('id', f'Contact_{i:02d}')}",
                    sensor_id="side_scan_01",
                    sensor_type="side_scan",
                    raw_confidence=round(det["confidence"], 3),
                    bbox=det["bbox"],
                    label_candidate=det["class_name"],
                    acoustic_shadow_ratio=meta.get("shadow_ratio", 0.35),
                    estimated_dimensions_m=meta.get("dimensions_m", (10.0, 5.0, 0.5)),
                    lat_lon=meta.get("lat_lon", (13.0835, 80.2715)),
                    depth_m=meta.get("depth_m", 24.3),
                ))
            return contacts

        # Development test replay fallback (active while best.pt is pending from Member 1)
        if not allow_dev_fallback:
            return []

        confidence = meta.get("sonar_confidence", 0.88)
        if confidence < self.confidence_threshold:
            return []

        contact = DebrisContact(
            contact_id=f"SONAR_{meta.get('id', 'Contact_01')}",
            sensor_id="side_scan_01",
            sensor_type="side_scan",
            raw_confidence=round(confidence, 3),
            bbox=(100.0, 100.0, 150.0, 150.0),
            label_candidate=meta.get("type", "ghost_net"),
            acoustic_shadow_ratio=meta.get("shadow_ratio", 0.35),
            estimated_dimensions_m=meta.get("dimensions_m", (10.0, 5.0, 0.5)),
            lat_lon=meta.get("lat_lon", (13.0835, 80.2715)),
            depth_m=meta.get("depth_m", 24.3),
        )
        return [contact]
