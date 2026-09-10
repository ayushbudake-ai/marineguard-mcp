# Role 5 — Streamlit SSS AI Detection Center & System Integration

**MoES / SIH26057 Primary User Interface & Real SSS YOLOv8n End-to-End Pipeline**

---

## 1. Executive Summary

Role 5 establishes the authoritative **Streamlit Web Application** (`streamlit_demo.py`) as the primary and single user interface for SIH judges and MoES operators.

- **Primary Input**: Recorded Side-Scan Sonar (SSS) imagery and survey logs.
- **AI Inference Engine**: Authoritative trained PyTorch `YOLOv8n` detection model (Experiment #2 Augmented Training).
- **Post-Processing & Gating**: Role 3 confidence filtering, geometry validation (non-zero area, min 4px), and boundary clamping.
- **Geospatial Integrity**: Geodetic coordinates displayed **strictly when recorded in metadata** (zero coordinate fabrication; suppressed with clear notice when unavailable).
- **Scope Compliance**: All vehicle controls, thruster sliders, simulated battery/depth telemetry, and fake AUV animations have been fully excised.
- **Official Exports**: Direct publication-grade MoES PDF Survey Reports, GeoJSON FeatureCollections, IHO S-100/S-124 Catalogues, and CSV Target Inventories.

---

## 2. Model Specifications & Integrity

| Parameter | Specification / Verified Value |
| :--- | :--- |
| **Model Architecture** | YOLOv8n Object Detection |
| **Authoritative Checkpoint** | `runs/detect/runs/detect/marineguard_sss_yolov8n_exp2_augmented/weights/best.pt` |
| **Git LFS OID / SHA-256** | `c9fd27940b9b1a28834002dcbc40d1306c3e56650309b536aecd9862236bd7d2` |
| **File Size** | 6,254,250 bytes (~6.25 MB) |
| **Training Configuration** | 75 epochs (`yolov8n`), imgsz 640, batch 16, best epoch 66 |
| **Native Model Classes** | `0: 'net'` |
| **MarineGuard Taxonomy Mapping** | Class `0: 'net'` → Species: `ghost_net` (Global Class ID 29) |
| **Development Validation F1** | `0.9993` (99.87% Precision, 100.0% Recall on 190 validation tiles) |

---

## 3. End-to-End Pipeline Architecture

```
                 RECORDED SSS IMAGE (PNG / JPG / BMP / TIF)
                                      ↓
                           PREPROCESSING & RESIZING
                       (Grayscale to 3-Channel RGB 640x640)
                                      ↓
                       REAL YOLOv8n PyTorch INFERENCE
                               (`best.pt` Exp #2)
                                      ↓
                             RAW YOLO DETECTIONS
                     (Float BBoxes, Confidences, Classes)
                                      ↓
                              ROLE 3 FILTERING
                (Confidence Slider, Geometry, Boundary Checks)
                                      ↓
                              DETECTION RESULT
                        ↙                           ↘
          ANNOTATED SSS IMAGE                     OFFICIAL REPORTS
     (Emerald ACCEPTED / Coral FILTERED)        (PDF, GeoJSON, S-100, CSV)
```

---

## 4. UI Operating Modes

### Mode A: Automatic Repository Demo
- Loads verified repository-controlled SSS sonar waterfall images (`data/processed/marineguard_sss/images/test/`).
- Includes positive debris contacts (`synth_ghost_net_00001.png`, `synth_ghost_net_00002.png`) and negative background seabed controls (`bg_1693569243.750_x2500.jpg`).
- Evaluates full YOLO inference with single-click demo execution without requiring judge upload.

### Mode B: Manual SSS Image Upload
- Allows uploading recorded underwater SSS image tiles (PNG, JPG, BMP, TIF).
- Executes the exact same production YOLOv8n + Role 3 pipeline.

---

## 5. Official SIH Run Command

To start the MarineGuard SSS AI Analysis Center:

```powershell
# Run strictly from repository root
cd c:\marineguard-mcp
python -m streamlit run streamlit_demo.py
```

---

## 6. Verification & Test Suite

All 19 unit, integration, and frozen core tests pass 100%:

```powershell
python -m pytest tests/test_ui_and_eval.py tests/test_compiler.py tests/test_detection.py tests/test_firewall.py tests/test_trace.py
```
