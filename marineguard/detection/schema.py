"""
Structured Detection Schema for MarineGuard MCP — Role 2: AI Inference & Integration

Defines standard dataclass/Pydantic schemas for object detection results,
hiding YOLO/underlying model implementation details from callers.
"""

from typing import List, Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class Detection(BaseModel):
    """Represents a single detected object."""
    model_config = ConfigDict(populate_by_name=True)

    class_name: str = Field(..., description="Canonical class name from official taxonomy", alias="class")
    class_id: Optional[int] = Field(default=None, description="Numeric class index from taxonomy")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    bbox: List[float] = Field(..., min_length=4, max_length=4, description="Bounding box [x1, y1, x2, y2] in pixel coordinates")
    segmentation: Optional[List[List[float]]] = Field(default=None, description="Optional polygon contour coordinates if supported by segmentation model")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional detector or sensor metadata")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard dictionary with 'class' key."""
        d: Dict[str, Any] = {
            "class": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": [round(coord, 2) for coord in self.bbox],
        }
        if self.class_id is not None:
            d["class_id"] = self.class_id
        if self.segmentation is not None:
            d["segmentation"] = self.segmentation
        if self.metadata:
            d["metadata"] = self.metadata
        return d


class DetectionResult(BaseModel):
    """Structured response container for image/frame detection."""
    detections: List[Detection] = Field(default_factory=list, description="List of detected objects")
    count: int = Field(default=0, description="Total count of detected objects")
    image_width: Optional[int] = Field(default=None, description="Input image width in pixels")
    image_height: Optional[int] = Field(default=None, description="Input image height in pixels")
    inference_time_ms: Optional[float] = Field(default=None, description="Inference latency in milliseconds")
    model_name: Optional[str] = Field(default=None, description="Model identifier used for inference")
    status: str = Field(default="SUCCESS", description="Execution status")

    @classmethod
    def from_detections(
        cls,
        detections: List[Detection],
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
        inference_time_ms: Optional[float] = None,
        model_name: Optional[str] = None,
        status: str = "SUCCESS",
    ) -> "DetectionResult":
        """Convenience constructor that automatically synchronizes count."""
        return cls(
            detections=detections,
            count=len(detections),
            image_width=image_width,
            image_height=image_height,
            inference_time_ms=inference_time_ms,
            model_name=model_name,
            status=status,
        )

    def to_api_dict(self) -> Dict[str, Any]:
        """Converts to the standard project API response format:
        {
            "detections": [
                { "class": "plastic-bottle", "confidence": 0.91, "bbox": [120, 80, 240, 310] }
            ],
            "count": 1
        }
        """
        res: Dict[str, Any] = {
            "detections": [d.to_dict() for d in self.detections],
            "count": len(self.detections),
        }
        if self.image_width is not None and self.image_height is not None:
            res["image_width"] = self.image_width
            res["image_height"] = self.image_height
        if self.inference_time_ms is not None:
            res["inference_time_ms"] = round(self.inference_time_ms, 2)
        return res
