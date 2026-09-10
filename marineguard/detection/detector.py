"""
Detector Service Interface & Implementations for MarineGuard MCP — Role 2

Provides a clean abstraction decoupling the rest of the application
from YOLO / Ultralytics implementation details:

    BaseDetector (ABC)
    ├── YOLODetector (Production: requires models/best.pt when Member 1 delivers)
    └── MockDetector (Testing/Mocking: predictable fixtures for unit tests)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import time
import numpy as np

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.model_loader import MarineDebrisModel, ModelNotFoundError


class BaseDetector(ABC):
    """Abstract interface for all marine debris detectors."""

    @abstractmethod
    def detect(self, image: np.ndarray) -> DetectionResult:
        """Runs inference on a preprocessed numpy image array [H, W, C] or [H, W].

        Returns:
            DetectionResult: Structured detection container.
        """
        pass

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Whether detector weights/model are successfully loaded and ready for inference."""
        pass

    @property
    def model_name(self) -> str:
        """Identifier name of the detector."""
        return self.__class__.__name__


class YOLODetector(BaseDetector):
    """Production YOLO / ONNX Detector.

    Consumes verified model weights (e.g. runs/seaclear_yolov8n_seg/onnx/best.onnx or models/best.pt)
    and official marineguard_classes.yaml.
    Fails clearly if model weights are unavailable when production inference is invoked.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        classes_path: Optional[Union[str, Path]] = None,
        confidence_threshold: float = 0.50,
        iou_threshold: float = 0.45,
    ):
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.model_loader = MarineDebrisModel.get(
            model_path=model_path,
            classes_path=classes_path,
            confidence_threshold=confidence_threshold,
        )

    @property
    def is_ready(self) -> bool:
        return self.model_loader.is_loaded

    @property
    def model_name(self) -> str:
        return f"YOLODetector({self.model_loader.model_path.name})"

    def detect(self, image: np.ndarray) -> DetectionResult:
        """Executes YOLO/ONNX inference on an image array.

        Raises:
            ModelNotFoundError: If production model weights are not loaded.
        """
        if not self.is_ready:
            raise ModelNotFoundError(
                f"Production YOLO/ONNX model is not available at '{self.model_loader.model_path}'. "
                f"Trained weights must be provided before running real inference. "
                f"(Use MockDetector for unit tests)."
            )

        start_time = time.perf_counter()
        raw_detections = self.model_loader.predict(image)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        h, w = image.shape[:2] if hasattr(image, "shape") and len(image.shape) >= 2 else (512, 512)
        detections: List[Detection] = []
        for raw in raw_detections:
            detections.append(
                Detection(
                    class_name=raw["class_name"],
                    class_id=raw.get("class_id"),
                    confidence=raw["confidence"],
                    bbox=list(raw["bbox"]),
                    segmentation=raw.get("segmentation"),
                    metadata={"source_sensor": raw.get("sensor", "optical_or_sonar")},
                )
            )

        return DetectionResult.from_detections(
            detections=detections,
            image_width=w,
            image_height=h,
            inference_time_ms=latency_ms,
            model_name=self.model_name,
        )


class ONNXOpticalDetector(BaseDetector):
    """Dedicated Optical ONNX Instance Segmentation Detector.

    Consumes the verified YOLOv8n-seg ONNX model (runs/seaclear_yolov8n_seg/onnx/best.onnx)
    and official marineguard_classes.yaml.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        classes_path: Optional[Union[str, Path]] = None,
        confidence_threshold: float = 0.50,
        iou_threshold: float = 0.45,
    ):
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        repo_root = Path(__file__).resolve().parents[2]
        target_path = Path(model_path) if model_path is not None else (
            repo_root / "runs" / "seaclear_yolov8n_seg" / "onnx" / "best.onnx"
        )
        self.model_loader = MarineDebrisModel.get(
            model_path=target_path,
            classes_path=classes_path,
            confidence_threshold=confidence_threshold,
            task="segment",
        )

    @property
    def is_ready(self) -> bool:
        return self.model_loader.is_loaded

    @property
    def model_name(self) -> str:
        return f"ONNXOpticalDetector({self.model_loader.model_path.name})"

    def detect(self, image: np.ndarray) -> DetectionResult:
        """Executes ONNX segmentation inference on an image array."""
        if not self.is_ready:
            raise ModelNotFoundError(
                f"ONNX optical segmentation model not available at '{self.model_loader.model_path}'."
            )

        start_time = time.perf_counter()
        raw_detections = self.model_loader.predict(image)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        h, w = image.shape[:2] if hasattr(image, "shape") and len(image.shape) >= 2 else (512, 512)
        detections: List[Detection] = []
        for raw in raw_detections:
            detections.append(
                Detection(
                    class_name=raw["class_name"],
                    class_id=raw.get("class_id"),
                    confidence=raw["confidence"],
                    bbox=list(raw["bbox"]),
                    segmentation=raw.get("segmentation"),
                    metadata={"source_sensor": "optical", "engine": "onnxruntime"},
                )
            )

        return DetectionResult.from_detections(
            detections=detections,
            image_width=w,
            image_height=h,
            inference_time_ms=latency_ms,
            model_name=self.model_name,
        )


class MockDetector(BaseDetector):
    """Test double detector for unit tests, API tests, and MCP tool tests.

    Never presented as real model output; strictly used to verify
    pipelines and integrations in the absence of trained weights.
    """

    def __init__(
        self,
        mock_detections: Optional[List[Dict[str, Any]]] = None,
        latency_ms: float = 5.0,
        model_name: str = "MockDetector",
        simulated_ready: bool = True,
    ):
        self._mock_detections = mock_detections if mock_detections is not None else []
        self._latency_ms = latency_ms
        self._model_name = model_name
        self._simulated_ready = simulated_ready

    @property
    def is_ready(self) -> bool:
        return self._simulated_ready

    @property
    def model_name(self) -> str:
        return self._model_name

    def set_mock_detections(self, detections: List[Dict[str, Any]]):
        """Configure mock detections for subsequent test calls."""
        self._mock_detections = detections

    def set_ready(self, ready: bool):
        """Simulate ready or not ready state."""
        self._simulated_ready = ready

    def detect(self, image: np.ndarray) -> DetectionResult:
        if not self._simulated_ready:
            raise ModelNotFoundError("Mock detector configured in NOT READY state for testing.")

        h, w = image.shape[:2] if hasattr(image, "shape") else (480, 640)
        detections: List[Detection] = []
        for raw in self._mock_detections:
            detections.append(
                Detection(
                    class_name=raw.get("class", raw.get("class_name", "plastic-bottle")),
                    class_id=raw.get("class_id", 0),
                    confidence=raw.get("confidence", 0.90),
                    bbox=list(raw.get("bbox", [100.0, 100.0, 200.0, 200.0])),
                    segmentation=raw.get("segmentation"),
                    metadata={"mock": True},
                )
            )

        return DetectionResult.from_detections(
            detections=detections,
            image_width=w,
            image_height=h,
            inference_time_ms=self._latency_ms,
            model_name=self._model_name,
        )
