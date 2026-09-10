# Role 2: Side-Scan Sonar Software Inference Layer & Integration

## 1. Overview & Current Status

This document describes the software architecture, signal processing pipeline, and integration interfaces for the **Side-Scan Sonar (SSS)** waterfall inference component in MarineGuard MCP.

**Current Implementation Status:**
* ✅ **2D CA-CFAR Acoustic Anomaly Extraction**: Full Cell-Averaging Constant False Alarm Rate pipeline with morphological clustering.
* ✅ **Canonical Structured Output**: Emits standard `Detection` and `DetectionResult` schemas.
* ✅ **Taxonomy Alignment**: Class-agnostic anomaly assignment mapped to official taxonomy class `unknown-object` (ID `27`).
* ✅ **Input Validation**: Robust matrix dimension checking (2D/3D), empty array handling, and NaN/Inf rejection.
* ✅ **Multi-Sensor Fusion Adapter**: Preserves legacy `DebrisContact` mapping for `MultiSensorFusionEngine`.
* ✅ **FastAPI REST API**: Exposed via `POST /detect/side-scan`.
* ✅ **MCP Tool**: Exposed via `detect_side_scan_waterfall`.
* ✅ **Comprehensive Unit Testing**: 15 software correctness unit tests.

---

## 2. Technical Honesty & Data Limitations

### Data Availability
* **No real Side-Scan Sonar (SSS) dataset currently exists in the repository.**
* The repository includes:
  * `data/raw/fls`: Forward-Looking Sonar (Acoustic Camera) images (ARIS Explorer 3000).
  * `data/raw/uatd`: Underwater Acoustic Target Detection (Forward-Looking acoustic camera) BMP frames.
  * `data/raw/seaclear`: Optical RGB camera photography.
* **Physics Distinction**: Forward-Looking Sonar (FLS) generates polar sector frames of the forward path, whereas Side-Scan Sonar (SSS) generates waterfall strips of lateral acoustic backscatter and grazing shadows. FLS data **cannot and must not be mislabeled as Side-Scan Sonar data**.

### Model Status
* **No dedicated Side-Scan trained ML model is currently available.**
* The optical YOLOv8n-seg model trained on SeaClear is not applied to side-scan waterfall imagery.
* **No fake Precision, Recall, F1, or mAP metrics are reported.**

---

## 3. Signal Processing & Detector Pipeline

### CA-CFAR Candidate Detection
The detector uses a 2-parameter 2D Cell-Averaging Constant False Alarm Rate (CA-CFAR) algorithm:

```
                  Waterfall Matrix [H, W]
                            ↓
               Input & Matrix Validation
         (Non-empty, finite values, 2D/3D shape)
                            ↓
           Sliding Window Background Statistics
    (Dynamic Reference Window R and Guard Window G)
                            ↓
               Adaptive Anomaly Threshold
             T = μ_noise + k(P_fa) * σ_noise
                            ↓
                 Binary Anomaly Mask
                            ↓
           Morphological Consolidation & Closing
                            ↓
             8-Connected Component Analysis
                            ↓
            Candidate Bounding Boxes [x1, y1, x2, y2]
                            ↓
        Acoustic Anomaly Confidence Score [0.50, 0.99]
                            ↓
             Canonical DetectionResult Output
```

### Anomaly Confidence
Confidence scores represent **acoustic anomaly signal-to-noise strength (SNR)**:
$$\text{SNR} = \frac{\max(I_{\text{region}}) - \mu_{\text{noise}}}{\sigma_{\text{noise}}}$$
$$\text{Confidence} = \min\left(0.99, \max\left(0.50, 0.50 + 0.45 \cdot \left(1 - \exp\left(-\frac{\text{SNR} - 2}{8}\right)\right)\right)\right)$$

> **Important Note:** This confidence represents acoustic anomaly prominence relative to local seafloor backscatter. It is **not** a calibrated probability of a specific debris species.

### Taxonomy Representation
Until a dedicated SSS classifier is trained on labeled side-scan imagery, candidate acoustic anomalies are assigned to:
* **Class Name**: `unknown-object`
* **Class ID**: `27` (from `marineguard_classes.yaml`)
* **Metadata**: `{"sensor": "side_scan", "method": "CA-CFAR", "snr": ..., "anomaly_type": "acoustic_highlight"}`

---

## 4. Software Architecture & Integration

### Python Interface
```python
from marineguard.detection.side_scan import SideScanDetector

detector = SideScanDetector(cfar_pfa=1e-4, confidence_threshold=0.50)

# Run waterfall inference
result = detector.detect_waterfall(waterfall_matrix)

# Access canonical structured output
print(f"Detected {result.count} acoustic anomalies")
for det in result.detections:
    print(f"Candidate: {det.class_name} ({det.confidence*100:.1f}%) at {det.bbox}")
```

### REST API
* **Endpoint**: `POST /detect/side-scan`
* **Request**: Upload waterfall image (`PNG`, `JPG`, `TIFF`, `BMP`)
* **Response**:
```json
{
  "detections": [
    {
      "class": "unknown-object",
      "class_id": 27,
      "confidence": 0.885,
      "bbox": [102.0, 102.0, 147.0, 148.0],
      "metadata": {
        "sensor": "side_scan",
        "method": "CA-CFAR",
        "snr": 12.4,
        "area_pixels": 1414,
        "anomaly_type": "acoustic_highlight"
      }
    }
  ],
  "count": 1,
  "image_width": 256,
  "image_height": 256,
  "inference_time_ms": 2.8
}
```

### MCP Tool Interface
* **Tool**: `detect_side_scan_waterfall`
* **Function**: `MarineGuardMCPServer.detect_side_scan_waterfall(waterfall_input, confidence_threshold, cfar_pfa)`

---

## 5. Summary: Implemented vs. Blocked

| Component | Status | Description |
| :--- | :---: | :--- |
| **CA-CFAR Anomaly Detection** | ✅ Implemented | 2D adaptive noise floor estimation, thresholding, clustering. |
| **Canonical Schema Output** | ✅ Implemented | Returns `Detection` / `DetectionResult` objects. |
| **Input Validation** | ✅ Implemented | Rejects empty matrices, NaN, Inf, invalid dimensions. |
| **Fusion Adapter** | ✅ Implemented | Converts detections to `DebrisContact` for `MultiSensorFusionEngine`. |
| **REST API** | ✅ Implemented | `POST /detect/side-scan` endpoint added. |
| **MCP Tool** | ✅ Implemented | `detect_side_scan_waterfall` tool added. |
| **Unit Tests** | ✅ Implemented | 15 deterministic software unit tests in `tests/test_side_scan.py`. |
| **Real SSS Dataset** | 🚫 Blocked | Requires acquisition of real side-scan sonar waterfall data. |
| **Dedicated SSS Model** | 🚫 Blocked | Requires training on labeled SSS data. |
| **Model Metrics (mAP/F1)** | 🚫 Blocked | Cannot be reported without real held-out SSS evaluation set. |
| **Multimodal Fusion Retuning** | 🚫 Blocked | Intentionally frozen per project handoff contract. |

---

## 6. Future Upgrade Path

```
Acquire Real Side-Scan Sonar Dataset (e.g. Seabed Debris SSS)
                           ↓
Convert Annotations to MarineGuard 50-Class Taxonomy
                           ↓
Train Dedicated SSS YOLO/Acoustic Object Detector
                           ↓
Export to ONNX & Verify Numerical Consistency
                           ↓
Plug Model Checkpoint into SideScanDetector Interface
                           ↓
Evaluate on Held-out Real SSS Test Set (Report Real Precision/Recall/mAP)
                           ↓
Multi-Sensor Fusion Calibration (Role 2 / Role 3)
```
