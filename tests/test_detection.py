"""
Unit Tests for Module 2 — Detection, Detector Service, Pipelines & Schemas
"""

import io
from pathlib import Path
import pytest
import numpy as np
from PIL import Image

from data.test_data.sample_frames import FrameReplayHarness
from marineguard.detection.side_scan import SideScanDetector
from marineguard.detection.sas import SASDetector
from marineguard.detection.optical import OpticalDetector
from marineguard.detection.bathymetry import BathymetryDetector
from marineguard.detection.fusion import MultiSensorFusionEngine
from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.detector import BaseDetector, MockDetector, YOLODetector
from marineguard.detection.model_loader import MarineDebrisModel, ModelNotFoundError
from marineguard.detection.preprocessing import DefaultPreprocessor
from marineguard.detection.postprocessing import PostProcessor
from marineguard.detection.pipeline import ImageDetectionPipeline, ImageValidationError
from marineguard.detection.annotator import ImageAnnotator
from marineguard.detection.video_pipeline import VideoDetectionPipeline


# ---------------------------------------------------------------------------
# 1. Schema & Serialization Tests
# ---------------------------------------------------------------------------

def test_structured_detection_schema():
    det = Detection(
        class_name="plastic-bottle",
        class_id=0,
        confidence=0.91234,
        bbox=[120.0, 80.0, 240.0, 310.0],
    )
    d = det.to_dict()
    assert d["class"] == "plastic-bottle"
    assert d["confidence"] == 0.9123
    assert d["bbox"] == [120.0, 80.0, 240.0, 310.0]
    assert d["class_id"] == 0

    result = DetectionResult.from_detections(
        detections=[det],
        image_width=640,
        image_height=480,
        inference_time_ms=12.5,
    )
    api_dict = result.to_api_dict()
    assert api_dict["count"] == 1
    assert len(api_dict["detections"]) == 1
    assert api_dict["detections"][0]["class"] == "plastic-bottle"
    assert api_dict["image_width"] == 640
    assert api_dict["image_height"] == 480
    assert api_dict["inference_time_ms"] == 12.5


def test_empty_detections_schema():
    result = DetectionResult.from_detections(detections=[])
    assert result.count == 0
    api_dict = result.to_api_dict()
    assert api_dict == {"detections": [], "count": 0}


# ---------------------------------------------------------------------------
# 2. Detector Interface & Test Doubles
# ---------------------------------------------------------------------------

def test_mock_detector_interface():
    mock_data = [
        {"class": "tire", "class_id": 8, "confidence": 0.88, "bbox": [50.0, 60.0, 150.0, 160.0]}
    ]
    detector = MockDetector(mock_detections=mock_data)
    assert detector.is_ready is True
    assert "MockDetector" in detector.model_name

    img = np.zeros((480, 640, 3), dtype=np.uint8)
    res = detector.detect(img)
    assert res.count == 1
    assert res.detections[0].class_name == "tire"
    assert res.detections[0].confidence == 0.88


def test_missing_model_handling():
    """Verify production YOLO detector raises ModelNotFoundError when best.pt is absent."""
    non_existent_weights = Path("models/definitely_missing_weights_12345.pt")
    loader = MarineDebrisModel(model_path=non_existent_weights)
    assert loader.is_loaded is False

    with pytest.raises(ModelNotFoundError) as exc_info:
        loader.predict(np.zeros((100, 100, 3), dtype=np.uint8))
    assert "not found" in str(exc_info.value).lower()

    yolo_detector = YOLODetector(model_path=non_existent_weights)
    assert yolo_detector.is_ready is False
    with pytest.raises(ModelNotFoundError):
        yolo_detector.detect(np.zeros((100, 100, 3), dtype=np.uint8))


# ---------------------------------------------------------------------------
# 3. Post-Processing & BBox Validation
# ---------------------------------------------------------------------------

def test_postprocessor_clipping_and_thresholding():
    taxonomy = {0: "bottle", 1: "can"}
    postprocessor = PostProcessor(confidence_threshold=0.50, taxonomy=taxonomy)

    raw_result = DetectionResult.from_detections([
        # Valid detection
        Detection(class_name="bottle", class_id=0, confidence=0.85, bbox=[10.0, 20.0, 100.0, 150.0]),
        # Below confidence threshold
        Detection(class_name="can", class_id=1, confidence=0.30, bbox=[50.0, 50.0, 80.0, 80.0]),
        # Out-of-bounds box (should be clipped)
        Detection(class_name="bottle", class_id=0, confidence=0.90, bbox=[-10.0, -20.0, 700.0, 550.0]),
        # Degenerate box (zero area)
        Detection(class_name="bottle", class_id=0, confidence=0.95, bbox=[50.0, 50.0, 50.0, 50.0]),
    ])

    cleaned = postprocessor.process(raw_result, image_width=640, image_height=480)
    assert cleaned.count == 2
    assert cleaned.detections[0].confidence == 0.85
    assert cleaned.detections[0].bbox == [10.0, 20.0, 100.0, 150.0]

    # Check clipped box
    clipped_det = cleaned.detections[1]
    assert clipped_det.confidence == 0.90
    assert clipped_det.bbox == [0.0, 0.0, 640.0, 480.0]


def test_official_class_mapping_taxonomy():
    taxonomy_file = Path(__file__).resolve().parents[1] / "marineguard_classes.yaml"
    if taxonomy_file.exists():
        loader = MarineDebrisModel.get(classes_path=taxonomy_file)
        assert len(loader.class_names) >= 10
        assert loader.class_names[0] == "bottle"
        assert loader.class_names[1] == "can"


# ---------------------------------------------------------------------------
# 4. Image Pipeline & Validation Tests
# ---------------------------------------------------------------------------

def test_image_pipeline_with_mock_detector():
    mock_det = MockDetector(mock_detections=[
        {"class": "plastic-bottle", "confidence": 0.94, "bbox": [100.0, 100.0, 200.0, 250.0]}
    ])
    pipeline = ImageDetectionPipeline(detector=mock_det)

    # Test with numpy image
    img = np.full((300, 400, 3), 128, dtype=np.uint8)
    res = pipeline.process(img)
    assert res.count == 1
    assert res.detections[0].class_name == "plastic-bottle"
    assert res.image_width == 400
    assert res.image_height == 300

    # Test with PIL image
    pil_img = Image.fromarray(img)
    res_pil = pipeline.process(pil_img)
    assert res_pil.count == 1

    # Test with raw image bytes (PNG)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    res_bytes = pipeline.process(png_bytes)
    assert res_bytes.count == 1


def test_image_pipeline_invalid_inputs():
    pipeline = ImageDetectionPipeline(detector=MockDetector())

    # Empty bytes
    with pytest.raises(ImageValidationError):
        pipeline.process(b"")

    # Corrupted bytes
    with pytest.raises(ImageValidationError):
        pipeline.process(b"not_an_image_random_bytes_12345")

    # Non-existent path
    with pytest.raises(ImageValidationError):
        pipeline.process("non_existent_image_file_path.png")

    # Empty numpy array
    with pytest.raises(ImageValidationError):
        pipeline.process(np.array([]))


# ---------------------------------------------------------------------------
# 5. Annotation Tests
# ---------------------------------------------------------------------------

def test_image_annotator():
    annotator = ImageAnnotator()
    base_img = np.zeros((300, 400, 3), dtype=np.uint8)

    detections = [
        Detection(class_name="plastic-bottle", confidence=0.91, bbox=[50.0, 50.0, 150.0, 200.0]),
        Detection(class_name="tire", confidence=0.84, bbox=[200.0, 100.0, 280.0, 180.0]),
    ]
    result = DetectionResult.from_detections(detections=detections)

    annotated = annotator.annotate(base_img, result)
    assert isinstance(annotated, Image.Image)
    assert annotated.size == (400, 300)

    # Verify zero detections doesn't crash
    annotated_empty = annotator.annotate(base_img, DetectionResult.from_detections([]))
    assert annotated_empty.size == (400, 300)


# ---------------------------------------------------------------------------
# 6. Video Pipeline & Stream Tests
# ---------------------------------------------------------------------------

def test_video_frame_stream_processing():
    mock_det = MockDetector(mock_detections=[
        {"class": "ghost-net", "confidence": 0.89, "bbox": [30.0, 40.0, 120.0, 180.0]}
    ])
    pipeline = ImageDetectionPipeline(detector=mock_det)
    video_pipeline = VideoDetectionPipeline(pipeline=pipeline)

    def frame_generator():
        for _ in range(3):
            yield np.zeros((240, 320, 3), dtype=np.uint8)

    stream = video_pipeline.process_frame_stream(frame_generator())
    results_list = list(stream)

    assert len(results_list) == 3
    for det_res, annotated_frame in results_list:
        assert det_res.count == 1
        assert det_res.detections[0].class_name == "ghost-net"
        assert isinstance(annotated_frame, Image.Image)


# ---------------------------------------------------------------------------
# 7. Existing Multi-Sensor Pipelines & Fusion
# ---------------------------------------------------------------------------

def test_detection_pipelines_and_fusion():
    harness = FrameReplayHarness()
    ping = harness.get_next_ping()

    side_scan = SideScanDetector()
    optical = OpticalDetector()
    bathy = BathymetryDetector()
    fusion = MultiSensorFusionEngine()

    c_sonar = side_scan.process_waterfall_ping(ping)
    c_optical = optical.process_optical_frame(ping)
    c_bathy = bathy.process_bathymetry_grid(ping)

    assert len(c_sonar) > 0
    assert len(c_optical) > 0
    assert len(c_bathy) > 0

    all_contacts = c_sonar + c_optical + c_bathy
    target = fusion.fuse(all_contacts)

    assert target.confidence >= 0.80
    assert "side_scan" in target.sensor_contributions
    assert "optical" in target.sensor_contributions
    assert "bathymetry" in target.sensor_contributions
    assert target.removal_priority in ["HIGH", "MEDIUM", "LOW"]
