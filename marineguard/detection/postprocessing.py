"""
Generic Detection Post-Processing for MarineGuard MCP — Role 2: AI Inference & Integration

Responsible for generic detector output normalization:
- Confidence filtering
- Bounding box boundary clipping and coordinate validation
- Filtering out degenerate / negative area bounding boxes
- Class ID to official taxonomy name mapping

Note: Does NOT perform Role 3's advanced false-positive filtering
(acoustic-shadow ratio heuristics or rock-vs-debris suppression).
"""

from typing import List, Dict, Any, Optional, Tuple
from marineguard.detection.schema import Detection, DetectionResult


class PostProcessor:
    """Standard post-processor for detector outputs."""

    def __init__(
        self,
        confidence_threshold: float = 0.50,
        min_box_size: float = 1.0,
        taxonomy: Optional[Dict[int, str]] = None,
    ):
        self.confidence_threshold = confidence_threshold
        self.min_box_size = min_box_size
        self.taxonomy = taxonomy or {}

    def clip_bbox(
        self,
        bbox: List[float],
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> Optional[List[float]]:
        """Validates and clips bounding box coordinates [x1, y1, x2, y2] to image bounds.

        Returns None if bounding box is degenerate or invalid.
        """
        if len(bbox) != 4:
            return None

        x1, y1, x2, y2 = bbox

        # Ensure correct min/max ordering
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)

        # Clip to image boundaries if dimensions provided
        if image_width is not None and image_width > 0:
            x_min = max(0.0, min(float(image_width), x_min))
            x_max = max(0.0, min(float(image_width), x_max))
        else:
            x_min = max(0.0, x_min)
            x_max = max(0.0, x_max)

        if image_height is not None and image_height > 0:
            y_min = max(0.0, min(float(image_height), y_min))
            y_max = max(0.0, min(float(image_height), y_max))
        else:
            y_min = max(0.0, y_min)
            y_max = max(0.0, y_max)

        width = x_max - x_min
        height = y_max - y_min

        # Check for minimum positive size
        if width < self.min_box_size or height < self.min_box_size:
            return None

        return [round(x_min, 2), round(y_min, 2), round(x_max, 2), round(y_max, 2)]

    def process(
        self,
        result: DetectionResult,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> DetectionResult:
        """Filters, clips, and standardizes raw detector result into a clean DetectionResult."""
        w = image_width if image_width is not None else result.image_width
        h = image_height if image_height is not None else result.image_height

        cleaned_detections: List[Detection] = []
        for det in result.detections:
            # 1. Confidence filtering
            if det.confidence < self.confidence_threshold:
                continue

            # 2. BBox clipping & validation
            valid_bbox = self.clip_bbox(det.bbox, image_width=w, image_height=h)
            if valid_bbox is None:
                continue

            # 3. Class name resolution from taxonomy if needed
            class_name = det.class_name
            if det.class_id is not None and det.class_id in self.taxonomy:
                class_name = self.taxonomy[det.class_id]

            cleaned_detections.append(
                Detection(
                    class_name=class_name,
                    class_id=det.class_id,
                    confidence=round(det.confidence, 4),
                    bbox=valid_bbox,
                    segmentation=det.segmentation,
                    metadata=det.metadata,
                )
            )

        return DetectionResult.from_detections(
            detections=cleaned_detections,
            image_width=w,
            image_height=h,
            inference_time_ms=result.inference_time_ms,
            model_name=result.model_name,
            status=result.status,
        )
