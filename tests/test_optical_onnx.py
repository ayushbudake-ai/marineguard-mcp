# Role 2: Optical ONNX Segmentation Pipeline Integration Tests
import io
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
import onnx
import onnxruntime as ort

from marineguard.detection.optical import OpticalDetector
from marineguard.detection.detector import ONNXOpticalDetector, YOLODetector
from marineguard.detection.pipeline import ImageDetectionPipeline, ImageValidationError
from marineguard.detection.model_loader import MarineDebrisModel, ModelNotFoundError
from marineguard.detection.schema import DetectionResult, Detection
from marineguard.detection.annotator import ImageAnnotator

REPO_ROOT = Path(__file__).resolve().parents[1]
ONNX_PATH = REPO_ROOT / 'runs' / 'seaclear_yolov8n_seg' / 'onnx' / 'best.onnx'
PT_PATH = REPO_ROOT / 'runs' / 'seaclear_yolov8n_seg' / 'train' / 'weights' / 'best.pt'
VAL_IMG_DIR = REPO_ROOT / 'data' / 'processed' / 'seaclear_segmentation' / 'images' / 'val'

def test_optical_onnx_model_loading():
    assert ONNX_PATH.exists(), f'Missing ONNX model at {ONNX_PATH}'
    onnx_model = onnx.load(str(ONNX_PATH))
    onnx.checker.check_model(onnx_model)
    session = ort.InferenceSession(str(ONNX_PATH), providers=['CPUExecutionProvider'])
    inputs = [inp.name for inp in session.get_inputs()]
    outputs = [out.name for out in session.get_outputs()]
    assert 'images' in inputs
    assert 'output0' in outputs
    assert 'output1' in outputs
    detector = ONNXOpticalDetector(model_path=ONNX_PATH)
    assert detector.is_ready is True
    assert 'best.onnx' in detector.model_name

def test_optical_onnx_valid_image_inference():
    test_img_path = VAL_IMG_DIR / '1009.jpg'
    if not test_img_path.exists():
        pytest.skip(f'Missing test image {test_img_path}')
    optical_detector = OpticalDetector(model_path=ONNX_PATH, confidence_threshold=0.25)
    assert optical_detector.is_model_loaded is True
    result = optical_detector.detect_image(test_img_path)
    assert isinstance(result, DetectionResult)
    assert result.status == 'SUCCESS'
    assert result.count >= 1
    assert result.image_width == 1920
    assert result.image_height == 1080
    assert result.inference_time_ms is not None and result.inference_time_ms > 0
    for det in result.detections:
        assert isinstance(det.class_name, str) and len(det.class_name) > 0
        assert det.class_id is not None and 0 <= det.class_id < 50
        assert 0.0 <= det.confidence <= 1.0
        assert len(det.bbox) == 4
        x1, y1, x2, y2 = det.bbox
        assert 0 <= x1 < x2 <= result.image_width
        assert 0 <= y1 < y2 <= result.image_height
        if det.segmentation is not None:
            assert isinstance(det.segmentation, list)
            assert len(det.segmentation) >= 3
            for pt in det.segmentation:
                assert len(pt) == 2

def test_optical_onnx_no_detection_case():
    detector = ONNXOpticalDetector(model_path=ONNX_PATH, confidence_threshold=0.999)
    pipeline = ImageDetectionPipeline(detector=detector)
    blank_img = np.zeros((512, 512, 3), dtype=np.uint8)
    result = pipeline.process(blank_img)
    assert isinstance(result, DetectionResult)
    assert result.count == 0
    assert len(result.detections) == 0

def test_optical_onnx_invalid_inputs():
    detector = ONNXOpticalDetector(model_path=ONNX_PATH)
    pipeline = ImageDetectionPipeline(detector=detector)
    with pytest.raises(ImageValidationError):
        pipeline.process(b'')
    with pytest.raises(ImageValidationError):
        pipeline.process(b'not_an_image_data_12345')
    with pytest.raises(ImageValidationError):
        pipeline.process('definitely_non_existent_image_99999.png')

def test_optical_onnx_pytorch_consistency():
    if not PT_PATH.exists():
        pytest.skip('PyTorch checkpoint not found for consistency test')
    sample_images = ['1009.jpg', '1017.jpg', '1019.jpg', '1037.jpg', '1043.jpg']
    pt_detector = YOLODetector(model_path=PT_PATH, confidence_threshold=0.25)
    onnx_detector = ONNXOpticalDetector(model_path=ONNX_PATH, confidence_threshold=0.25)
    pt_pipeline = ImageDetectionPipeline(detector=pt_detector, confidence_threshold=0.25)
    onnx_pipeline = ImageDetectionPipeline(detector=onnx_detector, confidence_threshold=0.25)
    for img_name in sample_images:
        img_p = VAL_IMG_DIR / img_name
        if not img_p.exists():
            continue
        pt_res = pt_pipeline.process(img_p)
        onnx_res = onnx_pipeline.process(img_p)
        assert pt_res.count == onnx_res.count, f'Count mismatch on {img_name}'
        pt_classes = [d.class_id for d in pt_res.detections]
        onnx_classes = [d.class_id for d in onnx_res.detections]
        assert pt_classes == onnx_classes, f'Class mismatch on {img_name}'

def test_optical_onnx_annotation_with_segmentation():
    test_img_path = VAL_IMG_DIR / '1009.jpg'
    if not test_img_path.exists():
        pytest.skip(f'Missing test image {test_img_path}')
    optical_detector = OpticalDetector(model_path=ONNX_PATH, confidence_threshold=0.25)
    result = optical_detector.detect_image(test_img_path)
    annotator = ImageAnnotator()
    annotated = annotator.annotate(test_img_path, result)
    assert isinstance(annotated, Image.Image)
    assert annotated.size == (1920, 1080)
