"""
Unit & Integration Tests for Member 5 — UI Dashboard & System Integration
Verifies:
1. Trimmed MCP server (detection & reporting only; no vehicle controls).
2. Real benchmark calculations in eval.py (F1, FPR, real latency).
3. Confidence filtering (threshold changes affect accepted/filtered counts).
4. No coordinate fabrication (missing coordinates remain missing).
5. Deletion of COMPLETE_MARINEGUARD_CODEBASE.py.
6. Trimmed config.yaml (model/fusion present, firewall telemetry absent).
"""

import os
from pathlib import Path
import pytest
import yaml
from marineguard.mcp_server import MarineGuardMCPServer
from marineguard.schemas import ClassifiedTarget
import eval as eval_module


def test_trimmed_mcp_server():
    """Verify that MCP server exposes detection & reporting tools and no vehicle actions."""
    server = MarineGuardMCPServer()

    # 1. trigger_close_inspection must not exist
    assert not hasattr(server, "trigger_close_inspection")

    # 2. Registry tools emitted must not contain vehicle action commands
    emitted_names = [t.get("name", "").lower() for t in server.registry.tools_emitted]
    for prohibited in ["control", "navigate", "steer", "altitude", "thruster", "motor"]:
        assert not any(prohibited in name for name in emitted_names), f"Prohibited tool {prohibited} found in MCP tools"

    # 3. Detection and reporting must work cleanly
    survey = server.marine_debris_survey("Sagar Netra", confidence_threshold=0.75)
    assert survey["status"] == "COMPLETED"
    assert "targets_accepted" in survey
    assert "targets_filtered" in survey
    assert len(survey["classified_targets"]) == survey["targets_accepted"]


def test_eval_pipeline_real_benchmarks():
    """Verify eval.py calculates real metrics empirically without hardcoded strings."""
    metrics = eval_module.evaluate_pipeline(num_iterations=20, confidence_threshold=0.70)

    assert isinstance(metrics["f1_score"], float)
    assert 0.0 <= metrics["f1_score"] <= 1.0
    assert isinstance(metrics["precision"], float)
    assert 0.0 <= metrics["precision"] <= 1.0
    assert isinstance(metrics["recall"], float)
    assert 0.0 <= metrics["recall"] <= 1.0
    assert isinstance(metrics["false_positive_rate"], float)
    assert 0.0 <= metrics["false_positive_rate"] <= 1.0
    assert metrics["latency_mean_ms"] > 0.0
    assert metrics["samples_evaluated"] >= 20
    assert metrics["true_positives"] + metrics["false_negatives"] > 0


def test_confidence_filtering_logic():
    """Verify that confidence threshold slider actually alters accepted vs filtered targets."""
    server = MarineGuardMCPServer()

    # Low threshold accepts all
    low_res = server.marine_debris_survey("Sagar Netra", confidence_threshold=0.50)
    # Very high threshold filters some or all
    high_res = server.marine_debris_survey("Sagar Netra", confidence_threshold=0.98)

    assert low_res["targets_accepted"] >= high_res["targets_accepted"]
    assert high_res["targets_filtered"] >= low_res["targets_filtered"]


def test_no_coordinate_fabrication():
    """Verify that coordinates are preserved if present and never fabricated if absent."""
    server = MarineGuardMCPServer()
    survey = server.marine_debris_survey("Sagar Netra")

    for target_dict in survey["classified_targets"]:
        target = ClassifiedTarget(**target_dict)
        if target.lat_lon is not None:
            # Must not be fabricated dummy (0, 0)
            assert target.lat_lon != (0.0, 0.0)
            assert -90.0 <= target.lat_lon[0] <= 90.0
            assert -180.0 <= target.lat_lon[1] <= 180.0


def test_obsolete_codebase_file_deleted():
    """Verify that COMPLETE_MARINEGUARD_CODEBASE.py has been deleted."""
    repo_root = Path(__file__).resolve().parent.parent
    obsolete_file = repo_root / "COMPLETE_MARINEGUARD_CODEBASE.py"
    assert not obsolete_file.exists(), "COMPLETE_MARINEGUARD_CODEBASE.py should have been deleted"


def test_trimmed_config_yaml():
    """Verify config.yaml contains model/fusion and does not contain firewall telemetry."""
    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Required sections
    assert "compiler" in config
    assert "models" in config["compiler"]
    assert "fusion" in config["compiler"]
    assert "exporters" in config

    # Firewall telemetry section must be excised
    assert "firewall" not in config, "firewall section should be excised from config.yaml"


def test_authoritative_sss_model_integrity():
    """Verify authoritative YOLOv8n SSS weights (Exp #2) exist and match SHA256."""
    from marineguard.detection.sss_yolo_adapter import verify_model_integrity, AUTHORITATIVE_MODEL_PATH
    is_ok, sha, msg = verify_model_integrity()
    assert is_ok, f"Model verification failed: {msg}"
    assert sha == "c9fd27940b9b1a28834002dcbc40d1306c3e56650309b536aecd9862236bd7d2"


def test_real_sss_yolo_inference_and_boxes():
    """Verify real YOLOv8n inference on SSS image produces real bounding boxes."""
    from marineguard.detection.sss_yolo_adapter import run_sss_pipeline
    test_img = "data/processed/marineguard_sss/images/test/synth_ghost_net_00001.png"
    assert os.path.exists(test_img), f"Test SSS image missing: {test_img}"

    res = run_sss_pipeline(test_img, confidence_threshold=0.70)
    assert res["status"] == "COMPLETED"
    assert res["raw_detections_count"] >= 1
    assert res["accepted_count"] >= 1

    first_det = res["accepted_detections"][0]
    assert first_det["species"] == "ghost_net"
    assert first_det["confidence"] > 0.85

    # Verify bounding box is real floating-point tensor output and NOT hardcoded (100,100,150,150)
    bbox = first_det["bbox"]
    assert len(bbox) == 4
    assert bbox != [100.0, 100.0, 150.0, 150.0], "BBox must not be placeholder (100,100,150,150)"
    assert bbox[2] > bbox[0]
    assert bbox[3] > bbox[1]


def test_sss_negative_seabed_rejection():
    """Verify clean background seabed image produces 0 false positive detections."""
    from marineguard.detection.sss_yolo_adapter import run_sss_pipeline
    bg_img = "data/processed/marineguard_sss/images/test/bg_1693569243.750_x2500.jpg"
    assert os.path.exists(bg_img), f"Background SSS image missing: {bg_img}"

    res = run_sss_pipeline(bg_img, confidence_threshold=0.50)
    assert res["status"] == "COMPLETED"
    assert res["raw_detections_count"] == 0
    assert res["accepted_count"] == 0


def test_role3_filtering_on_sss_yolo():
    """Verify Role 3 post-processing dynamically rejects low confidence and invalid geometry."""
    from marineguard.detection.sss_yolo_adapter import filter_yolo_detections

    sample_dets = [
        {"detection_index": 0, "class_id": 0, "raw_class": "net", "species": "ghost_net", "confidence": 0.92, "bbox": [100.0, 100.0, 200.0, 200.0], "bbox_area": 10000.0},
        {"detection_index": 1, "class_id": 0, "raw_class": "net", "species": "ghost_net", "confidence": 0.65, "bbox": [150.0, 150.0, 250.0, 250.0], "bbox_area": 10000.0},
        {"detection_index": 2, "class_id": 0, "raw_class": "net", "species": "ghost_net", "confidence": 0.90, "bbox": [10.0, 10.0, 12.0, 12.0], "bbox_area": 4.0},  # tiny box
    ]

    accepted, rejected = filter_yolo_detections(sample_dets, confidence_threshold=0.75, min_box_size=4.0)
    assert len(accepted) == 1
    assert accepted[0]["detection_index"] == 0
    assert len(rejected) == 2
    assert "LOW_CONFIDENCE" in rejected[0]["reason"]
    assert "TINY_BBOX" in rejected[1]["reason"]


def test_fastapi_health_endpoint():
    """Verify GET /api/health reports real model SHA and active status."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["sss_model"] == "loaded"
    assert data["model_sha256"] == "c9fd27940b9b1a28834002dcbc40d1306c3e56650309b536aecd9862236bd7d2"


def test_fastapi_real_detect_endpoint():
    """Verify POST /api/detect executes real YOLOv8n inference on positive sample."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    res = client.post("/api/detect", json={"sampleKey": "sample_01", "confidenceThreshold": 0.70})
    assert res.status_code == 200
    data = res.json()
    assert data["totalDetections"] >= 1
    assert data["acceptedCount"] >= 1
    first_det = data["detections"][0]
    assert first_det["species"] == "ghost_net"
    assert first_det["confidence"] > 0.85
    assert first_det["status"] == "accepted"


def test_fastapi_negative_control_detect_endpoint():
    """Verify POST /api/detect on negative seabed sample yields 0 detections."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    res = client.post("/api/detect", json={"sampleKey": "sample_bg", "confidenceThreshold": 0.50})
    assert res.status_code == 200
    data = res.json()
    assert data["totalDetections"] == 0
    assert data["acceptedCount"] == 0


def test_fastapi_reports_generation_and_download():
    """Verify POST /api/reports generates real report and download endpoint returns file."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    # Generate PDF
    gen_res = client.post("/api/reports", json={"format": "PDF"})
    assert gen_res.status_code == 200
    report_info = gen_res.json()
    assert report_info["format"] == "PDF"

    # Download PDF
    dl_res = client.get(report_info["downloadUrl"])
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 100


# ==============================================================================
# Requirement 18: Comprehensive Integration & Verification Tests (A through J)
# ==============================================================================

def test_req18_a_demo_samples_endpoint():
    """Requirement 18A: Verify GET /api/demo-samples returns repository demo samples."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    res = client.get("/api/demo-samples")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["count"] >= 3
    sample_ids = [s["id"] for s in data["samples"]]
    assert "ghost_net_contact_01" in sample_ids
    assert "background_seabed" in sample_ids


def test_req18_b_builtin_positive_sample():
    """Requirement 18B: Verify built-in positive sample produces expected YOLO detection."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    res = client.post("/api/detect", json={"sampleKey": "ghost_net_contact_01", "confidenceThreshold": 0.70})
    assert res.status_code == 200
    data = res.json()
    assert data["totalDetections"] == 1
    assert data["acceptedCount"] == 1
    det = data["detections"][0]
    assert det["species"] == "ghost_net"
    assert 0.90 < det["confidence"] < 0.98
    # Bounding box near [113.6, 210.6, 226.2, 319.3]
    x1, y1, x2, y2 = det["bbox"]
    assert 100.0 < x1 < 130.0
    assert 195.0 < y1 < 225.0
    assert 210.0 < x2 < 240.0
    assert 300.0 < y2 < 335.0


def test_req18_c_builtin_negative_sample():
    """Requirement 18C: Verify built-in negative control sample yields 0 detections from real model."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    res = client.post("/api/detect", json={"sampleKey": "background_seabed", "confidenceThreshold": 0.50})
    assert res.status_code == 200
    data = res.json()
    assert data["totalDetections"] == 0
    assert data["acceptedCount"] == 0
    assert data["filteredCount"] == 0
    assert len(data["detections"]) == 0


def test_req18_d_and_e_manual_image_upload_and_inference():
    """Requirement 18D & 18E: Verify POST /api/upload receives real bytes, decodes, executes real YOLO inference, and returns DetectionResult."""
    import io
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    # Read genuine test image
    with open("data/demo_sss/ghost_net_contact_01.png", "rb") as f:
        img_bytes = f.read()

    files = {"file": ("manual_upload_test.png", io.BytesIO(img_bytes), "image/png")}
    data = {"confidenceThreshold": "0.75"}
    res = client.post("/api/upload", files=files, data=data)
    assert res.status_code == 200
    res_data = res.json()

    # Verify upload was stored and analyzed
    assert res_data["fileId"].startswith("upload_")
    assert res_data["filename"] == "manual_upload_test.png"
    assert res_data["totalDetections"] >= 1
    assert res_data["acceptedCount"] >= 1
    assert "annotatedImageUrl" in res_data
    assert "detections" in res_data
    assert res_data["detections"][0]["species"] == "ghost_net"
    assert res_data["modelSha256"] == "c9fd27940b9b1a28834002dcbc40d1306c3e56650309b536aecd9862236bd7d2"


def test_req18_f_role3_filtering_threshold():
    """Requirement 18F: Verify changing confidence threshold gates detection verdict dynamically."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    # At conf=0.80, detection is ACCEPTED (conf is ~0.937)
    res_low = client.post("/api/detect", json={"sampleKey": "ghost_net_contact_01", "confidenceThreshold": 0.80})
    assert res_low.status_code == 200
    assert res_low.json()["acceptedCount"] == 1
    assert res_low.json()["filteredCount"] == 0
    assert res_low.json()["detections"][0]["status"] == "accepted"

    # At conf=0.98, detection is FILTERED (conf ~0.937 < 0.98)
    res_high = client.post("/api/detect", json={"sampleKey": "ghost_net_contact_01", "confidenceThreshold": 0.98})
    assert res_high.status_code == 200
    assert res_high.json()["acceptedCount"] == 0
    assert res_high.json()["filteredCount"] == 1
    assert res_high.json()["detections"][0]["status"] == "filtered"
    assert "LOW_CONFIDENCE" in res_high.json()["detections"][0]["rejectionReason"]


def test_req18_g_invalid_image_upload():
    """Requirement 18G: Verify uploading invalid/corrupt image bytes returns 400 error."""
    import io
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    fake_bytes = b"NOT_A_VALID_IMAGE_DATA_CORRUPT"
    files = {"file": ("corrupt.png", io.BytesIO(fake_bytes), "image/png")}
    res = client.post("/api/upload", files=files)
    assert res.status_code == 400
    assert "could not be decoded" in res.json()["detail"]


def test_req18_h_missing_file():
    """Requirement 18H: Verify requesting non-existent fileId/sampleKey returns 404 error."""
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    res = client.post("/api/detect", json={"sampleKey": "completely_non_existent_key_999"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


def test_req18_i_gps_unavailable_handling():
    """Requirement 18I: Verify that manual upload without telemetry correctly marks GPS unavailable."""
    import io
    from fastapi.testclient import TestClient
    from api_server import app

    client = TestClient(app)
    with open("data/demo_sss/background_seabed.png", "rb") as f:
        img_bytes = f.read()

    files = {"file": ("negative_test.png", io.BytesIO(img_bytes), "image/png")}
    res = client.post("/api/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["hasGps"] is False
    assert data["gpsCoordinates"] is None
    assert "Geolocation unavailable" in data["gpsMessage"]



