"""
Unit Tests for MarineGuard MCP Debris Detection Tool Integration
"""

import io
import base64
import pytest
from PIL import Image

from marineguard.mcp_server import MarineGuardMCPServer
from marineguard.detection.pipeline import ImageDetectionPipeline
from marineguard.detection.detector import MockDetector, YOLODetector


def create_test_image_bytes(format="PNG", size=(320, 240)) -> bytes:
    img = Image.new("RGB", size, color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_mcp_detect_marine_debris_success():
    mock_detector = MockDetector(
        mock_detections=[
            {"class": "plastic-bottle", "confidence": 0.93, "bbox": [100.0, 100.0, 200.0, 250.0]},
            {"class": "can", "confidence": 0.87, "bbox": [50.0, 50.0, 90.0, 90.0]},
        ]
    )
    pipeline = ImageDetectionPipeline(detector=mock_detector)
    server = MarineGuardMCPServer(detection_pipeline=pipeline)

    img_bytes = create_test_image_bytes()
    res = server.detect_marine_debris(img_bytes)

    assert res["status"] == "SUCCESS"
    assert res["count"] == 2
    assert len(res["detections"]) == 2
    assert res["detections"][0]["class"] == "plastic-bottle"
    assert res["detections"][0]["confidence"] == 0.93
    assert res["detections"][1]["class"] == "can"


def test_mcp_detect_base64_encoded_image():
    mock_detector = MockDetector(
        mock_detections=[
            {"class": "tire", "confidence": 0.89, "bbox": [10.0, 10.0, 100.0, 100.0]}
        ]
    )
    pipeline = ImageDetectionPipeline(detector=mock_detector)
    server = MarineGuardMCPServer(detection_pipeline=pipeline)

    img_bytes = create_test_image_bytes()
    b64_str = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")

    res = server.detect_marine_debris(b64_str)
    assert res["status"] == "SUCCESS"
    assert res["count"] == 1
    assert res["detections"][0]["class"] == "tire"


def test_mcp_detect_invalid_image_error():
    mock_detector = MockDetector()
    pipeline = ImageDetectionPipeline(detector=mock_detector)
    server = MarineGuardMCPServer(detection_pipeline=pipeline)

    res = server.detect_marine_debris(b"corrupted_non_image_payload")
    assert res["status"] == "ERROR"
    assert res["error_type"] == "INVALID_IMAGE"
    assert res["count"] == 0
    assert res["detections"] == []


def test_mcp_detect_missing_model_error():
    # Production YOLO detector when best.pt does not exist
    pipeline = ImageDetectionPipeline(detector=YOLODetector(model_path="models/non_existent_best.pt"))
    server = MarineGuardMCPServer(detection_pipeline=pipeline)

    img_bytes = create_test_image_bytes()
    res = server.detect_marine_debris(img_bytes)

    assert res["status"] == "MODEL_UNAVAILABLE"
    assert res["error_type"] == "MODEL_NOT_FOUND"
    assert "best.pt" in res["message"]
    assert res["count"] == 0
    assert res["detections"] == []
