"""
Role 3 Production Pipeline Integration Tests
tests/test_role3_production_integration.py

Comprehensive test suite verifying:
- TEST A: Empty detections
- TEST B: Valid detection acceptance and calibrated score
- TEST C: Low confidence rejection (LOW_CONFIDENCE)
- TEST D: Zero area rejection (ZERO_AREA_BBOX)
- TEST E: Invalid bbox rejection (INVALID_BBOX)
- TEST F: Out of bounds rejection (OUT_OF_BOUNDS)
- TEST G: Extreme aspect ratio rejection (EXTREME_ASPECT)
- TEST H: Confidence boundary values and monotonicity
- TEST I: Production ImageDetectionPipeline execution
- TEST J: Real SSS ML model -> MarineGuard class mapping 0 -> 29 -> Role 3 filtering -> evidence
- MCP and API endpoint integration
"""

import io
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.confidence import (
    calibrate_confidence,
    calibrate_confidence_float,
    is_monotonic,
    CONFIDENCE_METHOD,
)
from marineguard.detection.filtering import (
    DetectionFilter,
    filter_detection_result,
    FilteredResult,
)
from marineguard.detection.evidence import (
    DetectionEvidenceBuilder,
    format_evidence_card,
    format_evidence_html,
    format_result_summary,
)
from marineguard.detection.detector import MockDetector
from marineguard.detection.pipeline import ImageDetectionPipeline
from marineguard.detection.side_scan import SideScanDetector
from marineguard.mcp_server import MarineGuardMCPServer
from marineguard.api.app import app, get_pipeline


REPO_ROOT = Path(__file__).resolve().parents[1]
SSS_VAL_IMAGE = REPO_ROOT / "data" / "processed" / "marineguard_sss" / "images" / "val" / "synth_ghost_net_00001.png"


# ---------------------------------------------------------------------------
# TEST A — No detections
# ---------------------------------------------------------------------------

def test_role3_test_a_no_detections():
    """TEST A: Empty DetectionResult returns safe empty result without crashing."""
    empty_result = DetectionResult.from_detections([])
    f = DetectionFilter(confidence_threshold=0.30)
    fr = f.filter(empty_result)

    assert len(fr.filtered_detections) == 0
    assert len(fr.accepted) == 0
    assert len(fr.rejected) == 0

    det_result = fr.to_detection_result()
    assert isinstance(det_result, DetectionResult)
    assert det_result.count == 0
    assert det_result.detections == []
    assert det_result.role3_summary["raw_count"] == 0
    assert det_result.role3_summary["accepted_count"] == 0
    assert det_result.role3_summary["rejected_count"] == 0

    api_dict = det_result.to_api_dict()
    assert api_dict["count"] == 0
    assert api_dict["detections"] == []
    assert "role3_summary" in api_dict

    # Also test completely None input
    fr_none = f.filter(None)
    assert len(fr_none.accepted) == 0
    assert len(fr_none.rejected) == 0


# ---------------------------------------------------------------------------
# TEST B — Valid detection
# ---------------------------------------------------------------------------

def test_role3_test_b_valid_detection():
    """TEST B: Valid bbox and confidence: accepted, raw confidence preserved, presentation score present, evidence present."""
    det = Detection(
        class_name="plastic-bottle",
        class_id=0,
        confidence=0.88,
        bbox=[100.0, 100.0, 200.0, 250.0],
        metadata={"source_sensor": "optical"},
    )
    result = DetectionResult.from_detections([det], image_width=640, image_height=480)
    fr = filter_detection_result(result, confidence_threshold=0.30)

    assert len(fr.accepted) == 1
    assert len(fr.rejected) == 0

    fd = fr.accepted[0]
    assert fd.filter_status == "accepted"
    assert fd.filter_reason is None
    # Raw confidence preserved unchanged
    assert fd.raw_confidence == 0.88
    # Presentation/calibrated score derived and in [0, 100]
    assert isinstance(fd.calibrated_confidence, int)
    assert 82 <= fd.calibrated_confidence <= 100
    assert fd.confidence_method == CONFIDENCE_METHOD

    # Evidence generated
    builder = DetectionEvidenceBuilder()
    evidence = builder.build(fd)
    assert evidence.class_name == "plastic-bottle"
    assert evidence.filter_status == "accepted"
    assert evidence.raw_confidence == 0.88
    assert evidence.calibrated_confidence == fd.calibrated_confidence

    card = format_evidence_card(evidence)
    assert "[ACCEPTED]" in card
    assert "plastic-bottle" in card
    assert "0.8800" in card

    # Converted DetectionResult
    det_res = fr.to_detection_result()
    assert det_res.count == 1
    assert det_res.detections[0].confidence == 0.88
    assert det_res.detections[0].metadata["calibrated_confidence"] == fd.calibrated_confidence
    assert det_res.detections[0].metadata["role3"]["filter_status"] == "accepted"


# ---------------------------------------------------------------------------
# TEST C — Low confidence
# ---------------------------------------------------------------------------

def test_role3_test_c_low_confidence():
    """TEST C: Low confidence rejected with LOW_CONFIDENCE, evidence contains reason."""
    det = Detection(
        class_name="ghost-net",
        class_id=20,
        confidence=0.22,
        bbox=[50.0, 50.0, 150.0, 150.0],
    )
    result = DetectionResult.from_detections([det])
    fr = filter_detection_result(result, confidence_threshold=0.30)

    assert len(fr.accepted) == 0
    assert len(fr.rejected) == 1

    fd = fr.rejected[0]
    assert fd.filter_status == "rejected"
    assert fd.filter_reason == "LOW_CONFIDENCE"
    assert fd.rejection_rule == "LOW_CONFIDENCE"
    assert "LOW_CONFIDENCE_CHECK" in fd.applied_rules

    # Evidence record contains reason
    builder = DetectionEvidenceBuilder()
    evidence = builder.build(fd)
    assert evidence.filter_status == "rejected"
    assert evidence.filter_reason == "LOW_CONFIDENCE"

    card = format_evidence_card(evidence)
    assert "[REJECTED]" in card
    assert "LOW_CONFIDENCE" in card

    # Result maintains 0 accepted detections
    det_res = fr.to_detection_result()
    assert det_res.count == 0
    assert len(det_res.detections) == 0
    assert det_res.role3_summary["rejected_count"] == 1


# ---------------------------------------------------------------------------
# TEST D — Zero area
# ---------------------------------------------------------------------------

def test_role3_test_d_zero_area():
    """TEST D: Bbox with zero area rejected with ZERO_AREA_BBOX."""
    det1 = Detection(class_name="can", confidence=0.85, bbox=[100.0, 100.0, 100.0, 100.0])
    det2 = Detection(class_name="can", confidence=0.85, bbox=[100.0, 50.0, 100.0, 200.0])
    result = DetectionResult.from_detections([det1, det2])
    fr = filter_detection_result(result)

    assert len(fr.accepted) == 0
    assert len(fr.rejected) == 2
    for fd in fr.rejected:
        assert fd.filter_status == "rejected"
        assert fd.filter_reason == "ZERO_AREA_BBOX"


# ---------------------------------------------------------------------------
# TEST E — Invalid bbox
# ---------------------------------------------------------------------------

def test_role3_test_e_invalid_bbox():
    """TEST E: Malformed bbox (inverted coordinates, NaN, non-numeric, wrong length) rejected with INVALID_BBOX."""
    det_inv_x = Detection(class_name="tire", confidence=0.90, bbox=[200.0, 50.0, 100.0, 150.0])
    det_inv_y = Detection(class_name="tire", confidence=0.90, bbox=[50.0, 200.0, 150.0, 100.0])
    det_nan = Detection(class_name="tire", confidence=0.90, bbox=[50.0, float("nan"), 150.0, 100.0])
    det_inf = Detection(class_name="tire", confidence=0.90, bbox=[50.0, 50.0, float("inf"), 100.0])

    result = DetectionResult.from_detections([det_inv_x, det_inv_y, det_nan, det_inf])
    fr = filter_detection_result(result)

    assert len(fr.accepted) == 0
    assert len(fr.rejected) == 4
    for fd in fr.rejected:
        assert fd.filter_status == "rejected"
        assert fd.filter_reason == "INVALID_BBOX"


# ---------------------------------------------------------------------------
# TEST F — Out of bounds
# ---------------------------------------------------------------------------

def test_role3_test_f_out_of_bounds():
    """TEST F: Bbox fully outside image boundaries rejected with OUT_OF_BOUNDS."""
    det_oob_right = Detection(class_name="rope", confidence=0.75, bbox=[700.0, 100.0, 800.0, 200.0])
    det_oob_bottom = Detection(class_name="rope", confidence=0.75, bbox=[100.0, 500.0, 200.0, 600.0])
    det_oob_neg = Detection(class_name="rope", confidence=0.75, bbox=[-100.0, -100.0, -10.0, -10.0])

    result = DetectionResult.from_detections([det_oob_right, det_oob_bottom, det_oob_neg], image_width=640, image_height=480)
    fr = filter_detection_result(result, image_width=640, image_height=480)

    assert len(fr.accepted) == 0
    assert len(fr.rejected) == 3
    for fd in fr.rejected:
        assert fd.filter_status == "rejected"
        assert fd.filter_reason == "OUT_OF_BOUNDS"


# ---------------------------------------------------------------------------
# TEST G — Extreme aspect ratio
# ---------------------------------------------------------------------------

def test_role3_test_g_extreme_aspect():
    """TEST G: Extreme aspect ratio rejected with EXTREME_ASPECT."""
    det_wide = Detection(class_name="cable", confidence=0.80, bbox=[10.0, 100.0, 610.0, 102.0])
    det_tall = Detection(class_name="cable", confidence=0.80, bbox=[100.0, 10.0, 102.0, 410.0])

    result = DetectionResult.from_detections([det_wide, det_tall])
    fr = filter_detection_result(result, max_aspect_ratio=50.0)

    assert len(fr.accepted) == 0
    assert len(fr.rejected) == 2
    for fd in fr.rejected:
        assert fd.filter_status == "rejected"
        assert fd.filter_reason == "EXTREME_ASPECT"


# ---------------------------------------------------------------------------
# TEST H — Confidence boundary conditions
# ---------------------------------------------------------------------------

def test_role3_test_h_confidence_boundaries():
    """TEST H: Test all mapping boundaries explicitly:
    0.0, 0.299999, 0.30, 0.499999, 0.50, 0.699999, 0.70, 0.849999, 0.85, 1.0
    """
    boundaries = [
        0.0,
        0.299999,
        0.30,
        0.499999,
        0.50,
        0.699999,
        0.70,
        0.849999,
        0.85,
        1.0,
    ]

    cal_scores = []
    for val in boundaries:
        score = calibrate_confidence(val)
        assert isinstance(score, int)
        assert 0 <= score <= 100
        cal_scores.append(score)

    assert cal_scores[0] == 0
    assert cal_scores[-1] == 100

    for i in range(1, len(cal_scores)):
        assert cal_scores[i] >= cal_scores[i - 1], (
            f"Monotonicity failed between {boundaries[i-1]} ({cal_scores[i-1]}) "
            f"and {boundaries[i]} ({cal_scores[i]})"
        )

    assert is_monotonic() is True


# ---------------------------------------------------------------------------
# TEST I — Production ImageDetectionPipeline execution
# ---------------------------------------------------------------------------

def test_role3_test_i_production_pipeline_integration():
    """TEST I: ImageDetectionPipeline processes an image and executes Role 3 filtering in the live path."""
    mock_det = MockDetector(
        mock_detections=[
            {"class": "plastic-bottle", "confidence": 0.85, "bbox": [100.0, 100.0, 200.0, 200.0]},
            {"class": "tiny-speck", "confidence": 0.60, "bbox": [10.0, 10.0, 11.0, 11.0]},
        ]
    )
    pipeline = ImageDetectionPipeline(
        detector=mock_det,
        confidence_threshold=0.50,
    )

    img = np.full((300, 400, 3), 128, dtype=np.uint8)
    result = pipeline.process(img)

    assert isinstance(result, DetectionResult)
    assert result.count == 1
    assert result.detections[0].class_name == "plastic-bottle"
    assert result.detections[0].confidence == 0.85
    assert "calibrated_confidence" in result.detections[0].metadata
    assert result.detections[0].metadata["calibrated_confidence"] > 0
    assert result.detections[0].metadata["role3"]["filter_status"] == "accepted"

    assert result.role3_summary is not None
    assert result.role3_summary["raw_count"] == 2
    assert result.role3_summary["accepted_count"] == 1
    assert result.role3_summary["rejected_count"] == 1

    assert result.all_detections is not None
    assert len(result.all_detections) == 2
    speck_det = [d for d in result.all_detections if d["class"] == "tiny-speck"][0]
    assert speck_det["role3"]["filter_status"] == "rejected"
    assert speck_det["role3"]["filter_reason"] == "TINY_BBOX"

    api_dict = result.to_api_dict()
    assert api_dict["count"] == 1
    assert len(api_dict["detections"]) == 1
    assert api_dict["detections"][0]["class"] == "plastic-bottle"
    assert api_dict["detections"][0]["confidence"] == 0.85
    assert api_dict["role3_summary"]["accepted_count"] == 1


# ---------------------------------------------------------------------------
# TEST J — SSS integration with real validation image
# ---------------------------------------------------------------------------

def test_role3_test_j_sss_integration():
    """TEST J: SSS YOLO inference on real test image -> MarineGuard class mapping 0 -> 29 -> Role 3 filtering -> evidence."""
    if not SSS_VAL_IMAGE.exists():
        pytest.skip(f"SSS validation image not found at {SSS_VAL_IMAGE}")

    detector = SideScanDetector.with_sss_model(use_onnx=False, confidence_threshold=0.30)
    raw_res = detector.detect_waterfall(SSS_VAL_IMAGE, use_ml=True)

    assert raw_res.status in ("SUCCESS", "ok")
    assert raw_res.count >= 1

    for det in raw_res.detections:
        assert det.class_id == 29
        assert det.class_name == "net"

    fr = filter_detection_result(raw_res, confidence_threshold=0.30, image_width=raw_res.image_width, image_height=raw_res.image_height)

    assert len(fr.filtered_detections) == raw_res.count
    assert len(fr.accepted) >= 1

    fd = fr.accepted[0]
    builder = DetectionEvidenceBuilder()
    evidence = builder.build(fd)

    assert evidence.class_name == "net"
    assert evidence.class_id == 29
    assert evidence.filter_status == "accepted"
    assert evidence.calibrated_confidence > 0

    card = format_evidence_card(evidence)
    assert "[ACCEPTED] net (class_id=29)" in card

    summary = format_result_summary(fr)
    assert "ROLE 3 FILTER SUMMARY" in summary


# ---------------------------------------------------------------------------
# MCP Integration Verification
# ---------------------------------------------------------------------------

def test_role3_mcp_server_integration():
    """Verify MarineGuardMCPServer runs Role 3 filtering and exposes calibrated confidence."""
    mock_det = MockDetector(
        mock_detections=[
            {"class": "tire", "confidence": 0.82, "bbox": [50.0, 50.0, 150.0, 150.0]}
        ]
    )
    pipeline = ImageDetectionPipeline(detector=mock_det)
    server = MarineGuardMCPServer(detection_pipeline=pipeline)

    pil_img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    res = server.detect_marine_debris(buf.getvalue())

    assert res["status"] == "SUCCESS"
    assert res["count"] == 1
    det = res["detections"][0]
    assert det["class"] == "tire"
    assert det["confidence"] == 0.82
    assert "calibrated_confidence" in det
    assert det["calibrated_confidence"] > 0
    assert "role3" in det


# ---------------------------------------------------------------------------
# API Endpoint Integration Verification
# ---------------------------------------------------------------------------

def test_role3_api_detect_endpoint_integration():
    """Verify FastAPI /detect endpoint returns Role 3 summary and calibrated confidence."""
    mock_det = MockDetector(
        mock_detections=[
            {"class": "plastic-bottle", "confidence": 0.91, "bbox": [120.0, 80.0, 240.0, 310.0]}
        ]
    )
    mock_pipeline = ImageDetectionPipeline(detector=mock_det)
    app.dependency_overrides[get_pipeline] = lambda: mock_pipeline

    with TestClient(app) as client:
        img = Image.new("RGB", (640, 480), color=(73, 109, 137))
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        response = client.post(
            "/detect",
            files={"file": ("test.png", buf.getvalue(), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 1
        assert data["detections"][0]["class"] == "plastic-bottle"
        assert data["detections"][0]["confidence"] == 0.91

        assert "role3_summary" in data
        assert data["role3_summary"]["accepted_count"] == 1
        assert "calibrated_confidence" in data["detections"][0]

    app.dependency_overrides.clear()
