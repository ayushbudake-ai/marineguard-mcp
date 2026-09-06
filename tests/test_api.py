"""
API Tests for MarineGuard REST /detect Service
"""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from marineguard.api.app import app, get_pipeline
from marineguard.detection.pipeline import ImageDetectionPipeline
from marineguard.detection.detector import MockDetector, YOLODetector


def create_test_image_bytes(format="PNG", size=(640, 480)) -> bytes:
    """Helper to create valid in-memory image bytes."""
    img = Image.new("RGB", size, color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.fixture
def client_with_mock():
    """TestClient fixture with injected MockDetector returning a valid detection."""
    mock_detector = MockDetector(
        mock_detections=[
            {"class": "plastic-bottle", "confidence": 0.91, "bbox": [120.0, 80.0, 240.0, 310.0]}
        ]
    )
    mock_pipeline = ImageDetectionPipeline(detector=mock_detector)
    app.dependency_overrides[get_pipeline] = lambda: mock_pipeline

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client_with_empty_mock():
    """TestClient fixture with injected MockDetector returning 0 detections."""
    mock_detector = MockDetector(mock_detections=[])
    mock_pipeline = ImageDetectionPipeline(detector=mock_detector)
    app.dependency_overrides[get_pipeline] = lambda: mock_pipeline

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client_with_unloaded_yolo():
    """TestClient fixture with real YOLODetector when best.pt is absent."""
    pipeline = ImageDetectionPipeline(detector=YOLODetector(model_path="models/non_existent_best.pt"))
    app.dependency_overrides[get_pipeline] = lambda: pipeline

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_api_health_endpoint(client_with_mock):
    response = client_with_mock.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["model_loaded"] is True


def test_api_classes_endpoint(client_with_mock):
    response = client_with_mock.get("/classes")
    assert response.status_code == 200
    data = response.json()
    assert "classes" in data
    assert data["total_classes"] > 0


def test_api_detect_valid_image(client_with_mock):
    img_bytes = create_test_image_bytes(size=(640, 480))
    response = client_with_mock.post(
        "/detect",
        files={"file": ("test_frame.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    # Verify structured detection schema contract
    assert "detections" in data
    assert "count" in data
    assert data["count"] == 1

    first_det = data["detections"][0]
    assert first_det["class"] == "plastic-bottle"
    assert first_det["confidence"] == 0.91
    assert first_det["bbox"] == [120.0, 80.0, 240.0, 310.0]


def test_api_detect_empty_detections(client_with_empty_mock):
    img_bytes = create_test_image_bytes()
    response = client_with_empty_mock.post(
        "/detect",
        files={"file": ("clean_seafloor.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["detections"] == []


def test_api_detect_invalid_file(client_with_mock):
    # Send corrupted non-image content
    response = client_with_mock.post(
        "/detect",
        files={"file": ("corrupted.png", b"this_is_not_an_image", "image/png")},
    )
    assert response.status_code == 400
    assert "Invalid image" in response.json()["detail"]


def test_api_detect_empty_file(client_with_mock):
    # Send 0-byte file
    response = client_with_mock.post(
        "/detect",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_api_detect_missing_model_error(client_with_unloaded_yolo):
    # Send valid image when production model is absent
    img_bytes = create_test_image_bytes()
    response = client_with_unloaded_yolo.post(
        "/detect",
        files={"file": ("frame.png", img_bytes, "image/png")},
    )
    assert response.status_code == 503
    assert "Model unavailable" in response.json()["detail"]
