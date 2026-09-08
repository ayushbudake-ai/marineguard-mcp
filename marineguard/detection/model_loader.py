"""
Shared YOLO Model Loader for MarineGuard MCP — Role 2: AI Inference & Integration

Single place that loads the trained debris-detection model and exposes a
clean `.predict(image) -> list[dict]` call.

Consumes:
- models/best.pt (from Member 1)
- marineguard_classes.yaml (official 50-class taxonomy from Role 1)

When best.pt is absent:
- is_loaded is False
- Production inference fails clearly with ModelNotFoundError
- Callers and tests can verify readiness cleanly
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import threading
from ultralytics import YOLO
import yaml
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = REPO_ROOT / "models" / "best.pt"
DEFAULT_OPTICAL_ONNX_PATH = REPO_ROOT / "runs" / "seaclear_yolov8n_seg" / "onnx" / "best.onnx"
DEFAULT_CLASSES_PATH = REPO_ROOT / "marineguard_classes.yaml"


class ModelNotFoundError(FileNotFoundError):
    """Raised when production model weights (e.g. models/best.pt or ONNX export) are missing."""
    pass


class MarineDebrisModel:
    """Singleton/Instance wrapper around an Ultralytics YOLO model or ONNX export."""

    _instances: Dict[str, "MarineDebrisModel"] = {}
    _instance: Optional["MarineDebrisModel"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        classes_path: Optional[Union[str, Path]] = None,
        confidence_threshold: float = 0.50,
        task: Optional[str] = None,
    ):
        self.model_path = Path(model_path) if model_path is not None else DEFAULT_MODEL_PATH
        self.classes_path = Path(classes_path) if classes_path is not None else DEFAULT_CLASSES_PATH
        self.confidence_threshold = confidence_threshold
        self.task = task
        self.model = None
        self.class_names: Dict[int, str] = {}

        self.load_taxonomy()
        self.load_weights()

    def load_taxonomy(self) -> Dict[int, str]:
        """Loads the official class taxonomy from marineguard_classes.yaml."""
        if self.classes_path.exists():
            try:
                with open(self.classes_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    raw_classes = data.get("classes", {})
                    # Ensure keys are integer class IDs
                    self.class_names = {int(k): str(v) for k, v in raw_classes.items()}
            except Exception as exc:
                print(f"[model_loader] Warning: Failed to parse taxonomy at {self.classes_path}: {exc}")
                self.class_names = {}
        return self.class_names

    def load_weights(self) -> bool:
        """Attempts to load the YOLO model or ONNX runtime session if weights exist on disk."""
        if self.model_path.exists():
            try:
                from ultralytics import YOLO
                if self.model_path.suffix.lower() == ".onnx":
                    if self.task is not None:
                        self.model = YOLO(str(self.model_path), task=self.task)
                    else:
                        self.model = YOLO(str(self.model_path))
                else:
                    self.model = YOLO(str(self.model_path))
                return True
            except Exception as exc:
                print(f"[model_loader] Found {self.model_path} but failed to load it: {exc}")
                self.model = None
                return False
        self.model = None
        return False

    @classmethod
    def get(
        cls,
        model_path: Optional[Union[str, Path]] = None,
        confidence_threshold: float = 0.50,
        **kwargs,
    ) -> "MarineDebrisModel":
        """Process-wide singleton / keyed instance so detectors share the loaded weights."""
        with cls._lock:
            task = kwargs.get("task")
            key = (
                f"{str(model_path) if model_path is not None else 'default'}"
                f"_{confidence_threshold}_{task}"
            )
            if key not in cls._instances:
                instance = cls(
                    model_path=model_path,
                    confidence_threshold=confidence_threshold,
                    **kwargs,
                )
                cls._instances[key] = instance
                if cls._instance is None:
                    cls._instance = instance
            return cls._instances[key]

    @classmethod
    def reset_singleton(cls):
        """Reset singleton instances (useful for testing)."""
        with cls._lock:
            cls._instances.clear()
            cls._instance = None

    @property
    def is_loaded(self) -> bool:
        """Returns True only when the real model weights are loaded in memory."""
        return self.model is not None

    def predict(
        self,
        image: Any,
        imgsz: int = 512,
        device: Optional[Union[int, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Runs inference on an image input (numpy array, PIL image, or path).

        Args:
            image: Input image (numpy array, PIL image, file path, or bytes).
            imgsz: Input image size for the model (default: 512).
            device: Compute device override. ONNX always uses CPU regardless.

        Returns:
            List[Dict[str, Any]]: List of detection dicts:
                {
                    "class_name": str,
                    "class_id": int,
                    "confidence": float,
                    "bbox": (x1, y1, x2, y2),
                    "segmentation": Optional[List[List[float]]]
                }

        Raises:
            ModelNotFoundError: If production model is not loaded.
        """
        if self.model is None:
            raise ModelNotFoundError(
                f"Trained model not found at {self.model_path}. "
                f"Please ensure best.onnx or best.pt is placed in expected directories."
            )

        if self.model_path.suffix.lower() == ".onnx":
            results = self.model.predict(
                image,
                imgsz=imgsz,
                rect=False,
                conf=self.confidence_threshold,
                device="cpu",
                verbose=False,
            )
        else:
            predict_kwargs = {
                "imgsz": imgsz,
                "rect": False,
                "conf": self.confidence_threshold,
                "verbose": False,
            }
            if device is not None:
                predict_kwargs["device"] = device
            results = self.model.predict(image, **predict_kwargs)
        detections = []
        for r in results:
            if r.boxes is None:
                continue
            for i, box in enumerate(r.boxes):
                cls_id = int(box.cls.item())
                class_name = self.class_names.get(cls_id, f"class_{cls_id}")
                det: Dict[str, Any] = {
                    "class_name": class_name,
                    "class_id": cls_id,
                    "confidence": float(box.conf.item()),
                    "bbox": tuple(box.xyxy[0].tolist()),
                }
                # Optional segmentation polygons if available
                if getattr(r, "masks", None) is not None and r.masks is not None:
                    try:
                        if hasattr(r.masks, "xy") and r.masks.xy is not None and i < len(r.masks.xy):
                            poly = r.masks.xy[i].tolist()
                            if poly and len(poly) >= 3:
                                det["segmentation"] = poly
                    except Exception:
                        pass
                detections.append(det)
        return detections
