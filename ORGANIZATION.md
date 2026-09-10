# 🏗️ MarineGuard MCP — GitHub Repository Organization & Architecture

This document provides a comprehensive structural mapping of the **MarineGuard MCP** repository across all system layers, operational roles, and architectural components.

---

## 🗺️ Architectural Structure

```text
marineguard-mcp/
│
├── 🎨 FRONTEND / UI LAYER
│   ├── streamlit_demo.py               # Streamlit post-mission analysis dashboard
│   ├── .streamlit/config.toml          # Streamlit UI theme and server configuration
│   ├── my-react-router-app/            # Modern React Router v7 + Tailwind Web Application
│   │   ├── app/                        # React routes, components & UI views
│   │   ├── public/                     # Public web assets
│   │   ├── package.json                # Frontend dependencies
│   │   └── vite.config.ts              # Vite build setup
│   ├── my-project/                     # Standalone / alternate web frontend package
│   └── docs/demo.html, index.html      # Interactive static web demonstration
│
├── 🔌 BACKEND & API LAYER
│   ├── api_server.py                   # Production FastAPI bridge (REST API for UI)
│   ├── marineguard/
│   │   ├── mcp_server.py               # Model Context Protocol (MCP) tool server
│   │   ├── schemas.py                  # Pydantic data schemas & contracts
│   │   └── api/                        # API route handlers and utilities
│   └── config.yaml                     # System & service configuration
│
├── 🧠 AI & DETECTION PIPELINE
│   ├── marineguard/detection/
│   │   ├── sss_yolo_adapter.py         # Authoritative YOLOv8n SSS detection wrapper
│   │   ├── side_scan.py                # Side-scan sonar image detector & preprocessor
│   │   ├── detector.py                 # Optical debris detector
│   │   └── model_loader.py             # Model checkpoint loader & integrity verifier
│   ├── marineguard/
│   │   ├── v1_detector.py              # Frozen V1 YOLOv8n baseline detector
│   │   └── v2_detector.py              # V2 experimental detection wrapper
│   ├── models/                         # Serialized model weights & ONNX checkpoints
│   ├── runs/marineguard_full_512_b16-2/# Authoritative V1 training run & best.pt weights
│   ├── export_onnx.py                  # ONNX export script
│   └── verify_onnx.py                  # ONNX numerical parity verification
│
├── 🛡️ POST-PROCESSING & FILTERING
│   ├── marineguard/trace/
│   │   └── confidence_filter.py        # False-positive filtering (shadow & aspect ratios)
│   ├── marineguard/compiler/
│   │   └── filtering_layer.py          # Accepted vs Rejected classification pipeline
│   ├── marineguard/confidence.py       # Platt / Isotonic confidence calibration
│   └── marineguard/evidence.py         # Visual evidence crop generator & bounding boxes
│
├── 📄 REPORTING & GIS EXPORTERS
│   └── marineguard/exporters/
│       ├── pdf_exporter.py             # ReportLab automated PDF mission report generator
│       ├── geojson_exporter.py         # Maritime GIS GeoJSON layer exporter
│       ├── json_csv_report.py          # Structured JSON & CSV contact log exporter
│       ├── s100_exporter.py            # S-100 / S-124 maritime navigation hazard notices
│       └── coordinate_validator.py     # Geographic latitude/longitude range validation
│
├── 📊 DATASET & TRAINING PREPROCESSING
│   ├── convert_fls.py                  # FLS sonar dataset conversion to YOLO format
│   ├── convert_uatd.py                 # UATD underwater dataset conversion
│   ├── convert_seaclear.py             # SeaClear dataset converter
│   ├── create_combined_dataset.py      # Unified 50-class combined dataset generator
│   ├── marineguard_classes.yaml        # 50-class authoritative taxonomy
│   ├── unified_classes.yaml            # Unified label mappings
│   ├── validate_marineguard.py         # Dataset integrity & label validation
│   ├── train_yolov8_seg.py             # YOLOv8 segmentation training script
│   └── run_full_training.py            # Full dataset training executor
│
├── 🧪 TESTING & EVALUATION SUITE
│   ├── tests/
│   │   ├── test_api.py                 # FastAPI endpoint tests
│   │   ├── test_confidence.py          # Confidence calibration tests
│   │   ├── test_detection.py           # Optical & sonar detection tests
│   │   ├── test_evidence.py            # Evidence extraction tests
│   │   ├── test_exporters.py           # PDF, CSV, JSON, GeoJSON exporter tests
│   │   ├── test_filtering.py           # Filter rule & threshold tests
│   │   ├── test_mcp_detection.py       # MCP server tool tests
│   │   ├── test_optical_onnx.py        # ONNX inference tests
│   │   ├── test_side_scan.py           # Side-scan sonar pipeline tests
│   │   └── test_ui_and_eval.py         # UI and end-to-end evaluation tests
│   ├── eval.py, eval_detection.py      # Evaluation and precision/recall metrics
│   ├── benchmark_v1_latency.py         # Model inference latency benchmarking
│   └── v1_latency_benchmark.json       # Measured latency metrics
│
└── 📚 DOCUMENTATION
    ├── README.md                       # Main project overview & benchmark metrics
    ├── AGENTS.md / agents.md           # Role boundaries, execution rules & scope guidelines
    ├── docs/PROJECT_DOCUMENTATION.md   # Deep architectural specification
    ├── docs/HANDOFF_CONTRACT.md        # Inter-role contracts & interfaces
    └── docs/ROLE_*.md                  # Individual role handoff & verification audits
```

---

## 🔍 Layer Breakdown & Key Entry Points

### 1. 🎨 Frontend / UI Layer
* **Streamlit Dashboard**: `streamlit_demo.py` (Run via `streamlit run streamlit_demo.py`)
  * Supports post-mission sonar data upload, instant AI detection, confidence thresholding, interactive GIS maps (when coordinates are available), and direct report downloads.
* **React Web Frontend**: `my-react-router-app/` (Run via `npm run dev`)
  * High-performance React Router v7 + Tailwind application with bounding box visualizer and report generator.

### 2. 🔌 Backend & API Layer
* **FastAPI Server**: `api_server.py` (Run via `python api_server.py` or `uvicorn api_server:app --port 8000`)
  * REST API connecting frontends to YOLOv8 inference, filtering, and exporters.
* **MCP Server**: `marineguard/mcp_server.py` (Model Context Protocol tool provider)
  * Exposes detection, filtering, and reporting tools to AI agent orchestrators.

### 3. 🧠 AI & Detection Pipeline
* **Authoritative YOLOv8n Model**: Loaded via `marineguard/detection/sss_yolo_adapter.py` and validated with SHA256 integrity checks.
* **Side-Scan Sonar (SSS) Engine**: `marineguard/detection/side_scan.py` handling acoustic normalization, shadow enhancement, and multi-class anomaly detection.
* **Edge ONNX Engine**: `export_onnx.py` & `verify_onnx.py` for sub-10ms CPU/Edge deployment.

### 4. 🛡️ Post-Processing & Filtering
* **Confidence Calibration**: `marineguard/confidence.py` applying Platt/Isotonic scaling.
* **Domain Heuristics**: `marineguard/trace/confidence_filter.py` enforcing acoustic shadow-to-contact ratios.
* **Evidence Management**: `marineguard/evidence.py` generating forensic contact thumbnails.

### 5. 📄 Reporting & GIS Exporters
* **PDF Exporter**: `marineguard/exporters/pdf_exporter.py` generating ReportLab audit documents.
* **GeoJSON Exporter**: `marineguard/exporters/geojson_exporter.py` for QGIS/ArcGIS maritime layers.
* **S-100 / S-124 Exporter**: `marineguard/exporters/s100_exporter.py` for navigational hazard warnings.

### 6. 📊 Preprocessing & Training
* **Dataset Normalization**: Converters for FLS, UATD, SeaClear, and TrashCan into unified 50-class YOLO format.

### 7. 🧪 Testing & Evaluation
* **Pytest Suite**: 18 test suites covering API, detection, evidence, exporters, and filtering (`pytest`).
