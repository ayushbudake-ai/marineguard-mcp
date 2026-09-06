# MarineGuard MCP — Role 2: SeaClear YOLOv8-Seg Training & Pre-Flight Audit

**Audit Date**: 2026-09-06  
**Auditor**: Role 2 AI Inference & Integration Lead  
**Scope**: Pre-training dataset verification, YOLOv8n-seg model initialization, and pre-flight sanity check for the SeaClear segmentation dataset.

---

## 1. Pre-Training Dataset & Taxonomy Verification

* **Dataset Configuration File**: `data/processed/seaclear_segmentation/data.yaml`
* **Paths Configured**:
  * `train`: `images/train`
  * `val`: `images/val`
  * `test`: `images/test`
* **Class Count**: **50 classes** (`nc: 50`)
* **Taxonomy Consistency Explanation**:
  * The dataset YAML defines all 50 official classes from [`marineguard_classes.yaml`](file:///d:/Marine%20Drive/marineguard-mcp/marineguard_classes.yaml) (indices `0` to `49`).
  * The 40 SeaClear source categories map into **35 unique active MarineGuard classes** occupying their exact official IDs (e.g. `bottle` = 0, `can` = 1, `tire` = 8, `animal` = 23, `glass-bottle` = 25, `cement-tube` = 21, etc.).
  * The remaining **15 classes** (e.g. `chain`, `drink-carton`, `hook`, `propeller`, `valve`, `plane`, `rov`, etc.) belong strictly to sonar/acoustic modalities (FLS/UATD) and are present in the taxonomy definition with 0 instances in this optical dataset.
  * This preserves 100% project-wide taxonomy consistency and prevents class ID shifts across multi-sensor modules.

---

## 2. YOLOv8-Seg Label Format Verification

* **Total Label Files**: 8,610 across splits (`train`: 6,027, `val`: 1,722, `test`: 861).
* **Total Polygon Instances**: 31,555.
* **Coordinate Range**: Strictly normalized $[0.0, 1.0]$.
* **Format**: Standard YOLO segmentation line format:
  $$\text{class\_id } x_1\ y_1\ x_2\ y_2\ x_3\ y_3 \dots x_n\ y_n$$
* **Vertex Density**: Minimum 3 vertices, maximum 320 vertices, average **28.44 vertices** per instance.
* **Quality**: 0 invalid lines, 0 out-of-bounds coordinates, 0 degenerate polygons.

---

## 3. Pre-Training Sanity Check Results

A pre-flight validation check was executed using Ultralytics YOLOv8 segmentation:

| Check Item | Status | Details |
|---|---|---|
| **`data.yaml` Parsing** | **PASSED** | Validated `data/processed/seaclear_segmentation/data.yaml`, 50 classes, clean relative paths. |
| **Model Initialization** | **PASSED** | Successfully loaded official `yolov8n-seg.pt` checkpoint (`Task: segment`). |
| **Label Parsing & Format** | **PASSED** | 8,610 label files parsed with 31,555 valid polygon instances. |
| **Class IDs Validity** | **PASSED** | All class IDs belong to $[0, 49]$ and match [`marineguard_classes.yaml`](file:///d:/Marine%20Drive/marineguard-mcp/marineguard_classes.yaml). |
| **Split Disjointness** | **PASSED** | Zero file overlap across `train`, `val`, and `test` splits. |
| **Image Files on Disk** | **BLOCKED** | `data/processed/seaclear_segmentation/images/` currently contains **0 image files** on this machine. |

---

## 4. Reason for Image Absence & Blocker Analysis

1. **Source Archive Status**:
   * SeaClear raw archive `data/raw/seaclear/seaclear.rar` was partially downloaded (184 MB / 1.71 GB).
   * Per `DATA_HANDOFF.md`, Member 1 trained on a dedicated training environment (`C:\aaaa\SIH\marineguard-mcp\runs\marineguard_full_512_b16-2\weights\best.pt`) and excluded large image binary datasets from Git.
2. **Safety Rule Compliance**:
   * Per Step 3 of the task instructions:
     > *"If the sanity check fails: STOP. Do not attempt to silently repair the dataset. Report the exact error."*
   * Per core project rules: No fake images, no pseudo-masks, and no fabricated metrics.

---

## 5. Hardware & Environment Audit

* **GPU Hardware**: NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MB VRAM, Driver 560.94, CUDA 12.6 supported).
* **Installed Python Runtime**: Python 3.14.5.
* **Ultralytics**: Version 8.4.142 installed.
* **PyTorch Runtime**: PyTorch 2.14.0 (CPU build on Python 3.14).
* **Recommended Training Configuration (when images land)**:
  * `imgsz`: 512
  * `batch`: 16 (or 8 for safe VRAM clearance on 6GB RTX 3050)
  * `epochs`: 50
  * `workers`: 0 (for Windows stability)
  * `amp`: True

---

## 6. Actionable Next Steps to Resume Training

1. **Download / Extract Full SeaClear Images**:
   * Resume download of `seaclear.rar` (1.71 GB) or copy the SeaClear JPG images directly into `data/processed/seaclear_segmentation/images/{train,val,test}`.
2. **Execute Training Script**:
   * Run `yolo segment train data=data/processed/seaclear_segmentation/data.yaml model=yolov8n-seg.pt epochs=50 imgsz=512 batch=16 project=runs name=marineguard_seaclear_yolov8n_seg`.
3. **Evaluate on Held-Out Test Set**:
   * Run test evaluation against `data/processed/seaclear_segmentation/images/test/` to obtain real box and mask precision, recall, and mAP metrics.
