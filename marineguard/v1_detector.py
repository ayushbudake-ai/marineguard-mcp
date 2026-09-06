from pathlib import Path
from typing import Any, Dict, List

from ultralytics import YOLO


class MarineGuardV1Detector:
    """Real MarineGuard V1 YOLO object detector."""

    MODEL_VERSION = "v1"
    IMAGE_SIZE = 512

    def __init__(self, model_path: str | Path | None = None):
        repo_root = Path(__file__).resolve().parents[1]

        self.model_path = Path(
            model_path
            if model_path is not None
            else repo_root / "runs" / "marineguard_full_512_b16-2" / "weights" / "best.pt"
        )

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"MarineGuard V1 model not found: {self.model_path}"
            )

        self.model = YOLO(str(self.model_path))

    def predict(
        self,
        image_path: str | Path,
        confidence: float = 0.25,
    ) -> Dict[str, Any]:

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")

        results = self.model.predict(
            source=str(image_path),
            imgsz=self.IMAGE_SIZE,
            conf=confidence,
            verbose=False,
        )

        result = results[0]
        detections = []

        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = [float(x) for x in box.xyxy[0]]

            detections.append(
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(conf, 4),
                    "bbox": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                    },
                }
            )

        return {
            "frame_id": image_path.stem,
            "model_version": self.MODEL_VERSION,
            "detections": detections,
        }

    def predict_batch(
        self,
        image_paths: List[str | Path],
        confidence: float = 0.25,
    ) -> List[Dict[str, Any]]:
        """Run V1 inference on multiple images."""

        results = []

        for image_path in image_paths:
            results.append(
                self.predict(
                    image_path,
                    confidence=confidence,
                )
            )

        return results
