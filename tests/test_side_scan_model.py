"""
SSS YOLO Side-Scan Model Integration Tests

Validates the Role 2 SSS inference integration without modifying the
frozen V1 detector or MarineGuard global taxonomy.
"""

import numpy as np
import pytest

from marineguard.detection.side_scan import SideScanDetector
from marineguard.detection.model_loader import MarineDebrisModel
from marineguard.detection.schema import DetectionResult


from pathlib import Path

_EXP2_ONNX = Path("runs/detect/runs/detect/marineguard_sss_yolov8n_exp2_augmented/weights/best.onnx")
_BASELINE_ONNX = Path("runs/detect/runs/marineguard_sss_yolov8n_baseline/weights/best.onnx")

SSS_MODEL_PATH = str(_EXP2_ONNX if _EXP2_ONNX.exists() else _BASELINE_ONNX)

SSS_TEST_IMAGE = (
    "data/processed/marineguard_sss/images/test/"
    "synth_ghost_net_00001.png"
)


@pytest.fixture
def sss_model():
    """Load the current engineering/test SSS ONNX checkpoint."""
    MarineDebrisModel.reset_singleton()

    model = MarineDebrisModel.get(
        model_path=SSS_MODEL_PATH,
        confidence_threshold=0.01,
    )

    if not model.is_loaded:
        pytest.skip("SSS ONNX model is not available")

    return model


@pytest.fixture
def sss_image():
    """Load the controlled SSS test image."""
    from PIL import Image

    image = Image.open(SSS_TEST_IMAGE).convert("L")
    return np.array(image)


def test_sss_model_loads(sss_model):
    """SSS ONNX model must load successfully."""
    assert sss_model.is_loaded is True


def test_sss_model_missing_file_returns_unloaded():
    """Missing SSS model must not be reported as loaded."""
    MarineDebrisModel.reset_singleton()

    model = MarineDebrisModel.get(
        model_path="runs/detect/does_not_exist/best.onnx",
        confidence_threshold=0.01,
    )

    assert model.is_loaded is False


def test_sss_valid_image_produces_detection(sss_model, sss_image):
    """Controlled SSS image must pass through the integrated detector."""
    detector = SideScanDetector(
        model=sss_model,
        use_sss_model=True,
        confidence_threshold=0.01,
    )

    result = detector.detect(sss_image)

    assert isinstance(result, DetectionResult)
    assert result.status == "ok"
    assert result.image_width == 640
    assert result.image_height == 640
    assert result.count >= 1


def test_sss_detection_uses_marineguard_net_class(
    sss_model,
    sss_image,
):
    """SSS native class 0 must map to MarineGuard class 29 net."""
    detector = SideScanDetector(
        model=sss_model,
        use_sss_model=True,
        confidence_threshold=0.01,
    )

    result = detector.detect(sss_image)

    assert result.status == "ok"
    assert result.count >= 1

    for detection in result.detections:
        assert detection.class_id == 29
        assert detection.class_name == "net"
        assert detection.metadata["method"] == "SSS-YOLO"
        assert detection.metadata["native_class_id"] == 0


def test_sss_detection_fields_are_valid(sss_model, sss_image):
    """SSS detections must satisfy the canonical Detection contract."""
    detector = SideScanDetector(
        model=sss_model,
        use_sss_model=True,
        confidence_threshold=0.01,
    )

    result = detector.detect(sss_image)

    assert result.status == "ok"

    for detection in result.detections:
        assert isinstance(detection.class_id, int)
        assert detection.class_id == 29

        assert detection.class_name == "net"

        assert isinstance(detection.confidence, float)
        assert 0.0 <= detection.confidence <= 1.0

        assert len(detection.bbox) == 4

        x1, y1, x2, y2 = detection.bbox

        assert 0 <= x1 < x2 <= result.image_width
        assert 0 <= y1 < y2 <= result.image_height


def test_sss_detection_result_serializes_to_api(
    sss_model,
    sss_image,
):
    """SSS DetectionResult must remain API-compatible."""
    detector = SideScanDetector(
        model=sss_model,
        use_sss_model=True,
        confidence_threshold=0.01,
    )

    result = detector.detect(sss_image)
    api_result = result.to_api_dict()

    assert result.status == "ok"
    assert "detections" in api_result
    assert "count" in api_result
    assert "image_width" in api_result
    assert "image_height" in api_result
    assert "inference_time_ms" in api_result

    assert api_result["count"] == len(api_result["detections"])

    for detection in api_result["detections"]:
        assert detection["class"] == "net"
        assert detection["class_id"] == 29
        assert 0.0 <= detection["confidence"] <= 1.0
        assert len(detection["bbox"]) == 4


def test_sss_empty_input_is_rejected(sss_model):
    """Empty SSS input must not produce a successful detection."""
    detector = SideScanDetector(
        model=sss_model,
        use_sss_model=True,
        confidence_threshold=0.01,
    )

    empty = np.array([])

    result = detector.detect(empty)

    assert result.status.startswith("error:")
    assert result.count == 0


def test_sss_invalid_dimensions_are_rejected(sss_model):
    """Unsupported input dimensions must not reach SSS inference."""
    detector = SideScanDetector(
        model=sss_model,
        use_sss_model=True,
        confidence_threshold=0.01,
    )

    invalid = np.zeros((10, 10, 2), dtype=np.uint8)

    result = detector.detect(invalid)

    assert result.status.startswith("error:")
    assert result.count == 0


def test_sss_background_produces_no_detection(sss_model):
    """
    Controlled background image should produce zero detections.

    This is a regression test for the controlled input only and is not
    a claim of real-world SSS false-positive performance.
    """
    from PIL import Image

    background_path = (
        "data/processed/marineguard_sss/images/test/"
        "bg_1693569243.750_x2500.jpg"
    )

    image = Image.open(background_path).convert("L")
    background = np.array(image)

    detector = SideScanDetector(
        model=sss_model,
        use_sss_model=True,
        confidence_threshold=0.01,
    )

    result = detector.detect(background)

    assert result.status == "ok"
    assert result.count == 0


def test_cfar_default_path_remains_separate():
    """
    Default SideScanDetector behavior must remain CA-CFAR and must not
    silently switch to SSS YOLO.
    """
    detector = SideScanDetector()

    matrix = np.full((256, 256), 40, dtype=np.uint8)

    result = detector.detect(matrix)

    assert isinstance(result, DetectionResult)

    for detection in result.detections:
        assert detection.class_id == 27
        assert detection.class_name == "unknown-object"


def test_sss_model_can_be_explicitly_enabled(sss_model, sss_image):
    """SSS inference must be explicitly enabled."""
    detector = SideScanDetector(
        model=sss_model,
        use_sss_model=False,
        confidence_threshold=0.01,
    )

    result = detector.detect(sss_image)

    assert isinstance(result, DetectionResult)

    for detection in result.detections:
        assert detection.metadata.get("method") != "SSS-YOLO"