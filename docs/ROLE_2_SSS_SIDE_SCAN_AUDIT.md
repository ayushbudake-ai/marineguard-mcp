# MarineGuard SSS Side-Scan Integration Audit

**Status:** IMPLEMENTED and TESTED
**Scope:** Role 2 - Person B Engineering and Integration
**File:** `marineguard/detection/side_scan.py`

---

## 1. Purpose

This document audits the current SideScanDetector implementation including
all input handling, validation, processing paths, model integration, and
downstream compatibility.

---

## 2. Input Handling

### IMPLEMENTED

SideScanDetector accepts the following input types through
validate_and_normalize_matrix() and detect_waterfall():

| Input Type | Handling |
|---|---|
| str or Path | File path to waterfall image. File existence and integrity verified. |
| bytes / bytearray | Raw image bytes. Zero-length rejected. PIL decode + verify applied. |
| PIL.Image.Image | Converted directly to numpy array. |
| np.ndarray | Used directly. 2D and 3D shapes accepted. |

Unsupported types raise ImageValidationError.

---

## 3. Input Validation

### IMPLEMENTED and TESTED

| Check | Status | Error Raised |
|---|---|---|
| Empty array (0 elements) | IMPLEMENTED | ImageValidationError |
| Empty bytes (0 bytes) | IMPLEMENTED | ImageValidationError |
| Invalid dimensions (not 2D or 3D) | IMPLEMENTED | ImageValidationError |
| NaN values in array | IMPLEMENTED | ImageValidationError |
| Infinite values in array | IMPLEMENTED | ImageValidationError |
| Unsupported channel count | IMPLEMENTED | ImageValidationError |
| File not found | IMPLEMENTED | ImageValidationError |
| Corrupt image file | IMPLEMENTED | ImageValidationError |

Channel conversion rules:
- (H, W): used as-is, converted to float32
- (H, W, 1): first channel extracted
- (H, W, 3) or (H, W, 4): channel mean taken
- (H, W, C) with C not in {1, 3, 4}: ImageValidationError

---

## 4. Preprocessing

### IMPLEMENTED

After validation, the matrix is converted to a 2D float32 intensity map.

For the SSS YOLO path, the 2D grayscale intensity matrix is stacked into a
3-channel RGB-like array (np.stack([mat_f, mat_f, mat_f], axis=-1)) to
satisfy the YOLO model's expected 3-channel input format.

For the CA-CFAR path, the float32 matrix is used directly.

---

## 5. CA-CFAR Logic

### IMPLEMENTED and TESTED

Method: cfar_detect_2d()

The 2D CA-CFAR detector uses OpenCV box filters to efficiently compute:

1. Sliding reference window: Estimates background noise floor excluding a guard region.
2. Noise variance estimate: Used to compute adaptive noise standard deviation.
3. Adaptive threshold: noise_floor + k_mult * noise_std where k_mult is derived
   from the configured false-alarm probability (default: cfar_pfa=1e-4).
4. Global intensity floor: global_mean + 1.5 * global_std applied as additional
   constraint to reduce responses to uniform low-intensity regions.
5. Morphological close: 5x5 rectangular kernel applied to cluster adjacent anomaly pixels.
6. Connected components: Separates clusters into individual candidate bounding boxes.
7. Confidence mapping: Maps SNR to a deterministic score in [0.50, 0.99].

Legacy 1D row CA-CFAR is preserved in cfar_detect() for backward compatibility.

LIMITATION: CA-CFAR emits class_id=27 (unknown-object). It does not classify
the object type. Classification is delegated to the SSS YOLO path or a
separate classification stage.

---

## 6. SSS YOLO Invocation

### IMPLEMENTED and TESTED

The SSS YOLO path is activated by:
- use_sss_model=True at construction time, OR
- use_sss_model=True passed to detect_waterfall()

Default: use_sss_model=False (CA-CFAR path is the default).

THE SSS YOLO PATH MUST BE EXPLICITLY ENABLED. IT DOES NOT ACTIVATE SILENTLY.

When enabled:
1. Input is validated and normalized to a 2D float32 matrix.
2. Matrix is stacked into 3-channel array for YOLO input.
3. self.model.predict(model_image, imgsz=SSS_IMAGE_SIZE) is called.
4. Raw detections are filtered through the SSS class map.
5. Canonical Detection objects are constructed with MarineGuard class IDs.

Status: "ok" is set on the result when SSS YOLO is used.

---

## 7. Model Loading

### IMPLEMENTED and TESTED

Model loading is handled through the existing MarineDebrisModel abstraction
in marineguard/detection/model_loader.py.

The SSS detector accepts an optional model parameter at construction:
    SideScanDetector(model=sss_model, use_sss_model=True)

If model=None, the default V1 model path is used. For SSS-specific inference,
a dedicated MarineDebrisModel instance must be constructed with the SSS checkpoint.

MarineDebrisModel.is_loaded returns False if the model file does not exist.
A RuntimeError is raised if use_sss_model=True but the model is not loaded.

---

## 8. Detection Conversion

### IMPLEMENTED and TESTED

Raw YOLO detections are converted to marineguard.detection.schema.Detection objects.

SSS path:
    raw["class_id"]      -> SSS_CLASS_MAP lookup -> MarineGuard class_id
    SSS_CLASS_NAMES      -> class_name
    raw["confidence"]    -> confidence
    raw["bbox"]          -> bbox [x1, y1, x2, y2]

CA-CFAR path:
    UNKNOWN_CLASS_ID (27)   -> class_id
    "unknown-object"        -> class_name
    candidate["confidence"] -> confidence
    candidate["bbox"]       -> bbox [x1, y1, x2, y2]

---

## 9. DetectionResult Conversion

### IMPLEMENTED and TESTED

All detection paths return a DetectionResult via DetectionResult.from_detections().

Fields populated:
- detections: List of Detection objects
- count: Synchronized with len(detections)
- image_width / image_height: From validated input matrix
- inference_time_ms: Measured wall-clock latency
- model_name: From SideScanDetector.model_name property
- status: "SUCCESS" (CA-CFAR), "ok" (SSS YOLO), or "error: <message>" (validation failure)

The detect() method (BaseDetector interface) catches ImageValidationError and
returns an error DetectionResult with status="error: <message>".
detect_waterfall() raises ImageValidationError directly for explicit callers.

---

## 10. Taxonomy Mapping

### IMPLEMENTED and TESTED

    SSS native class 0
            |
    MarineGuard class 29
            |
         "net"

Constants defined as class attributes in SideScanDetector:
    SSS_CLASS_MAP   = {0: 29}
    SSS_CLASS_NAMES = {29: "net"}
    SSS_IMAGE_SIZE  = 640

CA-CFAR uses:
    UNKNOWN_CLASS_ID   = 27
    UNKNOWN_CLASS_NAME = "unknown-object"

These two are never conflated. SSS YOLO always emits class 29 ("net").
CA-CFAR always emits class 27 ("unknown-object").

---

## 11. Confidence Handling

### IMPLEMENTED and TESTED

| Path | Confidence Source | Range |
|---|---|---|
| CA-CFAR | Deterministic SNR-based mapping | [0.50, 0.99] |
| SSS YOLO | Raw model confidence | [0.0, 1.0] |

Both paths apply a confidence_threshold filter. Only detections at or above
the configured threshold are included in the result.

---

## 12. Bounding Box Handling

### IMPLEMENTED and TESTED

All bounding boxes are in [x1, y1, x2, y2] pixel-coordinate format.

CA-CFAR boxes are clamped to image dimensions:
    x1 = max(0.0, float(x))
    x2 = min(float(w), float(x + comp_w))

SSS YOLO boxes are taken directly from the YOLO model output.
Detections with bbox is None or len(bbox) != 4 are rejected.

---

## 13. Error Handling

### IMPLEMENTED and TESTED

| Error Scenario | Behavior |
|---|---|
| Empty/invalid input via detect() | Returns DetectionResult(status="error: ...") |
| Empty/invalid input via detect_waterfall() | Raises ImageValidationError |
| SSS model not loaded but enabled | Raises RuntimeError |
| Unknown SSS class ID | Detection silently skipped |
| Invalid bbox from model | Detection silently skipped |

---

## 14. Limitations

### LIMITATION

1. No NMS post-processing at the SSS integration layer: NMS handled by YOLO model.
2. CA-CFAR only produces class 27 (unknown-object). Cannot classify object types.
3. SSS YOLO currently has only one class (class 0 = "net").
4. ONNX CUDA execution unavailable: Environment has CUDA 13/cuDNN 9 dependency not installed.
   ONNX inference runs on CPU only.
5. No automatic bbox denormalization at integration layer; verified on current checkpoint
   which returns absolute pixel coordinates.
6. No temporal tracking: Each frame is processed independently.
7. CA-CFAR may produce false alarms on regular periodic patterns in SSS imagery.

---

## 15. Future Compatibility

### PENDING

- Final SSS checkpoint selection (Person A responsibility)
- Full SSS test-set verification (Person A responsibility)
- GPU ONNX execution after environment upgrade
- Optional CA-CFAR pre-filtering before SSS YOLO (see CA-CFAR+YOLO architecture doc)
- Temporal smoothing / track association layer
- Confidence calibration after final model selection
