# MarineGuard MCP — Role 2: Optical ONNX Segmentation Integration Report

**Document Date**: 2026-09-07  
**Author**: Role 2 AI Inference & Integration Lead  
**Status**: **INTEGRATION VERIFIED**  
**Integrated Model**: 
uns/seaclear_yolov8n_seg/onnx/best.onnx  
**Target Modality**: Optical Camera Debris Classification & Instance Segmentation  

---

## 1. Purpose & Scope

This document details the successful integration of the verified **YOLOv8n-seg ONNX instance segmentation model** into the **MarineGuard optical inference path**.

The integration establishes the complete production flow:
\text{Optical Image / Crop} \longrightarrow \text{Preprocessing} \longrightarrow \text{ONNX Runtime Engine} \longrightarrow \text{Post-Processing} \longrightarrow \text{MarineGuard Structured Detection Schema}

> [!NOTE]
> This task strictly integrates the optical sensor modality. The acoustic/sonar detectors (side_scan.py), bathymetry pipeline (athymetry.py), and multimodal fusion engine (usion.py) remain completely untouched.

---

## 2. Integrated Model & Specifications

* **Model File**: [
uns/seaclear_yolov8n_seg/onnx/best.onnx](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/onnx/best.onnx)
* **Source Checkpoint**: 
uns/seaclear_yolov8n_seg/train/weights/best.pt (Epoch 48)
* **Architecture**: YOLOv8n-seg (85 layers, 3.27M parameters)
* **Runtime Engine**: ONNX Runtime 1.29.0 (CPUExecutionProvider)
* **Taxonomy**: Official 50-class MarineGuard taxonomy ([marineguard_classes.yaml](file:///d:/Marine%20Drive/marineguard-mcp/marineguard_classes.yaml))

### Model Tensor I/O

| Stream | Name | Shape | Type | Description |
|---|---|---|---|---|
| **Input** | images | [1, 3, 512, 512] | loat32 | 512x512 normalized RGB tensor $[0.0, 1.0]$ |
| **Output 0** | output0 | [1, 86, 5376] | loat32 | 4 bbox coordinates + 50 class logits + 32 mask coefficients |
| **Output 1** | output1 | [1, 32, 128, 128] | loat32 | 32 prototype segmentation masks ( \times 128$) |

---

## 3. Integration Architecture

* **Input Loading**: ImageDetectionPipeline.validate_and_load_image validates file path, bytes, PIL, or numpy array.
* **Preprocessing**: DefaultPreprocessor handles channel verification and RGB-to-BGR conversion to match standard OpenCV/YOLO model expectations.
* **Model Inference**: ONNXOpticalDetector uses a cached MarineDebrisModel instance to execute inference via ONNX Runtime without redundant session reloads.
* **Post-Processing**: PostProcessor clips coordinates, filters by confidence threshold, and preserves polygon segmentation coordinates (Detection.segmentation).
* **Annotation**: ImageAnnotator renders bounding boxes, class labels, confidence scores, and segmentation polygon outlines.

---

## 4. Verification & Unit Tests

A dedicated test suite [	ests/test_optical_onnx.py](file:///d:/Marine%20Drive/marineguard-mcp/tests/test_optical_onnx.py) was executed to validate the integrated optical ONNX path:

| Test Case | Scope | Observed Result | Status |
|---|---|---|:---:|
| **Test 1: Model Loading** | Verify ONNX model exists, passes onnx.checker, and initializes InferenceSession | images: [1, 3, 512, 512] and outputs verified | **PASSED** |
| **Test 2: Valid Optical Image** | Verify inference on 1009.jpg, checking class names, confidences, bboxes, and mask polygons | 1 detection (nimal, conf=0.9078, 103-vertex polygon) | **PASSED** |
| **Test 3: Empty / No-Detection** | Verify blank solid image and high confidence filtering without crash | Returned DetectionResult(count=0, detections=[]) | **PASSED** |
| **Test 4: Invalid Input Handling** | Verify empty bytes, corrupt bytes, and non-existent paths raise ImageValidationError | Clean exceptions raised | **PASSED** |
| **Test 5: PyTorch vs. ONNX Parity** | Verify identical detection counts and class IDs across 5 validation images (1009.jpg, 1017.jpg, 1019.jpg, 1037.jpg, 1043.jpg) | 100% count and class parity | **PASSED** |
| **Test 6: Segmentation Annotation** | Verify ImageAnnotator renders boxes, labels, and polygon contours without dimension distortion | Clean annotated PIL image | **PASSED** |

### Benchmark Latency Measurements (Host CPU: 12th Gen Intel Core i5-12400F)

| Image | Resolution | Detections | ONNX Model Latency | End-to-End Latency (incl. I/O and Post-Proc) |
|---|:---:|:---:|:---:|:---:|
| **1009.jpg** |  \times 1080$ | 1 (nimal) | .55\text{ ms}$ | .85\text{ ms}$ |
| **1017.jpg** |  \times 1080$ | 2 (glass-bottle, nimal) | .37\text{ ms}$ | .21\text{ ms}$ |
| **1019.jpg** |  \times 1080$ | 2 (metal-wreckage) | .16\text{ ms}$ | .42\text{ ms}$ |
| **1037.jpg** |  \times 1080$ | 9 (mixed debris) | .44\text{ ms}$ | .51\text{ ms}$ |
| **1043.jpg** |  \times 1080$ | 4 (
ope, shell) | .79\text{ ms}$ | .87\text{ ms}$ |

---

## 5. Schema Compatibility & Backward Compatibility

* **Detection Schema**: Standard [marineguard/detection/schema.py](file:///d:/Marine%20Drive/marineguard-mcp/marineguard/detection/schema.py) (Detection, DetectionResult) is 100% preserved.
* **Segmentation Field**: Polygon coordinates are stored in Detection.segmentation as List[List[float]] without breaking callers expecting bounding-box-only dictionaries.
* **REST API (/detect)**: Fully compatible with existing endpoint contract.
* **MCP Tool (detect_marine_debris)**: Fully compatible with existing MCP server schema.

---

## 6. Scope & Protection Confirmation

* **usion.py**: **UNCHANGED** (Preserved for downstream fusion tuning stage).
* **side_scan.py**: **UNCHANGED** (Preserved for Member 1 sonar detector).
* **athymetry.py**: **UNCHANGED**.
* **Model Checkpoints**: est.pt and est.onnx remain unmodified.
* **Datasets & Labels**: Unmodified.

---

## 7. Next Steps

1. **Multimodal Fusion Calibration (Role 2 Task 3)**:
   * Ingest real optical segmentation masks and sonar contacts into usion.py.
   * Evaluate spatial IoU overlap between optical polygon boundaries and acoustic shadows.
   * Retune sensor confidence weights based on real multi-sensor detections.
