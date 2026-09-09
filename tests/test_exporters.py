"""
Role 4 — Exporter Tests for MarineGuard MCP

Tests:
    GeoJSONExporter
    S100Exporter
    PDFReportExporter
    TabularExporter
    Geotagger

Synthetic test coordinates/data are clearly marked as TEST ONLY.
They are used only inside test fixtures and must never leak into
production exports.

Run:
    python -m pytest tests/test_exporters.py -v
"""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from typing import Any, Dict, List, Optional

import pytest

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.exporters.geotagging import Geotagger, GeoCoordinate
from marineguard.exporters.geojson_export import GeoJSONExporter
from marineguard.exporters.s100_export import S100Exporter, S100ExportValidationError
from marineguard.exporters.pdf_report import PDFReportExporter
from marineguard.exporters.tabular_export import TabularExporter, TABULAR_FIELDS


# ===========================================================================
# TEST FIXTURES
# ===========================================================================

def _make_detection(
    class_name: str = "bottle",
    class_id: int = 0,
    confidence: float = 0.85,
    bbox: List[float] = None,
    source_sensor: str = "optical",
    calibrated_confidence: int = 82,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Detection:
    """Create a synthetic Detection for testing. TEST ONLY."""
    if bbox is None:
        bbox = [10.0, 20.0, 110.0, 120.0]
    metadata: Dict[str, Any] = {
        "source_sensor": source_sensor,
        "calibrated_confidence": calibrated_confidence,
        "role3": {
            "raw_confidence": round(confidence, 6),
            "calibrated_confidence": calibrated_confidence,
            "confidence_method": "DETERMINISTIC_PIECEWISE_LINEAR_v1",
            "confidence_threshold": 0.30,
            "filter_status": "accepted",
            "filter_reason": None,
            "applied_rules": ["LOW_CONFIDENCE", "INVALID_BBOX", "ZERO_AREA_BBOX"],
            "rejection_rule": None,
        },
    }
    # Synthetic test coordinates — TEST ONLY
    if latitude is not None:
        metadata["latitude"] = latitude
    if longitude is not None:
        metadata["longitude"] = longitude
    if extra_meta:
        metadata.update(extra_meta)
    return Detection(
        class_name=class_name,
        class_id=class_id,
        confidence=confidence,
        bbox=bbox,
        metadata=metadata,
    )


def _make_rejected_entry(
    class_name: str = "net",
    class_id: int = 29,
    raw_confidence: float = 0.18,
    rejection_rule: str = "LOW_CONFIDENCE",
    bbox: List[float] = None,
    source_sensor: str = "side-scan sonar",
) -> Dict[str, Any]:
    """Create a synthetic rejected detection dict for testing. TEST ONLY."""
    if bbox is None:
        bbox = [5.0, 5.0, 25.0, 25.0]
    return {
        "class": class_name,
        "class_id": class_id,
        "confidence": raw_confidence,
        "bbox": bbox,
        "metadata": {"source_sensor": source_sensor},
        "role3": {
            "raw_confidence": raw_confidence,
            "calibrated_confidence": 8,
            "confidence_method": "DETERMINISTIC_PIECEWISE_LINEAR_v1",
            "confidence_threshold": 0.30,
            "filter_status": "rejected",
            "filter_reason": rejection_rule,
            "applied_rules": ["LOW_CONFIDENCE"],
            "rejection_rule": rejection_rule,
        },
    }


def _make_result(
    detections: Optional[List[Detection]] = None,
    all_detections: Optional[List[Dict]] = None,
    image_width: int = 640,
    image_height: int = 480,
) -> DetectionResult:
    """Create a synthetic DetectionResult for testing. TEST ONLY."""
    dets = detections or []
    all_dets = all_detections or [d.to_dict() for d in dets]
    return DetectionResult(
        detections=dets,
        count=len(dets),
        image_width=image_width,
        image_height=image_height,
        inference_time_ms=12.5,
        model_name="MarineGuard-V1-TEST",
        status="SUCCESS",
        role3_summary={
            "raw_count": len(all_dets),
            "accepted_count": len(dets),
            "rejected_count": len(all_dets) - len(dets),
            "confidence_threshold": 0.30,
            "confidence_method": "DETERMINISTIC_PIECEWISE_LINEAR_v1",
        },
        all_detections=all_dets,
    )


# ===========================================================================
# GEOTAGGER TESTS
# ===========================================================================

class TestGeotagger:
    """Tests for Geotagger coordinate extraction."""

    def test_no_coordinates_returns_none(self):
        """Detection without any coordinate metadata → null coordinates."""
        det = _make_detection()  # no lat/lon
        tagger = Geotagger()
        coord = tagger.geotag(det)
        assert coord.latitude is None
        assert coord.longitude is None
        assert not coord.is_available

    def test_flat_lat_lon_in_metadata(self):
        """TEST ONLY synthetic coords: lat/lon flat in metadata → extracted correctly."""
        # Synthetic test coordinates — TEST ONLY
        det = _make_detection(latitude=12.9716, longitude=77.5946)
        tagger = Geotagger()
        coord = tagger.geotag(det)
        assert coord.latitude == pytest.approx(12.9716)
        assert coord.longitude == pytest.approx(77.5946)
        assert coord.is_available

    def test_nested_coordinates_dict(self):
        """TEST ONLY synthetic coords: nested coordinates dict in metadata."""
        # Synthetic test coordinates — TEST ONLY
        det = _make_detection(extra_meta={"coordinates": {"lat": 8.5241, "lon": 76.9366}})
        tagger = Geotagger()
        coord = tagger.geotag(det)
        assert coord.latitude == pytest.approx(8.5241)
        assert coord.longitude == pytest.approx(76.9366)
        assert coord.is_available

    def test_mission_metadata_fallback(self):
        """TEST ONLY synthetic coords: mission metadata provides real coords."""
        det = _make_detection()
        # Synthetic test coordinates — TEST ONLY
        tagger = Geotagger()
        coord = tagger.geotag(det, mission_metadata={"latitude": 10.0, "longitude": 76.0})
        assert coord.latitude == pytest.approx(10.0)
        assert coord.longitude == pytest.approx(76.0)

    def test_invalid_string_coord_ignored(self):
        """Non-numeric string in lat/lon metadata → null (not crash)."""
        det = _make_detection(extra_meta={"latitude": "N/A", "longitude": "N/A"})
        tagger = Geotagger()
        coord = tagger.geotag(det)
        assert coord.latitude is None
        assert coord.longitude is None

    def test_geojson_coordinate_order_lon_lat(self):
        """TEST ONLY: GeoJSON coordinates are [longitude, latitude] not [lat, lon]."""
        # Synthetic test coordinates — TEST ONLY
        det = _make_detection(latitude=13.0, longitude=80.0)
        tagger = Geotagger()
        coord = tagger.geotag(det)
        geojson_coords = coord.to_geojson_coordinates()
        # GeoJSON: [longitude, latitude]
        assert geojson_coords[0] == pytest.approx(80.0), "First element must be LONGITUDE"
        assert geojson_coords[1] == pytest.approx(13.0), "Second element must be LATITUDE"

    def test_geojson_coordinates_null_when_unavailable(self):
        """No coords available → to_geojson_coordinates returns None."""
        det = _make_detection()
        tagger = Geotagger()
        coord = tagger.geotag(det)
        assert coord.to_geojson_coordinates() is None

    def test_geotag_result_indexes_all_detections(self):
        """geotag_result maps index → GeoCoordinate for each detection."""
        d1 = _make_detection(latitude=1.0, longitude=2.0)
        d2 = _make_detection()  # no coords
        result = _make_result([d1, d2])
        tagger = Geotagger()
        coords = tagger.geotag_result(result)
        assert coords[0].is_available
        assert not coords[1].is_available


# ===========================================================================
# GEOJSON EXPORTER TESTS
# ===========================================================================

class TestGeoJSONExporter:
    """Tests for GeoJSONExporter."""

    def test_empty_result_is_valid_geojson(self):
        """Zero detections → valid empty FeatureCollection."""
        result = _make_result([])
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        assert fc["type"] == "FeatureCollection"
        assert fc["features"] == []
        assert "properties" in fc

    def test_single_detection_no_coords(self):
        """One detection without coordinates → Feature with geometry=null."""
        det = _make_detection()
        result = _make_result([det])
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        assert len(fc["features"]) == 1
        feature = fc["features"][0]
        assert feature["geometry"] is None  # null geometry — valid per RFC 7946

    def test_single_detection_with_coords_geometry_is_point(self):
        """TEST ONLY coords: one detection with coordinates → Point geometry."""
        # Synthetic test coordinates — TEST ONLY
        det = _make_detection(latitude=12.0, longitude=77.0)
        result = _make_result([det])
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        feature = fc["features"][0]
        assert feature["geometry"]["type"] == "Point"
        assert feature["geometry"]["coordinates"] is not None

    def test_coordinate_order_is_longitude_latitude(self):
        """TEST ONLY coords: GeoJSON Point coordinates MUST be [longitude, latitude]."""
        # Synthetic test coordinates — TEST ONLY
        TEST_LAT = 13.0827
        TEST_LON = 80.2707
        det = _make_detection(latitude=TEST_LAT, longitude=TEST_LON)
        result = _make_result([det])
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        coords = fc["features"][0]["geometry"]["coordinates"]
        assert coords[0] == pytest.approx(TEST_LON), "First coord must be LONGITUDE"
        assert coords[1] == pytest.approx(TEST_LAT), "Second coord must be LATITUDE"

    def test_multiple_detections(self):
        """Multiple detections → multiple features."""
        dets = [
            _make_detection("bottle", 0, 0.90),
            _make_detection("net", 29, 0.75, source_sensor="side-scan sonar"),
            _make_detection("tire", 8, 0.82),
        ]
        result = _make_result(dets)
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        assert len(fc["features"]) == 3

    def test_detection_properties_preserved(self):
        """Properties must include class_id, class_name, confidence, sensor, bbox, status."""
        det = _make_detection("unknown-object", 27, 0.65, source_sensor="side-scan sonar")
        result = _make_result([det])
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        props = fc["features"][0]["properties"]
        assert props["class_id"] == 27
        assert props["class_name"] == "unknown-object"
        assert props["raw_confidence"] == pytest.approx(0.65, abs=1e-5)
        assert props["source_sensor"] == "side-scan sonar"
        assert len(props["bbox"]) == 4
        assert props["filter_status"] == "accepted"

    def test_calibrated_confidence_in_properties(self):
        """Calibrated confidence from metadata → preserved in properties."""
        det = _make_detection(calibrated_confidence=75)
        result = _make_result([det])
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        assert fc["features"][0]["properties"]["calibrated_confidence"] == 75

    def test_rejected_detections_not_in_features(self):
        """Rejected detections MUST NOT appear in the GeoJSON features list."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected_dict = _make_rejected_entry("net", 29, 0.18)
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected_dict],
        )
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        # Only accepted detection in features
        assert len(fc["features"]) == 1
        assert fc["features"][0]["properties"]["filter_status"] == "accepted"
        # Rejected appears in audit, not features
        for feat in fc["features"]:
            assert feat["properties"].get("class_name") != "net" or \
                   feat["properties"].get("filter_status") == "accepted"

    def test_rejected_in_audit_property(self):
        """Rejected detections appear in properties.rejected_audit when include_rejected=True."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected_dict = _make_rejected_entry("net", 29, 0.18)
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected_dict],
        )
        exporter = GeoJSONExporter()
        fc = exporter.export(result, include_rejected=True)
        assert fc["properties"]["rejected_count"] >= 1

    def test_output_to_file(self, tmp_path):
        """Writing to file produces valid JSON."""
        result = _make_result([_make_detection()])
        out_file = str(tmp_path / "test.geojson")
        exporter = GeoJSONExporter()
        exporter.export(result, output_file=out_file)
        assert os.path.exists(out_file)
        with open(out_file) as f:
            data = json.load(f)
        assert data["type"] == "FeatureCollection"

    def test_feature_collection_type_always_present(self):
        """type='FeatureCollection' always present even with zero detections."""
        result = _make_result([])
        fc = GeoJSONExporter().export(result)
        assert fc["type"] == "FeatureCollection"

    def test_sss_detection_optical_sensor_preserved(self):
        """Side-scan sonar detection preserves source_sensor correctly."""
        det_sss = _make_detection(
            class_name="net", class_id=29, source_sensor="side-scan sonar"
        )
        det_opt = _make_detection(
            class_name="bottle", class_id=0, source_sensor="optical"
        )
        result = _make_result([det_sss, det_opt])
        exporter = GeoJSONExporter()
        fc = exporter.export(result)
        sensors = [f["properties"]["source_sensor"] for f in fc["features"]]
        assert "side-scan sonar" in sensors
        assert "optical" in sensors

    def test_missing_optional_metadata_no_crash(self):
        """Detection with empty metadata does not crash exporter."""
        det = Detection(
            class_name="can",
            class_id=1,
            confidence=0.60,
            bbox=[5.0, 5.0, 50.0, 50.0],
            metadata={},
        )
        result = _make_result([det])
        fc = GeoJSONExporter().export(result)
        assert len(fc["features"]) == 1


# ===========================================================================
# S-100 EXPORTER TESTS
# ===========================================================================

class TestS100Exporter:
    """Tests for S100Exporter."""

    def test_empty_result_valid_catalog(self):
        """Zero detections → valid catalog with empty features list."""
        result = _make_result([])
        exporter = S100Exporter()
        catalog = exporter.export(result)
        assert "s100Header" in catalog
        assert catalog["features"] == []

    def test_header_contains_compliance_statement(self):
        """Header must contain PARTIAL_IMPLEMENTATION compliance statement."""
        result = _make_result([])
        catalog = S100Exporter().export(result)
        hdr = catalog["s100Header"]
        spec = hdr["specification"].upper()
        assert "PARTIAL" in spec or "PARTIAL" in hdr.get("complianceStatement", "").upper()

    def test_supported_fields_present(self):
        """Supported fields are present in each feature."""
        det = _make_detection("bottle", 0, 0.85)
        result = _make_result([det])
        catalog = S100Exporter().export(result)
        feature = catalog["features"][0]
        assert "classId" in feature
        assert "className" in feature
        assert "rawConfidence" in feature
        assert "sourceSensor" in feature
        assert "bboxPixels" in feature
        assert "filterStatus" in feature

    def test_unsupported_fields_are_null_not_fabricated(self):
        """depth, bathymetry, horizontal accuracy → null (not fabricated)."""
        det = _make_detection()
        result = _make_result([det])
        catalog = S100Exporter().export(result)
        feature = catalog["features"][0]
        assert feature["depthMeters"] is None
        assert feature["bathymetry"] is None
        assert feature["horizontalAccuracyMeters"] is None
        assert feature["qualityOfSounding"] is None

    def test_position_null_when_no_coords(self):
        """Position must be null/unavailable when no real coords exist."""
        det = _make_detection()  # no coords
        result = _make_result([det])
        catalog = S100Exporter().export(result)
        pos = catalog["features"][0]["position"]
        assert pos["latitude"] is None
        assert pos["longitude"] is None

    def test_position_filled_when_coords_available(self):
        """TEST ONLY coords: position filled from real metadata."""
        # Synthetic test coordinates — TEST ONLY
        det = _make_detection(latitude=9.5, longitude=76.2)
        result = _make_result([det])
        catalog = S100Exporter().export(result)
        pos = catalog["features"][0]["position"]
        assert pos["latitude"] == pytest.approx(9.5)
        assert pos["longitude"] == pytest.approx(76.2)

    def test_multiple_detections(self):
        """Multiple accepted detections → multiple features."""
        dets = [_make_detection("bottle", 0), _make_detection("net", 29)]
        result = _make_result(dets)
        catalog = S100Exporter().export(result)
        assert len(catalog["features"]) == 2

    def test_wrong_input_type_raises_validation_error(self):
        """Passing wrong type raises S100ExportValidationError."""
        exporter = S100Exporter()
        with pytest.raises(S100ExportValidationError):
            exporter.export({"not": "a DetectionResult"})

    def test_output_to_file(self, tmp_path):
        """Writing to file produces valid JSON."""
        result = _make_result([_make_detection()])
        out_file = str(tmp_path / "s100.json")
        S100Exporter().export(result, output_file=out_file)
        assert os.path.exists(out_file)
        with open(out_file) as f:
            data = json.load(f)
        assert "s100Header" in data

    def test_supported_fields_list_in_header(self):
        """Header documents what fields are supported."""
        result = _make_result([])
        catalog = S100Exporter().export(result)
        assert "supportedFields" in catalog["s100Header"]
        assert "unsupportedFields" in catalog["s100Header"]

    def test_sss_class29_net_taxonomy_preserved(self):
        """SSS class_id=29 (net) is correctly preserved."""
        det = _make_detection("net", 29, source_sensor="side-scan sonar")
        result = _make_result([det])
        catalog = S100Exporter().export(result)
        feat = catalog["features"][0]
        assert feat["classId"] == 29
        assert feat["className"] == "net"
        assert feat["sourceSensor"] == "side-scan sonar"

    def test_cfar_class27_unknown_object_taxonomy_preserved(self):
        """CA-CFAR class_id=27 (unknown-object) is correctly preserved."""
        det = _make_detection("unknown-object", 27, source_sensor="side-scan sonar")
        result = _make_result([det])
        catalog = S100Exporter().export(result)
        feat = catalog["features"][0]
        assert feat["classId"] == 27
        assert feat["className"] == "unknown-object"


# ===========================================================================
# PDF REPORT EXPORTER TESTS
# ===========================================================================

class TestPDFReportExporter:
    """Tests for PDFReportExporter.

    PDF generation requires reportlab. If reportlab is available, a PDF is
    produced. If a layout error occurs, a .txt fallback is produced.
    We test both paths by checking the returned file exists and is non-empty.
    """

    def test_empty_result_no_crash(self, tmp_path):
        """Zero detections → report generated without crash."""
        result = _make_result([])
        out = str(tmp_path / "report.pdf")
        exporter = PDFReportExporter()
        path = exporter.generate_report(result, output_file=out)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_single_detection_report(self, tmp_path):
        """One detection → report generated without crash."""
        result = _make_result([_make_detection("bottle", 0, 0.88)])
        out = str(tmp_path / "report.pdf")
        path = PDFReportExporter().generate_report(result, output_file=out)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_multiple_detections_report(self, tmp_path):
        """Multiple detections → report generated without crash."""
        dets = [
            _make_detection("bottle", 0, 0.88),
            _make_detection("net", 29, 0.72, source_sensor="side-scan sonar"),
            _make_detection("tire", 8, 0.65),
        ]
        rejected = _make_rejected_entry("unknown-object", 27, 0.18)
        result = _make_result(
            detections=dets,
            all_detections=[d.to_dict() for d in dets] + [rejected],
        )
        out = str(tmp_path / "report.pdf")
        path = PDFReportExporter().generate_report(result, output_file=out, mission_id="TEST-001")
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_missing_coordinates_no_fabrication(self, tmp_path):
        """Missing coordinates → 'unavailable' in report, not fake values."""
        det = _make_detection()  # no lat/lon
        result = _make_result([det])
        out = str(tmp_path / "report_nocoord.pdf")
        path = PDFReportExporter().generate_report(result, output_file=out)
        # If txt fallback produced, check text content
        if path.endswith(".txt"):
            with open(path) as f:
                content = f.read()
            assert "unavailable" in content.lower()
        # If PDF produced, just verify it was created (content checked in txt test)
        assert os.path.exists(path)

    def test_txt_fallback_contains_unavailable_for_missing_coords(self, tmp_path):
        """Plain-text fallback report explicitly says coordinates unavailable."""
        det = _make_detection()  # no lat/lon
        result = _make_result([det])
        exporter = PDFReportExporter()
        txt_out = str(tmp_path / "report_fallback.txt")
        exporter._generate_txt_fallback(result, txt_out, None, "2026-09-09 UTC")
        with open(txt_out) as f:
            content = f.read()
        assert "unavailable" in content.lower()
        assert "bottle" in content.lower()

    def test_txt_fallback_contains_rejection_info(self, tmp_path):
        """Plain-text fallback report includes rejected detection audit info."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected = _make_rejected_entry("net", 29, 0.18, "LOW_CONFIDENCE")
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected],
        )
        exporter = PDFReportExporter()
        txt_out = str(tmp_path / "report_rej.txt")
        exporter._generate_txt_fallback(result, txt_out, "MISSION-007", "2026-09-09 UTC")
        with open(txt_out) as f:
            content = f.read()
        assert "LOW_CONFIDENCE" in content
        assert "net" in content.lower()

    def test_no_temperature_battery_depth_in_report(self, tmp_path):
        """Report must NOT contain temperature, battery, depth sensor fields."""
        result = _make_result([_make_detection()])
        exporter = PDFReportExporter()
        txt_out = str(tmp_path / "scope_check.txt")
        exporter._generate_txt_fallback(result, txt_out, None, "2026-09-09 UTC")
        with open(txt_out) as f:
            content = f.read().lower()
        # These should not appear in the report
        forbidden = ["temperature", "battery", "battery_reserve", "imu", "compass"]
        for word in forbidden:
            assert word not in content, f"Forbidden field '{word}' found in report"

    def test_evidence_info_in_txt_fallback(self, tmp_path):
        """Evidence/filter information (rules, calibrated conf) in txt fallback."""
        det = _make_detection("bottle", 0, 0.88, calibrated_confidence=85)
        result = _make_result([det])
        exporter = PDFReportExporter()
        txt_out = str(tmp_path / "evidence_test.txt")
        exporter._generate_txt_fallback(result, txt_out, None, "2026-09-09 UTC")
        with open(txt_out) as f:
            content = f.read()
        assert "85" in content  # calibrated confidence
        assert "bottle" in content.lower()

    def test_empty_result_txt_fallback(self, tmp_path):
        """Empty result txt fallback shows zero detections, no crash."""
        result = _make_result([])
        exporter = PDFReportExporter()
        txt_out = str(tmp_path / "empty.txt")
        exporter._generate_txt_fallback(result, txt_out, None, "2026-09-09 UTC")
        with open(txt_out) as f:
            content = f.read()
        assert "No rejected detections recorded" in content


# ===========================================================================
# TABULAR EXPORTER TESTS (CSV + JSON)
# ===========================================================================

class TestTabularExporter:
    """Tests for TabularExporter (CSV and JSON)."""

    # -----------------------------------------------------------------------
    # CSV tests
    # -----------------------------------------------------------------------

    def test_csv_headers_correct(self):
        """CSV header row matches TABULAR_FIELDS exactly."""
        result = _make_result([])
        csv_str = TabularExporter().export_csv(result)
        reader = csv.DictReader(io.StringIO(csv_str))
        assert list(reader.fieldnames) == TABULAR_FIELDS

    def test_csv_empty_result(self):
        """Zero detections → CSV header only, no data rows."""
        result = _make_result([])
        csv_str = TabularExporter().export_csv(result, include_rejected=False)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert rows == []

    def test_csv_single_accepted_detection(self):
        """One accepted detection → one data row."""
        det = _make_detection("bottle", 0, 0.88)
        result = _make_result([det])
        csv_str = TabularExporter().export_csv(result, include_rejected=False)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["class_name"] == "bottle"
        assert rows[0]["filter_status"] == "accepted"
        assert rows[0]["rejection_rule"] == ""
        assert rows[0]["rejection_reason"] == ""

    def test_csv_multiple_detections(self):
        """Multiple detections → multiple rows."""
        dets = [
            _make_detection("bottle", 0),
            _make_detection("net", 29, source_sensor="side-scan sonar"),
            _make_detection("tire", 8),
        ]
        result = _make_result(dets)
        csv_str = TabularExporter().export_csv(result, include_rejected=False)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 3

    def test_csv_null_coords_are_empty_string(self):
        """Null latitude/longitude → empty string in CSV."""
        det = _make_detection()  # no coords
        result = _make_result([det])
        csv_str = TabularExporter().export_csv(result, include_rejected=False)
        reader = csv.DictReader(io.StringIO(csv_str))
        row = list(reader)[0]
        assert row["latitude"] == ""
        assert row["longitude"] == ""

    def test_csv_coords_filled_when_available(self):
        """TEST ONLY coords: real coords → filled in CSV."""
        # Synthetic test coordinates — TEST ONLY
        det = _make_detection(latitude=11.0, longitude=77.0)
        result = _make_result([det])
        csv_str = TabularExporter().export_csv(result, include_rejected=False)
        reader = csv.DictReader(io.StringIO(csv_str))
        row = list(reader)[0]
        assert row["latitude"] == "11.0"
        assert row["longitude"] == "77.0"

    def test_csv_rejected_detections_included(self):
        """include_rejected=True → rejected detections appear with rejection info."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected = _make_rejected_entry("net", 29, 0.18, "LOW_CONFIDENCE")
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected],
        )
        csv_str = TabularExporter().export_csv(result, include_rejected=True)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        statuses = [r["filter_status"] for r in rows]
        assert "accepted" in statuses
        assert "rejected" in statuses

    def test_csv_rejected_clearly_marked(self):
        """Rejected row has filter_status='rejected' and rejection_rule set."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected = _make_rejected_entry("net", 29, 0.18, "LOW_CONFIDENCE")
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected],
        )
        csv_str = TabularExporter().export_csv(result, include_rejected=True)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        rej_rows = [r for r in rows if r["filter_status"] == "rejected"]
        assert len(rej_rows) >= 1
        assert rej_rows[0]["rejection_rule"] == "LOW_CONFIDENCE"
        assert rej_rows[0]["class_name"] == "net"

    def test_csv_confidence_values(self):
        """Confidence values are correct in CSV output."""
        det = _make_detection("bottle", 0, 0.88, calibrated_confidence=85)
        result = _make_result([det])
        csv_str = TabularExporter().export_csv(result, include_rejected=False)
        reader = csv.DictReader(io.StringIO(csv_str))
        row = list(reader)[0]
        assert float(row["raw_confidence"]) == pytest.approx(0.88, abs=1e-4)
        assert row["calibrated_confidence"] == "85"

    def test_csv_sensor_information(self):
        """Source sensor preserved correctly in CSV."""
        det_sss = _make_detection("net", 29, source_sensor="side-scan sonar")
        det_opt = _make_detection("bottle", 0, source_sensor="optical")
        result = _make_result([det_sss, det_opt])
        csv_str = TabularExporter().export_csv(result, include_rejected=False)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        sensors = [r["source_sensor"] for r in rows]
        assert "side-scan sonar" in sensors
        assert "optical" in sensors

    def test_csv_output_to_file(self, tmp_path):
        """CSV written to file is readable."""
        result = _make_result([_make_detection()])
        out_file = str(tmp_path / "detections.csv")
        TabularExporter().export_csv(result, output_file=out_file)
        assert os.path.exists(out_file)
        with open(out_file) as f:
            content = f.read()
        assert "class_name" in content

    # -----------------------------------------------------------------------
    # JSON tests
    # -----------------------------------------------------------------------

    def test_json_schema_field_present(self):
        """JSON output contains 'schema' key with field list."""
        result = _make_result([])
        json_str = TabularExporter().export_json(result)
        data = json.loads(json_str)
        assert "schema" in data
        assert data["schema"] == TABULAR_FIELDS

    def test_json_empty_result(self):
        """Zero detections → JSON with empty detections array."""
        result = _make_result([])
        json_str = TabularExporter().export_json(result, include_rejected=False)
        data = json.loads(json_str)
        assert data["detections"] == []
        assert data["accepted_count"] == 0

    def test_json_single_detection(self):
        """One detection → one entry in detections array."""
        det = _make_detection("bottle", 0, 0.88)
        result = _make_result([det])
        json_str = TabularExporter().export_json(result, include_rejected=False)
        data = json.loads(json_str)
        assert len(data["detections"]) == 1
        assert data["detections"][0]["class_name"] == "bottle"

    def test_json_null_values_are_json_null(self):
        """Missing latitude/longitude → JSON null (not empty string)."""
        det = _make_detection()  # no coords
        result = _make_result([det])
        json_str = TabularExporter().export_json(result, include_rejected=False)
        data = json.loads(json_str)
        assert data["detections"][0]["latitude"] is None
        assert data["detections"][0]["longitude"] is None

    def test_json_multiple_detections(self):
        """Multiple detections → correct count."""
        dets = [_make_detection(), _make_detection("net", 29), _make_detection("tire", 8)]
        result = _make_result(dets)
        json_str = TabularExporter().export_json(result, include_rejected=False)
        data = json.loads(json_str)
        assert len(data["detections"]) == 3

    def test_json_rejected_included(self):
        """Rejected detections appear in JSON when include_rejected=True."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected = _make_rejected_entry("net", 29, 0.18, "LOW_CONFIDENCE")
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected],
        )
        json_str = TabularExporter().export_json(result, include_rejected=True)
        data = json.loads(json_str)
        statuses = [d["filter_status"] for d in data["detections"]]
        assert "accepted" in statuses
        assert "rejected" in statuses
        assert data["rejected_count"] >= 1

    def test_json_role3_summary_present(self):
        """role3_summary from DetectionResult is included in JSON output."""
        result = _make_result([_make_detection()])
        json_str = TabularExporter().export_json(result)
        data = json.loads(json_str)
        assert "role3_summary" in data
        assert data["role3_summary"] is not None

    def test_json_output_to_file(self, tmp_path):
        """JSON written to file is readable."""
        result = _make_result([_make_detection()])
        out_file = str(tmp_path / "detections.json")
        TabularExporter().export_json(result, output_file=out_file)
        assert os.path.exists(out_file)
        with open(out_file) as f:
            data = json.load(f)
        assert "detections" in data


# ===========================================================================
# CROSS-EXPORTER: REJECTED NOT CONFUSED WITH ACCEPTED
# ===========================================================================

class TestRejectedNotReportedAsAccepted:
    """Verify that rejected detections are never accidentally exported as accepted."""

    def test_geojson_features_are_all_accepted(self):
        """All GeoJSON features must have filter_status='accepted'."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected_dict = _make_rejected_entry("net", 29, 0.18)
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected_dict],
        )
        fc = GeoJSONExporter().export(result)
        for feat in fc["features"]:
            assert feat["properties"]["filter_status"] == "accepted", \
                f"Feature with status {feat['properties']['filter_status']} found in features list"

    def test_s100_features_are_all_accepted(self):
        """All S-100 features must have filterStatus='accepted'."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected_dict = _make_rejected_entry("net", 29, 0.18)
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected_dict],
        )
        catalog = S100Exporter().export(result)
        for feat in catalog["features"]:
            assert feat["filterStatus"] == "accepted", \
                f"Feature with filterStatus {feat['filterStatus']} found in S-100 features list"

    def test_csv_accepted_rows_all_accepted(self):
        """Accepted CSV rows must not have rejection info."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected = _make_rejected_entry("net", 29, 0.18)
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected],
        )
        csv_str = TabularExporter().export_csv(result, include_rejected=True)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        accepted_rows = [r for r in rows if r["filter_status"] == "accepted"]
        for row in accepted_rows:
            assert row["rejection_rule"] == ""
            assert row["rejection_reason"] == ""

    def test_json_accepted_entries_have_no_rejection_rule(self):
        """Accepted JSON entries must not have rejection_rule set."""
        accepted = _make_detection("bottle", 0, 0.85)
        rejected = _make_rejected_entry("net", 29, 0.18)
        result = _make_result(
            detections=[accepted],
            all_detections=[accepted.to_dict(), rejected],
        )
        json_str = TabularExporter().export_json(result, include_rejected=True)
        data = json.loads(json_str)
        for entry in data["detections"]:
            if entry["filter_status"] == "accepted":
                assert entry["rejection_rule"] is None
                assert entry["rejection_reason"] is None
