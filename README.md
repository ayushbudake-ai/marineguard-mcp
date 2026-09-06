# 🌊 MarineGuard MCP

### AI-Powered Automated Underwater Marine Debris & Anomaly Detection

**SIH 2026 — Problem Statement SIH26057**

MarineGuard MCP is an AI-based underwater marine debris and anomaly detection system designed for **side-scan sonar imagery**.

The project focuses on converting underwater sonar imagery into structured, explainable detections that can be consumed by downstream processing, reporting, and MCP-based application components.

---

## 🎯 Problem Statement

Underwater marine debris is difficult to detect manually because sonar imagery can contain:

* Low visibility
* Noise and clutter
* Shadows and highlights
* Complex seabed backgrounds
* Small or partially occluded objects
* Large volumes of survey imagery

MarineGuard aims to automate this detection process using computer vision and a standardized detection pipeline.

---

# 🧠 Current System

The current project is organized around the following pipeline:

```text
Side-Scan Sonar Imagery
        │
        ▼
┌─────────────────────┐
│ Dataset Processing  │
│ & Validation        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ MarineGuard V1      │
│ YOLOv8n Detector    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Structured Detection│
│ Output              │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Downstream Pipeline │
│ Roles 2 → 5         │
└─────────────────────┘
```

The repository separates the **frozen V1 baseline** from future experimental work.

---

# 📊 MarineGuard V1 Baseline

The V1 dataset is the official frozen baseline for the project.

| Property             |      Value |
| -------------------- | ---------: |
| Dataset version      |     **V1** |
| Classes              |     **50** |
| Total images         | **18,073** |
| Total labels         | **18,073** |
| Valid bounding boxes | **46,209** |
| Training images      | **12,652** |
| Validation images    |  **3,613** |
| Test images          |  **1,808** |

### V1 Model

| Property     | Value            |
| ------------ | ---------------- |
| Architecture | YOLOv8n          |
| Task         | Object Detection |
| Input        | 512 × 512        |
| Classes      | 50               |
| Status       | **FROZEN**       |

### V1 Test Results

| Metric    |     Result |
| --------- | ---------: |
| Precision | **89.70%** |
| Recall    | **71.90%** |
| F1        | **79.94%** |
| mAP50     | **80.69%** |
| mAP50-95  | **55.74%** |

The V1 test set is held out and must not be modified during model development.

---

# 📦 Dataset Sources

MarineGuard V1 combines the following source datasets:

1. **FLS**
2. **UATD**
3. **SeaClear**

The source datasets are converted into the MarineGuard 50-class taxonomy before combination.

### SeaClear V1 GitHub Artifact

The SeaClear YOLO package distributed through Git LFS contains:

* **8,610 images**
* **8,610 labels**
* Dataset YAML

The processed 27.9 GB V1 dataset is **not stored as a normal Git repository artifact**. It is reproducibly generated from the source datasets.

---

# 🏷️ 50-Class Taxonomy

MarineGuard uses a fixed **50-class taxonomy**.

The authoritative class definitions are maintained in:

```text
marineguard_classes.yaml
unified_classes.yaml
```

V1 class IDs must not be reordered.

---

# 📁 Repository Structure

```text
marineguard-mcp/
│
├── data/
│   └── raw/
│       └── seaclear/
│
├── docs/
│   ├── HANDOFF_CONTRACT.md
│   ├── PROJECT_DOCUMENTATION.md
│   ├── ROLE_DEPENDENCY_MATRIX.md
│   ├── MODEL_REGISTRY.md
│   ├── DETECTION_SCHEMA.json
│   ├── V1_DATASET_MANIFEST.md
│   └── ROLE1_HANDOFF_CHECKLIST.md
│
├── marineguard/
│
├── tests/
│
├── runs/
│   └── marineguard_full_512_b16-2/
│       └── weights/
│           └── best.pt
│
├── convert_fls.py
├── convert_uatd.py
├── convert_seaclear.py
├── create_combined_dataset.py
├── validate_marineguard.py
│
├── run_full_training.py
├── run_sanity.py
│
├── marineguard_classes.yaml
├── unified_classes.yaml
├── requirements.txt
│
├── ROLE1_FINAL_RESULTS.md
├── ROLE1_TO_ROLE2_HANDOFF.md
└── README.md
```

---

# 🔬 Data Processing Pipeline

The V1 preprocessing pipeline is:

```text
Raw Source Dataset
        │
        ▼
Source-specific Conversion
        │
        ├── convert_fls.py
        ├── convert_uatd.py
        └── convert_seaclear.py
        │
        ▼
MarineGuard Taxonomy
        │
        ▼
Combined Dataset
        │
        ▼
Validation
        │
        ▼
Train / Val / Test
        │
        ▼
YOLO Training
        │
        ▼
V1 Baseline Model
```

---

# 🤝 Role-Based Architecture

MarineGuard development is divided into five roles.

### Role 1 — Data & Preprocessing

Responsible for:

* Dataset ingestion
* Annotation conversion
* Taxonomy
* Dataset validation
* Train/validation/test splitting
* Baseline training
* Evaluation
* Model and dataset handoff

**Status: COMPLETE**

### Role 2 — Detection Integration

Consumes the Role 1 V1 model and integrates the detector into the application pipeline.

### Role 3 — Confidence & Filtering

Consumes structured detector outputs and performs downstream confidence/filtering logic.

### Role 4 — Reporting & Geolocation

Consumes filtered detections and adds reporting/geolocation information.

### Role 5 — Application / MCP Integration

Consumes the downstream detection and reporting interfaces and integrates them into the application.

Detailed dependencies are documented in:

```text
docs/ROLE_DEPENDENCY_MATRIX.md
docs/HANDOFF_CONTRACT.md
```

---

# 📤 Detection Output Contract

The standardized detector output is:

```json
{
  "frame_id": "frame_000001",
  "model_version": "v1",
  "detections": [
    {
      "class_id": 0,
      "class_name": "bottle",
      "confidence": 0.91,
      "bbox": {
        "x1": 120,
        "y1": 80,
        "x2": 310,
        "y2": 350
      }
    }
  ]
}
```

The formal JSON Schema is available at:

```text
docs/DETECTION_SCHEMA.json
```

This contract provides a stable interface between the detector and downstream roles.

---

# 🚀 Reproducing the Dataset

A developer reproducing the V1 baseline should:

```text
1. Obtain the required source datasets.
2. Place them under data/raw/.
3. Run the source conversion scripts.
4. Create the combined dataset.
5. Run dataset validation.
6. Verify the expected V1 counts.
7. Train/evaluate using the portable dataset configuration.
```

The repository intentionally avoids machine-specific absolute paths.

For example, dataset configuration uses:

```yaml
path: .
train: images/train
val: images/val
test: images/test
```

This allows the repository to work across different Windows and Linux machines.

---

# 📥 Getting the Repository

```bash
git clone https://github.com/ayushbudake-ai/marineguard-mcp.git
cd marineguard-mcp
```

Install Git LFS before retrieving large artifacts:

```bash
git lfs install
git lfs pull
```

---

# 🧪 V1 Verification

A successful V1 reproduction should produce:

```text
Images:      18,073
Labels:      18,073
Valid boxes: 46,209

Train: 12,652
Val:    3,613
Test:   1,808
```

The V1 baseline checkpoint is:

```text
runs/marineguard_full_512_b16-2/weights/best.pt
```

Its SHA-256 checksum is recorded in:

```text
docs/MODEL_REGISTRY.md
```

---

# 🔒 V1 Freeze Policy

V1 is the official frozen baseline.

The following must not be silently changed:

* Dataset
* Test set
* Class IDs
* Class mapping
* Model checkpoint
* V1 evaluation methodology

Any change to:

* Source dataset
* Source dataset version
* Preprocessing
* Class mapping
* Filtering
* Dataset split
* Annotation conversion

requires a new dataset version.

For example:

```text
V1
V2
V3
```

V2 experimental work must not replace V1 until it has been independently evaluated and formally promoted.

---

# 🧪 Experimental V2

V2 development is treated separately from the frozen V1 baseline.

The V1 model remains the official comparison baseline until a future version satisfies the project's evaluation and handoff requirements.

---

# 📚 Documentation

The `docs/` directory is the primary technical documentation source.

Important documents:

| Document                     | Purpose                                    |
| ---------------------------- | ------------------------------------------ |
| `HANDOFF_CONTRACT.md`        | Cross-role interface and artifact contract |
| `ROLE_DEPENDENCY_MATRIX.md`  | Dependencies between Roles 1–5             |
| `MODEL_REGISTRY.md`          | Model versions, checksums and metrics      |
| `DETECTION_SCHEMA.json`      | Detector output contract                   |
| `V1_DATASET_MANIFEST.md`     | Frozen V1 dataset identity                 |
| `ROLE1_HANDOFF_CHECKLIST.md` | Role 1 completion checklist                |
| `PROJECT_DOCUMENTATION.md`   | Overall technical documentation            |
| `ROLE1_FINAL_RESULTS.md`     | V1 training/evaluation results             |
| `ROLE1_TO_ROLE2_HANDOFF.md`  | Role 1 → Role 2 handoff                    |

---

# 🛡️ Engineering Principles

MarineGuard follows several important project rules:

* **GitHub is the authoritative handoff source.**
* **V1 remains frozen.**
* **Test data remains held out.**
* **No machine-specific paths in portable configuration.**
* **Large artifacts use Git LFS or controlled distribution.**
* **Model versions are explicitly tracked.**
* **Detection interfaces are schema-defined.**
* **Downstream roles consume documented contracts rather than local assumptions.**
* **Experimental V2 work must not silently replace V1.**

---

# 📌 Current Status

### Role 1 — Data & Preprocessing

**🟢 COMPLETE**

The official Role 1 handoff has been verified from a fresh GitHub clone.

Verified:

```text
✓ GitHub repository
✓ Git LFS
✓ SeaClear V1 dataset
✓ 8,610 images
✓ 8,610 labels
✓ V1 model
✓ Model checksum
✓ 50-class taxonomy
✓ Detection schema
✓ Dataset manifest
✓ Model registry
✓ Role dependency matrix
✓ Role 1 handoff documentation
✓ Portable training paths
✓ Fresh-clone reproducibility
```

The frozen V1 baseline is ready for downstream integration.

---

# 📄 License

See the repository license and the individual source-dataset licenses/terms before redistributing source data or derived artifacts.

---

## 🌊 MarineGuard MCP

**SIH 2026 — SIH26057**

AI-powered underwater marine debris and anomaly detection using side-scan sonar imagery.
