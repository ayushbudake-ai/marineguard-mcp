# Design Document

**Project:** MarineGuard — Automated Underwater Marine Debris Detection  
**Context:** Engineering Specifications & Pipeline Design  

---

## 1. Standard Report Schema (Frozen at Phase 0)

To ensure strict interoperability between pipeline modules and downstream consumers, the export schema is frozen in Phase 0.

### JSON Report Schema
```json
{
  "survey_id": "string",
  "source_log": "string (uploaded file name)",
  "generated_at": "ISO 8601 timestamp",
  "detections": [
    {
      "detection_id": "string",
      "classification": "ghost_net | plastic | metal | shipwreck | pipe | unknown",
      "confidence": 0.89,
      "bounding_box": {
        "width_m": 12.0,
        "height_m": 8.0
      },
      "location": {
        "lat": 13.0835,
        "lon": 80.2715
      },
      "depth_m": 24.3,
      "sensor_source": "side_scan | optical | bathymetry | fused"
    }
  ],
  "summary": {
    "total_detections": 1,
    "high_confidence_count": 1
  }
}
```

### CSV Report Structure.
The CSV export directly mirrors the flattened `detections` array:
`detection_id, classification, confidence, width_m, height_m, lat, lon, depth_m, sensor_source`

---

## 2. Preprocessing Design.

Sonar imagery exhibits intense multiplicative speckle noise, non-uniform acoustic illumination, and sensor motion artifacts. The preprocessing pipeline standardizes raw imagery prior to inference.

| Step | Technique | Algorithmic Purpose |
|:---|:---|:---|
| **Speckle Denoise** | Enhanced Lee Filter or Median Filter | Suppresses multiplicative speckle noise while preserving sharp highlight-shadow boundaries of debris. |
| **Resolution Normalization** | Bilinear Resampling | Resamples varying across-track resolutions to a standardized pixel-to-meter ratio (e.g. $2.5\text{ cm/pixel}$). |
| **Shadow-Aware Augmentation** | Synthetic Acoustic Shadow Injection | Simulates acoustic shadows cast by seafloor relief during model training to improve false-positive discrimination. |
| **Dropout Simulation** | Random Row/Frame Masking | Simulates vehicle roll/heave/pitch data loss and acoustic modem transmission gaps. |

---

## 3. Model Design

* **Primary Model Architecture:** **YOLOv8-seg** (Instance Segmentation). Chosen for optimal speed/accuracy trade-off, real-time bounding box and segmentation mask extraction, and native ONNX runtime export capabilities.
* **Alternative Considered:** **U-Net** (PyTorch). Excellent for dense pixel-level masks, but higher inference latency on embedded edge hardware; retained as an alternative if boundary precision requires improvement.
* **Training Data Sources:** Public sonar and underwater debris datasets:
  * **Marine Debris FLS:** Forward-Looking Sonar acoustic debris imagery.
  * **UATD (Underwater Acoustic Target Dataset):** Side-scan sonar target repository.
  * **SeaClear / TrashCan:** Optical and acoustic underwater debris benchmarks.
* **Inference Runtime & Target:** ONNX Runtime / TensorRT on embedded hardware (NVIDIA Jetson). Batch size $1\text{--}4$, target inference latency $\le 200\text{ ms/frame}$.

---

## 4. Confidence Scoring & Filtering Design

Raw neural network confidence scores are frequently uncalibrated (over-confident on out-of-distribution noise). The filtering stage guarantees statistical precision:

### Calibration
* **Platt / Isotonic Calibration:** Calibrate raw logits against held-out validation benchmarks so that a reported confidence of $0.80$ corresponds to an empirical precision of $\approx 80\%$.

### False-Positive Filtering Heuristics
Acoustic shadows are critical in side-scan sonar interpretation. The false-positive suppression filter applies two key physical checks:
1. **Shadow-Ratio Check:** Anthropogenic debris protruding above the seafloor casts a distinct acoustic shadow whose length is proportional to object height and sonar altitude ($L_s = \frac{H_t \cdot R}{H_a}$). Contacts lacking a corresponding acoustic shadow are suppressed as natural flat rock or sediment patterns.
2. **Aspect-Ratio & Silhouette Heuristics:** Ghost nets exhibit irregular, draped amorphous silhouettes with high edge entropy, whereas pipes and cables exhibit linear high-aspect-ratio signatures. Natural rock clusters exhibit distinct fractal spatial clustering.
3. **Trace Generation:** Each detection outputs an explainability string (e.g. `Shadow ratio: 0.35 (expected 0.30-0.60) | Aspect ratio: 1.5 | Filter: PASSED`).

---

## 5. Geotagging Design

Georeferencing translates sonar image pixel coordinates $(u, v)$ into absolute geographic coordinates $(\text{lat}, \text{lon})$:

1. **Inputs:** Vehicle navigation telemetry at ping time:
   * Vehicle Position: $(\text{lat}_v, \text{lon}_v)$
   * Vehicle Heading: $\psi$
   * Towfish/AUV Altitude: $H_a$
   * Slant Range & Across-Track Distance: $y_r$
2. **Coordinate Transformation:**
   $$\Delta x = y_r \cos\left(\psi + \frac{\pi}{2}\right), \quad \Delta y = y_r \sin\left(\psi + \frac{\pi}{2}\right)$$
   $$\text{lat} = \text{lat}_v + \frac{\Delta y}{R_{\text{earth}}}, \quad \text{lon} = \text{lon}_v + \frac{\Delta x}{R_{\text{earth}} \cos(\text{lat}_v)}$$
3. **Fallback Policy:** If navigation metadata is absent or corrupted, location coordinates are explicitly output as `null` rather than generating fabricated coordinates (`rules.md §5`).

---

## 6. UI / Dashboard Flow

The redesigned Streamlit application removes simulation sliders and focuses strictly on the operational analyst flow:

```
[ Upload Screen ]
       │  User uploads SSS log file or waterfall image (.xtf, .png, .jpg)
       ▼
[ Pipeline Execution ]
       │  Preprocessing → Detection (ONNX) → Filtering → Geotagging
       ▼
[ Results Inspection View ]
 ├── Tab 1: Detection Overlay  (Bounding boxes, segmentation masks, class tags on sonar waterfall)
 ├── Tab 2: GIS Map View       (Interactive spatial distribution with removal priority color-coding)
 ├── Tab 3: Performance Metrics (F1 score, false positive rate, inference latency of the run)
 └── Tab 4: Report Exporter    (One-click download of JSON, CSV, and GeoJSON survey packages)
```

---

## 7. Explainability Design

Preserved from the initial prototype trace engine, each classified target produces an auditable reasoning chain and composite visual evidence package:

* **Audit Trace:** Captures contributing sensor channels (Side-Scan Sonar, Optical, Bathymetry), raw vs. calibrated confidence scores, and specific heuristic filter verdicts.
* **Evidence Overlay Visualizer (`marineguard/trace/visualizer.py`):** Dynamically composes a multi-panel evidence image containing the side-scan waterfall crop, acoustic highlight/shadow profile, optical verification frame, and bathymetric anomaly profile.
