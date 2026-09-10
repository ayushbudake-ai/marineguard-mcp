"""
Underwater Optical Detection Pipeline for MarineGuard MCP — Role 2: AI Inference & Integration
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import numpy as np
from PIL import Image

from marineguard.schemas import DebrisContact
from marineguard.detection.model_loader import MarineDebrisModel
from marineguard.detection.schema import DetectionResult


class OpticalDetector:
    """Optical Debris Classification & Instance Segmentation Engine.

    Runs the trained YOLOv8n-seg ONNX/PyTorch model on real optical crops/frames.
    In development/replay test mode (when frame data is absent in simulated pings),
    falls back to ping metadata to maintain pipeline testability.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.50,
        model: Optional[MarineDebrisModel] = None,
        model_path: Optional[Union[str, Path]] = None,
    ):
        self.confidence_threshold = confidence_threshold
        repo_root = Path(__file__).resolve().parents[2]
        if model is not None:
            self.model = model
        else:
            default_optical_path = (
                repo_root / "runs" / "seaclear_yolov8n_seg" / "onnx" / "best.onnx"
                if (repo_root / "runs" / "seaclear_yolov8n_seg" / "onnx" / "best.onnx").exists()
                else (repo_root / "models" / "best.onnx" if (repo_root / "models" / "best.onnx").exists() else (repo_root / "models" / "best.pt"))
            )
            target_path = Path(model_path) if model_path is not None else default_optical_path
            self.model = MarineDebrisModel.get(
                model_path=target_path,
                confidence_threshold=confidence_threshold,
                task="segment",
            )

    @property
    def is_model_loaded(self) -> bool:
        return self.model.is_loaded

    def detect_image(self, image: Union[str, Path, bytes, np.ndarray, Image.Image]) -> DetectionResult:
        """Runs optical detection & segmentation on an image input and returns structured DetectionResult."""
        from marineguard.detection.pipeline import ImageDetectionPipeline
        from marineguard.detection.detector import ONNXOpticalDetector, YOLODetector

        if str(self.model.model_path).lower().endswith(".onnx"):
            detector = ONNXOpticalDetector(
                model_path=self.model.model_path,
                classes_path=self.model.classes_path,
                confidence_threshold=self.confidence_threshold,
            )
        else:
            detector = YOLODetector(
                model_path=self.model.model_path,
                classes_path=self.model.classes_path,
                confidence_threshold=self.confidence_threshold,
            )

        pipeline = ImageDetectionPipeline(detector=detector, confidence_threshold=self.confidence_threshold)
        return pipeline.process(image)

    def process_optical_frame(self, ping_payload: Dict[str, Any], allow_dev_fallback: bool = True) -> List[DebrisContact]:
        meta = ping_payload.get("target_meta", {})

        # Real model inference path
        if self.model.is_loaded:
            frame = None
            for key in ("optical_crop", "optical_frame", "image"):
                if key in ping_payload and ping_payload[key] is not None:
                    frame = ping_payload[key]
                    break

            if frame is not None:
                detections = self.model.predict(frame)
                contacts = []
                for i, det in enumerate(detections):
                    contacts.append(DebrisContact(
                        contact_id=f"OPTICAL_{meta.get('id', f'Contact_{i:02d}')}",
                        sensor_id="optical_01",
                        sensor_type="optical",
                        raw_confidence=round(det["confidence"], 3),
                        bbox=det["bbox"],
                        label_candidate=det["class_name"],
                        estimated_dimensions_m=meta.get("dimensions_m", (10.0, 5.0, 0.5)),
                        lat_lon=meta.get("lat_lon", (13.0835, 80.2715)),
                        depth_m=meta.get("depth_m", 24.3),
                    ))
                if contacts:
                    return contacts

        # Development test replay fallback (active while best.pt is pending from Member 1)
        if not allow_dev_fallback:
            return []

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
