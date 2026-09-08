"""
Unit Tests for Side-Scan Sonar Waterfall Processing Layer — Role 2: AI Inference & Integration

Validates:
1. Matrix input validation (2D, 3D, empty, NaN, Inf, invalid types)
2. CA-CFAR acoustic anomaly detection math and candidate extraction
3. Bounding box and confidence range invariants
4. Canonical Detection and DetectionResult schema serialization
5. Legacy 1D CA-CFAR row detector compatibility
6. DebrisContact fusion adapter compatibility
7. Side-scan waterfall annotation
8. MCP detect_side_scan_waterfall tool integration
9. FastAPI POST /detect/side-scan REST endpoint integration
"""

import io
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from marineguard.detection.side_scan import SideScanDetector
from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.pipeline import ImageValidationError
from marineguard.detection.model_loader import ModelNotFoundError
from marineguard.schemas import DebrisContact
from marineguard.mcp_server import MarineGuardMCPServer
from marineguard.api.app import app
from data.test_data.sample_frames import FrameReplayHarness


# ---------------------------------------------------------------------------
# 1. Input Validation Tests
# ---------------------------------------------------------------------------

def test_side_scan_valid_256x256_matrix():
    """Test 1: Valid 256x256 2D matrix produces structured DetectionResult."""
    detector = SideScanDetector()
    matrix = np.full((256, 256), 40, dtype=np.uint8)
    result = detector.detect_waterfall(matrix)

    assert isinstance(result, DetectionResult)
    assert result.status == "SUCCESS"
    assert result.image_width == 256
    assert result.image_height == 256
    assert result.inference_time_ms is not None and result.inference_time_ms >= 0


def test_side_scan_3d_input_handling():
    """Test 2: 3D single-channel (H, W, 1) and RGB (H, W, 3) arrays process cleanly."""
    detector = SideScanDetector()

    # (H, W, 1)
    mat_1ch = np.full((128, 128, 1), 50, dtype=np.float32)
    res_1ch = detector.detect_waterfall(mat_1ch)
    assert res_1ch.image_width == 128
    assert res_1ch.image_height == 128

    # (H, W, 3)
    mat_3ch = np.full((128, 128, 3), 50, dtype=np.uint8)
    res_3ch = detector.detect_waterfall(mat_3ch)
    assert res_3ch.image_width == 128
    assert res_3ch.image_height == 128


def test_side_scan_empty_input_fails():
    """Test 3: Empty numpy array and 0-byte input raise ImageValidationError."""
    detector = SideScanDetector()

    with pytest.raises(ImageValidationError):
        detector.detect_waterfall(np.array([]))

    with pytest.raises(ImageValidationError):
        detector.detect_waterfall(b"")


def test_side_scan_nan_input_fails():
    """Test 4: Input containing NaN values raises ImageValidationError."""
    detector = SideScanDetector()
    mat_nan = np.full((100, 100), 40.0, dtype=np.float32)
    mat_nan[50, 50] = np.nan

    with pytest.raises(ImageValidationError) as exc_info:
        detector.detect_waterfall(mat_nan)
    assert "nan" in str(exc_info.value).lower()


def test_side_scan_inf_input_fails():
    """Test 5: Input containing Inf values raises ImageValidationError."""
    detector = SideScanDetector()
    mat_inf = np.full((100, 100), 40.0, dtype=np.float32)
    mat_inf[20, 20] = np.inf

    with pytest.raises(ImageValidationError) as exc_info:
        detector.detect_waterfall(mat_inf)
    assert "inf" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 2. CA-CFAR Detection & Candidate Generation Tests
# ---------------------------------------------------------------------------

def test_side_scan_uniform_noise_zero_false_alarms():
    """Test 6: Uniform Gaussian noise background does not generate uncontrolled false detections."""
    detector = SideScanDetector(cfar_pfa=1e-4)
    np.random.seed(42)
    noise = np.random.normal(loc=40, scale=8, size=(256, 256)).astype(np.uint8)
    result = detector.detect_waterfall(noise)

    assert isinstance(result, DetectionResult)
    assert result.count == 0
    assert len(result.detections) == 0


def test_side_scan_synthetic_acoustic_spike_detection():
    """Test 7: Deterministic artificial highlight region is reliably bounded by CA-CFAR.

    NOTE: This is a software correctness unit test, not a claim of real-world model accuracy.
    """
    detector = SideScanDetector(cfar_pfa=1e-4, min_area=20)
    np.random.seed(42)
    mat = np.random.normal(loc=40, scale=8, size=(256, 256)).astype(np.uint8)

    # Inject artificial acoustic highlight at [100:150, 100:150]
    mat[100:150, 100:150] = np.random.normal(loc=220, scale=10, size=(50, 50)).astype(np.uint8)

    result = detector.detect_waterfall(mat)
    assert result.count >= 1

    # Verify candidate overlaps the injected highlight
    spike_det = result.detections[0]
    x1, y1, x2, y2 = spike_det.bbox
    assert x1 <= 120 and x2 >= 130
    assert y1 <= 120 and y2 >= 130
    assert spike_det.class_name == "unknown-object"
    assert spike_det.class_id == 27
    assert spike_det.confidence >= 0.50


def test_side_scan_bounding_box_validity():
    """Test 8: Invariant check that 0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H."""
    detector = SideScanDetector()
    np.random.seed(123)
    mat = np.random.normal(loc=40, scale=8, size=(200, 300)).astype(np.uint8)
    mat[60:100, 80:140] = 230

    result = detector.detect_waterfall(mat)
    for det in result.detections:
        x1, y1, x2, y2 = det.bbox
        assert 0 <= x1 < x2 <= 300
        assert 0 <= y1 < y2 <= 200


def test_side_scan_confidence_validity():
    """Test 9: Invariant check that anomaly confidence score satisfies 0.0 <= conf <= 1.0."""
    detector = SideScanDetector()
    mat = np.random.normal(loc=40, scale=8, size=(256, 256)).astype(np.uint8)
    mat[50:90, 50:90] = 240

    result = detector.detect_waterfall(mat)
    for det in result.detections:
        assert isinstance(det.confidence, float)
        assert 0.0 <= det.confidence <= 1.0


def test_side_scan_determinism():
    """Test 10: Identical waterfall matrix yields identical detections across multiple invocations."""
    detector = SideScanDetector()
    np.random.seed(999)
    mat = np.random.normal(loc=40, scale=8, size=(256, 256)).astype(np.uint8)
    mat[80:120, 80:120] = 225

    res1 = detector.detect_waterfall(mat)
    res2 = detector.detect_waterfall(mat)

    assert res1.count == res2.count
    assert len(res1.detections) == len(res2.detections)
    for d1, d2 in zip(res1.detections, res2.detections):
        assert d1.bbox == d2.bbox
        assert d1.confidence == d2.confidence
        assert d1.class_name == d2.class_name


def test_side_scan_canonical_schema_serialization():
    """Test 11: DetectionResult serializes cleanly to standard API dictionary."""
    detector = SideScanDetector()
    mat = np.random.normal(loc=40, scale=8, size=(256, 256)).astype(np.uint8)
    mat[100:140, 100:140] = 235

    result = detector.detect_waterfall(mat)
    api_dict = result.to_api_dict()

    assert "count" in api_dict
    assert "detections" in api_dict
    assert "image_width" in api_dict
    assert "image_height" in api_dict
    assert "inference_time_ms" in api_dict
    assert api_dict["count"] == len(api_dict["detections"])

    if api_dict["count"] > 0:
        det0 = api_dict["detections"][0]
        assert "class" in det0
        assert "confidence" in det0
        assert "bbox" in det0
        assert len(det0["bbox"]) == 4


# ---------------------------------------------------------------------------
# 3. Fusion Compatibility & Legacy Methods
# ---------------------------------------------------------------------------

def test_side_scan_legacy_cfar_detect_row():
    """Verify preserved 1D row CA-CFAR method works as expected."""
    detector = SideScanDetector(cfar_pfa=1e-3)
    row = np.full(100, 20.0, dtype=np.float32)
    row[50] = 200.0  # Spike

    anomalies = detector.cfar_detect(row, num_guard=4, num_ref=16)
    assert 50 in anomalies


def test_side_scan_process_waterfall_ping_fusion_compatibility():
    """Test 12: process_waterfall_ping produces valid DebrisContact objects for fusion."""
    detector = SideScanDetector()
    harness = FrameReplayHarness()
    ping = harness.get_next_ping()

    contacts = detector.process_waterfall_ping(ping)
    assert len(contacts) > 0
    c0 = contacts[0]
    assert isinstance(c0, DebrisContact)
    assert c0.sensor_type == "side_scan"
    assert c0.sensor_id == "side_scan_01"
    assert 0.0 <= c0.raw_confidence <= 1.0
    assert len(c0.bbox) == 4
    assert c0.depth_m > 0


# ---------------------------------------------------------------------------
# 4. Annotator & Interface Tests
# ---------------------------------------------------------------------------

def test_side_scan_annotator_rendering():
    """Test 13: SideScanDetector.annotate_waterfall renders PIL Image with bounding boxes."""
    detector = SideScanDetector()
    mat = np.random.normal(loc=40, scale=8, size=(256, 256)).astype(np.uint8)
    mat[100:140, 100:140] = 230

    annotated = detector.annotate_waterfall(mat)
    assert isinstance(annotated, Image.Image)
    assert annotated.size == (256, 256)


# ---------------------------------------------------------------------------
# 5. MCP & API Integration Tests
# ---------------------------------------------------------------------------

def test_mcp_detect_side_scan_waterfall_tool():
    """Test 14: MarineGuardMCPServer.detect_side_scan_waterfall MCP tool integration."""
    server = MarineGuardMCPServer()
    mat = np.random.normal(loc=40, scale=8, size=(256, 256)).astype(np.uint8)
    mat[80:130, 80:130] = 230

    # Test with raw numpy matrix
    res = server.detect_side_scan_waterfall(mat)
    assert res["status"] == "SUCCESS"
    assert "detections" in res
    assert res["image_width"] == 256
    assert res["image_height"] == 256

    # Test with invalid payload
    err_res = server.detect_side_scan_waterfall(b"not_an_image")
    assert err_res["status"] == "ERROR"
    assert err_res["error_type"] == "INVALID_IMAGE"


def test_api_detect_side_scan_endpoint():
    """Test 15: FastAPI POST /detect/side-scan REST endpoint integration."""
    img = Image.new("L", (256, 256), color=40)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    with TestClient(app) as client:
        response = client.post(
            "/detect/side-scan",
            files={"file": ("waterfall_frame.png", img_bytes, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert "count" in data
        assert data["image_width"] == 256
        assert data["image_height"] == 256

        # Test empty file rejection
        err_resp = client.post(
            "/detect/side-scan",
            files={"file": ("empty.png", b"", "image/png")},
        )
        assert err_resp.status_code == 400


# ---------------------------------------------------------------------------
# 6. SSS Specialist ML Model Integration Tests (PyTorch & ONNX)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
SSS_PT_PATH = REPO_ROOT / "runs" / "detect" / "runs" / "marineguard_sss_yolov8n_baseline" / "weights" / "best.pt"
SSS_ONNX_PATH = REPO_ROOT / "runs" / "detect" / "runs" / "marineguard_sss_yolov8n_baseline" / "weights" / "best.onnx"
SSS_VAL_IMAGE = REPO_ROOT / "data" / "processed" / "marineguard_sss" / "images" / "val" / "synth_ghost_net_00001.png"


def test_side_scan_with_sss_model_pt_loading():
    """Test 16: with_sss_model(use_onnx=False) loads PyTorch weights and reports ready."""
    assert SSS_PT_PATH.exists(), f"SSS PT weights missing at {SSS_PT_PATH}"
    detector = SideScanDetector.with_sss_model(use_onnx=False, confidence_threshold=0.50)
    assert detector.is_ready is True
    assert detector.is_model_loaded is True
    assert "best.pt" in detector.model_name


def test_side_scan_with_sss_model_onnx_loading():
    """Test 17: with_sss_model(use_onnx=True) loads ONNX weights and reports ready."""
    assert SSS_ONNX_PATH.exists(), f"SSS ONNX weights missing at {SSS_ONNX_PATH}"
    detector = SideScanDetector.with_sss_model(use_onnx=True, confidence_threshold=0.50)
    assert detector.is_ready is True
    assert detector.is_model_loaded is True
    assert "best.onnx" in detector.model_name


def test_side_scan_detect_sss_valid_image_pt():
    """Test 18: detect_sss() runs PT inference on a valid SSS image, mapping class 0 -> 29 ('net')."""
    assert SSS_VAL_IMAGE.exists(), f"SSS test image missing at {SSS_VAL_IMAGE}"
    detector = SideScanDetector.with_sss_model(use_onnx=False, confidence_threshold=0.25)
    result = detector.detect_sss(SSS_VAL_IMAGE)

    assert isinstance(result, DetectionResult)
    assert result.status == "SUCCESS"
    assert result.count >= 1
    assert result.image_width == 640
    assert result.image_height == 640
    assert result.inference_time_ms is not None and result.inference_time_ms > 0

    det = result.detections[0]
    assert det.class_id == 29
    assert det.class_name == "net"
    assert 0.0 <= det.confidence <= 1.0
    assert len(det.bbox) == 4
    x1, y1, x2, y2 = det.bbox
    assert 0 <= x1 < x2 <= result.image_width
    assert 0 <= y1 < y2 <= result.image_height
    assert det.metadata.get("sensor") == "side_scan"
    assert det.metadata.get("official_class_id") == 29


def test_side_scan_detect_sss_valid_image_onnx():
    """Test 19: detect_sss() runs ONNX inference on a valid SSS image with class mapping 0 -> 29 ('net')."""
    assert SSS_VAL_IMAGE.exists(), f"SSS test image missing at {SSS_VAL_IMAGE}"
    detector = SideScanDetector.with_sss_model(use_onnx=True, confidence_threshold=0.25)
    result = detector.detect_sss(SSS_VAL_IMAGE)

    assert isinstance(result, DetectionResult)
    assert result.status == "SUCCESS"
    assert result.count >= 1
    assert result.image_width == 640
    assert result.image_height == 640
    assert result.inference_time_ms is not None and result.inference_time_ms > 0

    det = result.detections[0]
    assert det.class_id == 29
    assert det.class_name == "net"
    assert 0.0 <= det.confidence <= 1.0
    assert len(det.bbox) == 4
    x1, y1, x2, y2 = det.bbox
    assert 0 <= x1 < x2 <= result.image_width
    assert 0 <= y1 < y2 <= result.image_height


def test_side_scan_detect_waterfall_use_ml_branching():
    """Test 20: detect_waterfall() switches cleanly between ML (use_ml=True) and CA-CFAR (use_ml=False)."""
    assert SSS_VAL_IMAGE.exists()
    detector = SideScanDetector.with_sss_model(confidence_threshold=0.25)

    # 1. ML path (returns class 29 'net')
    ml_result = detector.detect_waterfall(SSS_VAL_IMAGE, use_ml=True)
    assert ml_result.count >= 1
    assert ml_result.detections[0].class_id == 29
    assert ml_result.detections[0].class_name == "net"

    # 2. CA-CFAR path (returns class 27 'unknown-object' if anomalies found, or count 0)
    cfar_result = detector.detect_waterfall(SSS_VAL_IMAGE, use_ml=False)
    assert isinstance(cfar_result, DetectionResult)
    for det in cfar_result.detections:
        assert det.class_id == 27
        assert det.class_name == "unknown-object"


def test_side_scan_detect_sss_missing_model_raises():
    """Test 21: detect_sss() raises ModelNotFoundError if model weights are not loaded."""
    missing_path = REPO_ROOT / "models" / "definitely_missing_sss_model_99999.pt"
    detector = SideScanDetector(model_path=missing_path)
    assert detector.is_model_loaded is False

    with pytest.raises(ModelNotFoundError) as exc_info:
        detector.detect_sss(SSS_VAL_IMAGE)
    assert "not available" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()


def test_side_scan_detect_sss_invalid_inputs():
    """Test 22: detect_sss() validates inputs and raises ImageValidationError on invalid payloads."""
    detector = SideScanDetector.with_sss_model(use_onnx=False)

    # Empty bytes
    with pytest.raises(ImageValidationError):
        detector.detect_sss(b"")

    # Corrupt bytes
    with pytest.raises(ImageValidationError):
        detector.detect_sss(b"corrupted_bytes_not_an_image")

    # Non-existent file
    with pytest.raises(ImageValidationError):
        detector.detect_sss("non_existent_sss_file_12345.png")

    # Empty numpy array
    with pytest.raises(ImageValidationError):
        detector.detect_sss(np.array([]))

    # NaN in matrix
    mat_nan = np.full((100, 100), 50.0, dtype=np.float32)
    mat_nan[25, 25] = np.nan
    with pytest.raises(ImageValidationError):
        detector.detect_sss(mat_nan)

    # Inf in matrix
    mat_inf = np.full((100, 100), 50.0, dtype=np.float32)
    mat_inf[30, 30] = np.inf
    with pytest.raises(ImageValidationError):
        detector.detect_sss(mat_inf)


def test_side_scan_detect_sss_pil_and_numpy_inputs():
    """Test 23: detect_sss() supports PIL Image and 2D/3D numpy inputs."""
    detector = SideScanDetector.with_sss_model(use_onnx=False)

    # PIL Image
    pil_img = Image.open(SSS_VAL_IMAGE)
    res_pil = detector.detect_sss(pil_img)
    assert res_pil.status == "SUCCESS"
    assert res_pil.count >= 1

    # 3D NumPy array
    arr_3d = np.array(pil_img)
    res_3d = detector.detect_sss(arr_3d)
    assert res_3d.status == "SUCCESS"
    assert res_3d.count >= 1

    # 2D NumPy array
    arr_2d = np.array(pil_img.convert("L"))
    res_2d = detector.detect_sss(arr_2d)
    assert res_2d.status == "SUCCESS"


def test_side_scan_process_waterfall_ping_ml_support():
    """Test 24: process_waterfall_ping() supports use_ml=True with SSS specialist model."""
    detector = SideScanDetector.with_sss_model(use_onnx=False, confidence_threshold=0.25)
    pil_img = Image.open(SSS_VAL_IMAGE)
    arr = np.array(pil_img)

    ping_payload = {
        "sonar_waterfall": arr,
        "target_meta": {"id": "Ping_ML_01", "type": "net", "sonar_confidence": 0.95},
    }
    contacts = detector.process_waterfall_ping(ping_payload, use_ml=True)
    assert len(contacts) >= 1
    assert contacts[0].sensor_type == "side_scan"
    assert contacts[0].sensor_id == "side_scan_01"
    assert 0.0 <= contacts[0].raw_confidence <= 1.0
