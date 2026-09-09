"""
Tests for Role 3 — False-Positive Filtering Layer
marineguard/detection/filtering.py
"""

import pytest
from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.filtering import (
    DetectionFilter,
    FilteredDetection,
    FilteredResult,
    filter_detection_result,
    _check_confidence,
    _check_bbox_valid,
    _check_bbox_positive_area,
    _check_bbox_area,
    _check_bbox_in_bounds,
    _check_aspect_ratio,
    _check_cfar_geometry,
    _check_bathymetry_geometry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_detection(
    class_name="plastic-bottle",
    class_id=0,
    confidence=0.80,
    bbox=None,
    metadata=None,
):
    return Detection(
        class_name=class_name,
        class_id=class_id,
        confidence=confidence,
        bbox=bbox or [50.0, 50.0, 150.0, 200.0],
        metadata=metadata or {},
    )


def make_result(detections, image_width=640, image_height=480):
    return DetectionResult.from_detections(
        detections=detections,
        image_width=image_width,
        image_height=image_height,
        model_name="TestModel",
    )


# ---------------------------------------------------------------------------
# 1. Empty input
# ---------------------------------------------------------------------------

def test_filter_empty_detections():
    """Empty DetectionResult → empty FilteredResult with 0 detections."""
    result = make_result([])
    f = DetectionFilter()
    fr = f.filter(result)
    assert len(fr.filtered_detections) == 0
    assert len(fr.accepted) == 0
    assert len(fr.rejected) == 0


# ---------------------------------------------------------------------------
# 2. Single accepted detection
# ---------------------------------------------------------------------------

def test_filter_single_accepted():
    """Valid high-confidence detection must be accepted."""
    det = make_detection(confidence=0.85)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert len(fr.accepted) == 1
    assert fr.accepted[0].filter_status == "accepted"
    assert fr.accepted[0].filter_reason is None


# ---------------------------------------------------------------------------
# 3. Single rejected detection — low confidence
# ---------------------------------------------------------------------------

def test_filter_low_confidence_rejected():
    """Detection with confidence below threshold → LOW_CONFIDENCE."""
    det = make_detection(confidence=0.20)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert len(fr.rejected) == 1
    assert fr.rejected[0].filter_reason == "LOW_CONFIDENCE"


# ---------------------------------------------------------------------------
# 4. Multiple detections — mixed accepted/rejected
# ---------------------------------------------------------------------------

def test_filter_multiple_mixed():
    """Multiple detections with varied quality → correct split."""
    dets = [
        make_detection(confidence=0.85, bbox=[10.0, 10.0, 100.0, 100.0]),  # accepted
        make_detection(confidence=0.10, bbox=[10.0, 10.0, 100.0, 100.0]),  # rejected: LOW_CONFIDENCE
        make_detection(confidence=0.75, bbox=[50.0, 50.0, 50.0, 50.0]),    # rejected: ZERO_AREA_BBOX
    ]
    result = make_result(dets)
    fr = filter_detection_result(result, confidence_threshold=0.30)
    assert len(fr.accepted) == 1
    assert len(fr.rejected) == 2


# ---------------------------------------------------------------------------
# 5. Confidence boundary cases
# ---------------------------------------------------------------------------

def test_filter_confidence_exactly_at_threshold():
    """Detection at exactly threshold must be accepted."""
    det = make_detection(confidence=0.50)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert fr.accepted[0].filter_status == "accepted"


def test_filter_confidence_just_below_threshold():
    """Detection just below threshold must be rejected."""
    det = make_detection(confidence=0.4999)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert fr.rejected[0].filter_reason == "LOW_CONFIDENCE"


# ---------------------------------------------------------------------------
# 6. Invalid bounding box
# ---------------------------------------------------------------------------

def test_filter_invalid_bbox_wrong_length():
    """_check_bbox_valid rejects bbox with wrong number of coordinates.

    Pydantic enforces min_length=4 on Detection.bbox at construction time, so
    we test _check_bbox_valid directly with a fake object carrying a short bbox.
    """
    class FakeDet:
        bbox = [10.0, 20.0]  # only 2 coords
        confidence = 0.80
        metadata = {}
        class_id = 0

    passed, reason = _check_bbox_valid(FakeDet())
    assert not passed
    assert reason == "INVALID_BBOX"


def test_filter_bbox_with_nan():
    """BBox containing NaN → INVALID_BBOX."""
    import math

    class FakeDet:
        bbox = [10.0, float("nan"), 100.0, 200.0]
        confidence = 0.80
        metadata = {}
        class_id = 0

    passed, reason = _check_bbox_valid(FakeDet())
    assert not passed
    assert reason == "INVALID_BBOX"


def test_filter_bbox_with_inf():
    """BBox containing Inf → INVALID_BBOX."""
    class FakeDet:
        bbox = [10.0, float("inf"), 100.0, 200.0]
        confidence = 0.80
        metadata = {}
        class_id = 0

    passed, reason = _check_bbox_valid(FakeDet())
    assert not passed
    assert reason == "INVALID_BBOX"


# ---------------------------------------------------------------------------
# 7. Zero area bounding box
# ---------------------------------------------------------------------------

def test_filter_zero_area_bbox_point():
    """BBox that is a single point → ZERO_AREA_BBOX."""
    det = make_detection(bbox=[50.0, 50.0, 50.0, 50.0])
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.30)
    assert fr.rejected[0].filter_reason == "ZERO_AREA_BBOX"


def test_filter_zero_area_bbox_line():
    """BBox with height=0 → ZERO_AREA_BBOX."""
    det = make_detection(bbox=[10.0, 50.0, 100.0, 50.0])
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.30)
    assert fr.rejected[0].filter_reason == "ZERO_AREA_BBOX"


# ---------------------------------------------------------------------------
# 8. Edge-of-image bounding box
# ---------------------------------------------------------------------------

def test_filter_edge_of_image_bbox_accepted():
    """BBox touching but not exceeding image boundary → accepted."""
    det = make_detection(bbox=[0.0, 0.0, 640.0, 480.0])
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert fr.accepted[0].filter_status == "accepted"


def test_filter_bbox_partially_out_of_bounds_accepted():
    """BBox partially outside image boundary → accepted (partial overlap)."""
    det = make_detection(bbox=[-10.0, -10.0, 100.0, 100.0])
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    # Partially inside, so should be accepted
    assert fr.accepted[0].filter_status == "accepted"


def test_filter_bbox_fully_out_of_bounds():
    """BBox completely outside image boundary → OUT_OF_BOUNDS."""
    det = make_detection(bbox=[700.0, 500.0, 800.0, 600.0])
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.30)
    reasons = [fd.filter_reason for fd in fr.rejected]
    assert "OUT_OF_BOUNDS" in reasons


# ---------------------------------------------------------------------------
# 9. Tiny bbox
# ---------------------------------------------------------------------------

def test_filter_tiny_bbox():
    """BBox with area < min_area_px2 → TINY_BBOX."""
    det = make_detection(bbox=[10.0, 10.0, 11.0, 11.0])  # 1x1 = area=1
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.30, min_area_px2=4.0)
    assert fr.rejected[0].filter_reason == "TINY_BBOX"


# ---------------------------------------------------------------------------
# 10. Aspect ratio
# ---------------------------------------------------------------------------

def test_filter_extreme_aspect_ratio():
    """Very thin BBox → EXTREME_ASPECT."""
    det = make_detection(bbox=[0.0, 0.0, 640.0, 2.0])  # 640x2 = 320:1
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.30, max_aspect_ratio=50.0)
    assert fr.rejected[0].filter_reason == "EXTREME_ASPECT"


def test_filter_acceptable_aspect_ratio():
    """Normal aspect ratio → accepted."""
    det = make_detection(bbox=[10.0, 10.0, 110.0, 70.0])  # 100x60 = 1.67:1
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert fr.accepted[0].filter_status == "accepted"


# ---------------------------------------------------------------------------
# 11. Rejection reason is set
# ---------------------------------------------------------------------------

def test_rejection_reason_populated():
    """Rejected detection must have filter_reason and rejection_rule set."""
    det = make_detection(confidence=0.10)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    fd = fr.rejected[0]
    assert fd.filter_reason is not None
    assert fd.rejection_rule is not None


def test_accepted_reason_is_none():
    """Accepted detection must have filter_reason=None."""
    det = make_detection(confidence=0.85)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    fd = fr.accepted[0]
    assert fd.filter_reason is None
    assert fd.rejection_rule is None


# ---------------------------------------------------------------------------
# 12. Modality — optical
# ---------------------------------------------------------------------------

def test_filter_optical_detection():
    """Optical detection with valid confidence and bbox → accepted."""
    det = make_detection(
        class_name="plastic-bottle", class_id=0, confidence=0.80,
        bbox=[100.0, 100.0, 200.0, 200.0],
        metadata={"source_sensor": "optical"},
    )
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert fr.accepted[0].filter_status == "accepted"


# ---------------------------------------------------------------------------
# 13. Modality — SSS net (class_id=29)
# ---------------------------------------------------------------------------

def test_filter_sss_net_detection():
    """SSS net detection (class_id=29) → accepted when valid."""
    det = make_detection(
        class_name="net", class_id=29, confidence=0.72,
        bbox=[50.0, 50.0, 200.0, 200.0],
        metadata={"source_sensor": "side_scan"},
    )
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert fr.accepted[0].filter_status == "accepted"
    # class_id=29 must not trigger CFAR_GEOMETRY rule (that's for class_id=27)
    rules = fr.accepted[0].applied_rules
    assert "CFAR_GEOMETRY_CHECK" not in rules


# ---------------------------------------------------------------------------
# 14. Modality — CA-CFAR (class_id=27)
# ---------------------------------------------------------------------------

def test_filter_cfar_valid():
    """Valid CA-CFAR anomaly detection → accepted."""
    det = make_detection(
        class_name="unknown-object", class_id=27, confidence=0.65,
        bbox=[50.0, 50.0, 120.0, 100.0],  # 70x50 = area 3500
        metadata={"source_sensor": "ca_cfar"},
    )
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert fr.accepted[0].filter_status == "accepted"
    assert "CFAR_GEOMETRY_CHECK" in fr.accepted[0].applied_rules


def test_filter_cfar_tiny_area_rejected():
    """CA-CFAR candidate with area < CFAR minimum → rejected by CFAR_GEOMETRY.

    The bbox area is 5 px² (50x51 to 51x52.1 = 1x1.1 ~ 1.1 — too small).
    We need area >= generic TINY_BBOX min (4 px²) but < CFAR min (16 px²):
    e.g., 50,50 to 52,52.5 → width=2, height=2.5 → area=5.0, passes TINY_BBOX,
    but _check_cfar_geometry requires min_area_px2=16 for sonar.
    """
    det = make_detection(
        class_name="unknown-object", class_id=27, confidence=0.65,
        bbox=[50.0, 50.0, 52.0, 52.5],  # area = 5.0 px²: passes TINY_BBOX (>=4), fails CFAR (>=16)
        metadata={"source_sensor": "ca_cfar"},
    )
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert fr.rejected[0].filter_reason == "CFAR_GEOMETRY"


# ---------------------------------------------------------------------------
# 15. Raw confidence preserved
# ---------------------------------------------------------------------------

def test_raw_confidence_preserved():
    """The raw_confidence in FilteredDetection must equal Detection.confidence."""
    det = make_detection(confidence=0.732)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    fd = fr.accepted[0] if fr.accepted else fr.rejected[0]
    assert abs(fd.raw_confidence - 0.732) < 1e-9


# ---------------------------------------------------------------------------
# 16. Calibrated confidence added
# ---------------------------------------------------------------------------

def test_calibrated_confidence_added():
    """FilteredDetection must carry a calibrated_confidence [0, 100]."""
    det = make_detection(confidence=0.80)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    fd = fr.accepted[0]
    assert 0 <= fd.calibrated_confidence <= 100


# ---------------------------------------------------------------------------
# 17. Applied rules non-empty
# ---------------------------------------------------------------------------

def test_applied_rules_non_empty():
    """At least one rule must be checked for every detection."""
    det = make_detection(confidence=0.80)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    assert len(fr.accepted[0].applied_rules) > 0


# ---------------------------------------------------------------------------
# 18. API dict backward compatibility
# ---------------------------------------------------------------------------

def test_to_api_dict_backward_compatible():
    """to_api_dict must include 'detections' and 'count' for accepted dets."""
    det = make_detection(confidence=0.85)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    d = fr.to_api_dict()
    assert "detections" in d
    assert "count" in d
    assert d["count"] == len(fr.accepted)


def test_to_api_dict_has_role3_summary():
    """to_api_dict must include 'role3_summary' with filter metadata."""
    det = make_detection(confidence=0.85)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)
    d = fr.to_api_dict()
    assert "role3_summary" in d
    assert "raw_count" in d["role3_summary"]
    assert "accepted_count" in d["role3_summary"]
    assert "rejected_count" in d["role3_summary"]


def test_to_full_api_dict_includes_rejected():
    """to_full_api_dict must include all detections (accepted + rejected)."""
    dets = [
        make_detection(confidence=0.85),
        make_detection(confidence=0.10),
    ]
    result = make_result(dets)
    fr = filter_detection_result(result, confidence_threshold=0.50)
    d = fr.to_full_api_dict()
    assert "all_detections" in d
    assert len(d["all_detections"]) == 2


# ---------------------------------------------------------------------------
# 19. Deterministic output
# ---------------------------------------------------------------------------

def test_filter_deterministic():
    """Same input → same output every time."""
    det = make_detection(confidence=0.65, bbox=[20.0, 20.0, 120.0, 120.0])
    result = make_result([det])
    fr1 = filter_detection_result(result, confidence_threshold=0.50)
    fr2 = filter_detection_result(result, confidence_threshold=0.50)
    assert fr1.accepted[0].filter_status == fr2.accepted[0].filter_status
    assert fr1.accepted[0].filter_reason == fr2.accepted[0].filter_reason
