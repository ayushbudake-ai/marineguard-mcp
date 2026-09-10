"""
Tests for Role 3 — Evidence / Explainability Layer
marineguard/detection/evidence.py
"""

import pytest
from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.filtering import filter_detection_result
from marineguard.detection.evidence import (
    DetectionEvidenceBuilder,
    EvidenceRecord,
    format_evidence_card,
    format_evidence_html,
    format_result_summary,
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
# 1. Basic evidence building
# ---------------------------------------------------------------------------

def test_evidence_build_accepted():
    """Accepted detection → EvidenceRecord with filter_status='accepted'."""
    det = make_detection(confidence=0.85)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    records = builder.build_all(fr)
    assert len(records) == 1
    rec = records[0]
    assert rec.filter_status == "accepted"
    assert rec.filter_reason is None
    assert rec.raw_confidence == pytest.approx(0.85, abs=1e-9)


def test_evidence_build_rejected():
    """Rejected detection → EvidenceRecord with filter_status='rejected'."""
    det = make_detection(confidence=0.10)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    records = builder.build_all(fr)
    assert len(records) == 1
    rec = records[0]
    assert rec.filter_status == "rejected"
    assert rec.filter_reason == "LOW_CONFIDENCE"


# ---------------------------------------------------------------------------
# 2. EvidenceRecord fields are correct
# ---------------------------------------------------------------------------

def test_evidence_record_fields():
    """EvidenceRecord must expose all expected fields."""
    det = make_detection(
        class_name="tire", class_id=8, confidence=0.72,
        bbox=[100.0, 100.0, 200.0, 200.0],
        metadata={"source_sensor": "optical"},
    )
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    rec = builder.build(fr.accepted[0])
    assert rec.class_name == "tire"
    assert rec.class_id == 8
    assert rec.raw_confidence == pytest.approx(0.72, abs=1e-9)
    assert 0 <= rec.calibrated_confidence <= 100
    assert rec.confidence_method != ""
    assert rec.confidence_threshold == 0.50
    assert rec.bbox == [100.0, 100.0, 200.0, 200.0]
    assert rec.source_sensor == "optical"
    assert rec.filter_status == "accepted"


# ---------------------------------------------------------------------------
# 3. to_dict round-trip
# ---------------------------------------------------------------------------

def test_evidence_record_to_dict():
    """EvidenceRecord.to_dict() must return a plain dict with expected keys."""
    det = make_detection(confidence=0.75)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    rec = builder.build(fr.accepted[0])
    d = rec.to_dict()

    required_keys = {
        "class_name", "raw_confidence", "calibrated_confidence",
        "confidence_method", "filter_status", "filter_reason",
        "rejection_rule", "applied_rules", "bbox", "source_sensor",
    }
    for key in required_keys:
        assert key in d, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# 4. Explainability — card formatting
# ---------------------------------------------------------------------------

def test_format_evidence_card_accepted():
    """Evidence card for accepted detection must contain 'ACCEPTED' and class name."""
    det = make_detection(class_name="ghost-net", confidence=0.82)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    rec = builder.build(fr.accepted[0])
    card = format_evidence_card(rec)
    assert "ACCEPTED" in card
    assert "ghost-net" in card
    assert "Raw confidence" in card


def test_format_evidence_card_rejected():
    """Evidence card for rejected detection must contain rejection reason."""
    det = make_detection(confidence=0.10)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    rec = builder.build(fr.rejected[0])
    card = format_evidence_card(rec)
    assert "REJECTED" in card
    assert "LOW_CONFIDENCE" in card


def test_format_evidence_card_no_fabrication():
    """Evidence card must not contain strings that are not backed by data."""
    det = make_detection(confidence=0.78)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    rec = builder.build(fr.accepted[0])
    card = format_evidence_card(rec)
    # The card should NOT contain fabricated improvement claims
    assert "reduced false positives by" not in card.lower()
    assert "accuracy" not in card.lower()


# ---------------------------------------------------------------------------
# 5. HTML formatting
# ---------------------------------------------------------------------------

def test_format_evidence_html_accepted():
    """HTML card for accepted detection must contain class name and ACCEPTED."""
    det = make_detection(class_name="plastic-bottle", confidence=0.80)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    rec = builder.build(fr.accepted[0])
    html = format_evidence_html(rec)
    assert "plastic-bottle" in html
    assert "ACCEPTED" in html


def test_format_evidence_html_rejected():
    """HTML card for rejected detection must contain rejection reason in red."""
    det = make_detection(confidence=0.10)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    rec = builder.build(fr.rejected[0])
    html = format_evidence_html(rec)
    assert "REJECTED" in html
    assert "LOW_CONFIDENCE" in html


# ---------------------------------------------------------------------------
# 6. Result summary formatting
# ---------------------------------------------------------------------------

def test_format_result_summary_content():
    """Summary must contain raw/accepted/rejected counts."""
    dets = [
        make_detection(confidence=0.85),
        make_detection(confidence=0.10),
    ]
    result = make_result(dets)
    fr = filter_detection_result(result, confidence_threshold=0.50)
    summary = format_result_summary(fr)
    assert "Raw detections" in summary
    assert "Accepted" in summary
    assert "Rejected" in summary
    assert "2" in summary  # 2 total


# ---------------------------------------------------------------------------
# 7. Empty result evidence
# ---------------------------------------------------------------------------

def test_evidence_build_empty():
    """Empty FilteredResult → empty evidence list."""
    result = make_result([])
    fr = filter_detection_result(result)
    builder = DetectionEvidenceBuilder()
    records = builder.build_all(fr)
    assert records == []


# ---------------------------------------------------------------------------
# 8. CA-CFAR evidence
# ---------------------------------------------------------------------------

def test_evidence_cfar_detection():
    """CA-CFAR detection evidence must indicate source_sensor from metadata."""
    det = make_detection(
        class_name="unknown-object", class_id=27, confidence=0.65,
        bbox=[50.0, 50.0, 120.0, 120.0],
        metadata={"source_sensor": "ca_cfar"},
    )
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    records = builder.build_all(fr)
    assert records[0].source_sensor == "ca_cfar"


# ---------------------------------------------------------------------------
# 9. Applied rules in evidence
# ---------------------------------------------------------------------------

def test_evidence_applied_rules_non_empty():
    """EvidenceRecord.applied_rules must list at least one checked rule."""
    det = make_detection(confidence=0.75)
    result = make_result([det])
    fr = filter_detection_result(result, confidence_threshold=0.50)

    builder = DetectionEvidenceBuilder()
    rec = builder.build(fr.accepted[0])
    assert len(rec.applied_rules) > 0
