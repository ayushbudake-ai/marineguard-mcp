# Role 1 → Role 2 Handoff

## 1. V1 Model

**Model version:** `v1`
**Model:** MarineGuard V1
**Architecture:** YOLOv8n
**Task:** Object Detection
**Classes:** 50
**Input size:** `512 × 512`

This checkpoint is an **object detector, not a segmentation model**.

---

## 2. Trained Checkpoint

Repository-relative path:

```text
runs/marineguard_full_512_b16-2/weights/best.pt
```

The checkpoint is tracked using **Git LFS**.

### Retrieve from GitHub

After cloning the repository:

```powershell
git lfs install
git lfs pull
```

The checkpoint will be available at:

```text
runs/marineguard_full_512_b16-2/weights/best.pt
```

Do **not** use a machine-specific absolute path.

### Model integrity

**SHA-256:**

```text
18C9E560B9E82BB6EFE3A108584497C4979A9E135BED578DB179341E0778E0D1
```

**File size:** `6,226,410 bytes`

The checksum can be verified with:

```powershell
Get-FileHash .\runs\marineguard_full_512_b16-2\weights\best.pt -Algorithm SHA256
```

---

## 3. V1 Dataset

MarineGuard V1 contains:

```text
Images:        18,073
Labels:        18,073
Classes:       50
Valid boxes:   46,209

Train:         12,652
Validation:     3,613
Test:           1,808
```

The test set is held out and must remain untouched for model-development decisions.

The processed V1 dataset is a generated artifact and is **not distributed as a 27.9 GB Git repository artifact**.

Reproduction information is documented in:

```text
docs/V1_DATASET_MANIFEST.md
```

---

## 4. Class Taxonomy

The authoritative 50-class taxonomy is:

```text
marineguard_classes.yaml
```

Class IDs must not be reordered for V1.

---

## 5. Detection Output Contract

The canonical detector output schema is:

```text
docs/DETECTION_SCHEMA.json
```

Expected structure:

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

Role 2 integration must preserve:

* `frame_id`
* `model_version`
* `class_id`
* `class_name`
* `confidence`
* bounding box coordinates

Do not invent a different detection contract without updating the downstream dependency documentation.

---

## 6. V1 Held-Out Test Results

| Metric    | Result |
| --------- | -----: |
| Precision | 89.70% |
| Recall    | 71.90% |
| F1        | 79.94% |
| mAP50     | 80.69% |
| mAP50-95  | 55.74% |

These results are the **frozen V1 baseline**.

---

## 7. Role 2 Responsibilities

Role 2 is responsible for:

1. ONNX export
2. Real detector integration
3. Real per-detection confidence outputs
4. Fusion retuning
5. Downstream integrated evaluation

Role 2 must consume the V1 model and contracts rather than creating a separate incompatible detector interface.

---

## 8. ONNX Export

The exported ONNX model must preserve the V1 model's:

* 50-class taxonomy
* class IDs
* object-detection task
* input resolution expectations
* per-detection confidence information

The ONNX model should be treated as a derived artifact from V1 unless a new model version is explicitly created.

---

## 9. Downstream Dependencies

Role 2 must provide outputs compatible with:

```text
Role 3 → confidence calibration/filtering
Role 4 → reporting/geotagging
Role 5 → Streamlit/MCP integration
```

The canonical schema is:

```text
docs/DETECTION_SCHEMA.json
```

The dependency definitions are documented in:

```text
docs/ROLE_DEPENDENCY_MATRIX.md
docs/HANDOFF_CONTRACT.md
```

---

## 10. Model Registry

The authoritative model metadata is maintained in:

```text
docs/MODEL_REGISTRY.md
```

V1 must remain frozen.

If Role 2 produces a materially different model or changes the model architecture, taxonomy, preprocessing, or evaluation protocol, it must receive a new model/version identifier rather than silently replacing V1.

---

## 11. Important V1 Rules

* V1 is the frozen baseline.
* Do not overwrite the V1 checkpoint with V2.
* Do not reorder V1 class IDs.
* Do not modify the held-out V1 test set.
* Do not hardcode machine-specific paths.
* Do not silently change the detection JSON contract.
* V2 remains experimental and paused until formally selected as the new baseline.

---

## 12. Quick Start for Role 2

From a fresh clone:

```powershell
git clone https://github.com/ayushbudake-ai/marineguard-mcp.git
cd marineguard-mcp
git lfs install
git lfs pull
```

Verify the model exists:

```powershell
Test-Path .\runs\marineguard_full_512_b16-2\weights\best.pt
```

Verify the checksum:

```powershell
Get-FileHash .\runs\marineguard_full_512_b16-2\weights\best.pt -Algorithm SHA256
```

Expected:

```text
18C9E560B9E82BB6EFE3A108584497C4979A9E135BED578DB179341E0778E0D1
```

Then inspect:

```text
marineguard_classes.yaml
docs/DETECTION_SCHEMA.json
docs/MODEL_REGISTRY.md
docs/ROLE_DEPENDENCY_MATRIX.md
docs/HANDOFF_CONTRACT.md
```

---

## Status

**Role 1 V1 handoff to Role 2: READY**

V1 model, taxonomy, dataset metadata, test baseline, retrieval instructions, and detection contract are available through the GitHub repository.
