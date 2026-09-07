"""
FastAPI REST Service for MarineGuard MCP — Role 2: AI Inference & Integration

Exposes HTTP endpoints for debris detection:
- POST /detect: Upload image frame -> returns structured JSON detections
- GET /health: Status of model readiness & system health
- GET /classes: List of official taxonomy classes
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Query, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from marineguard.detection.pipeline import ImageDetectionPipeline, ImageValidationError
from marineguard.detection.detector import BaseDetector, YOLODetector
from marineguard.detection.side_scan import SideScanDetector
from marineguard.detection.model_loader import ModelNotFoundError, MarineDebrisModel

app = FastAPI(
    title="MarineGuard Detection API",
    description="REST API for underwater and sonar marine debris detection (Role 2)",
    version="1.0.0",
)

# CORS middleware for web clients / dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance (can be swapped in tests via app.state or dependency override)
_default_pipeline: Optional[ImageDetectionPipeline] = None


def get_pipeline() -> ImageDetectionPipeline:
    """Dependency provider for ImageDetectionPipeline."""
    global _default_pipeline
    if getattr(app.state, "pipeline", None) is not None:
        return app.state.pipeline
    if _default_pipeline is None:
        _default_pipeline = ImageDetectionPipeline()
    return _default_pipeline


@app.get("/health")
async def health_check(pipeline: ImageDetectionPipeline = Depends(get_pipeline)) -> Dict[str, Any]:
    """Returns service health and model readiness status."""
    is_ready = pipeline.detector.is_ready
    return {
        "status": "HEALTHY",
        "model_name": pipeline.detector.model_name,
        "model_loaded": is_ready,
        "mode": "PRODUCTION" if is_ready else "PENDING_MEMBER_1_MODEL",
        "message": (
            "Model ready for inference."
            if is_ready
            else "Ready for Member 1 model (models/best.pt not yet placed in repository)."
        ),
    }


@app.get("/classes")
async def get_classes() -> Dict[str, Any]:
    """Returns the official 50-class taxonomy loaded from marineguard_classes.yaml."""
    model_loader = MarineDebrisModel.get()
    return {
        "total_classes": len(model_loader.class_names),
        "classes": model_loader.class_names,
    }


@app.post("/detect", status_code=status.HTTP_200_OK)
async def detect_image(
    file: UploadFile = File(..., description="Image file (JPG, PNG, BMP, etc.) to run detection on"),
    confidence: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Optional confidence threshold override"),
    pipeline: ImageDetectionPipeline = Depends(get_pipeline),
) -> Dict[str, Any]:
    """Accepts an uploaded image file and returns structured marine debris detections.

    Expected standard response schema:
    {
        "detections": [
            { "class": "plastic-bottle", "confidence": 0.91, "bbox": [120, 80, 240, 310] }
        ],
        "count": 1
    }
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {exc}",
        )

    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # Adjust confidence threshold if specified
    if confidence is not None:
        pipeline.postprocessor.confidence_threshold = confidence

    try:
        result = pipeline.process(content)
        return result.to_api_dict()

    except ImageValidationError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image: {str(val_err)}",
        )
    except ModelNotFoundError as model_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model unavailable: {str(model_err)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(exc)}",
        )


@app.post("/detect/side-scan", status_code=status.HTTP_200_OK)
async def detect_side_scan_waterfall_api(
    file: UploadFile = File(..., description="Side-scan sonar waterfall image file (PNG, JPG, BMP, TIFF)"),
    confidence: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Optional confidence threshold override"),
    cfar_pfa: Optional[float] = Query(default=1e-4, ge=1e-8, le=0.1, description="CFAR Probability of False Alarm"),
) -> Dict[str, Any]:
    """Accepts an uploaded side-scan sonar waterfall image and returns CA-CFAR acoustic anomaly detections."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {exc}",
        )

    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    detector = SideScanDetector()
    try:
        result = detector.detect_waterfall(
            content,
            confidence_threshold=confidence,
            cfar_pfa=cfar_pfa,
        )
        return result.to_api_dict()

    except ImageValidationError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid waterfall image: {str(val_err)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Side-scan inference error: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
