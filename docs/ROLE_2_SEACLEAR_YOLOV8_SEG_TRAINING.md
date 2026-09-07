# MarineGuard MCP — Role 2: SeaClear YOLOv8-Seg Training & Verification Report

**Document Date**: 2026-09-07  
**Author**: Role 2 AI Inference & Integration Lead  
**Status**: **COMPLETED** (50/50 Epochs Trained, Validated, and Evaluated on Held-Out Test Split)  
**Model Checkpoint**: `runs/seaclear_yolov8n_seg/train/weights/best.pt`  

---

## 1. Purpose & Scope

This document provides the formal record of the completed **YOLOv8n-seg** instance segmentation training run on the verified SeaClear underwater segmentation dataset for **MarineGuard MCP**.

The training run completed all **50 of 50 planned epochs** normally and without interruption. Post-training evaluation was successfully conducted against both the **validation split (1,722 images)** and the independent, **held-out test split (861 images)**.

---

## 2. Completed Training Run Overview

> YOLOv8n-seg training on the SeaClear segmentation dataset completed successfully for all 50 planned epochs.

The training was performed on CPU (Intel runtime via PyTorch) and took approximately **19.17 hours** (69,013.97 seconds). Training converged smoothly without interruption, out-of-memory errors, or hardware failures.

### Summary of Run Parameters
* **Status**: COMPLETED normally (not interrupted)
* **Epochs Planned**: 50
* **Epochs Completed**: 50 / 50
* **Runtime**: ~19.17 hours (69,013.97 s)
* **Execution Environment**: PyTorch CPU build on Python 3.14
* **Best Checkpoint**: `runs/seaclear_yolov8n_seg/train/weights/best.pt` (Epoch 48)
* **Final Checkpoint**: `runs/seaclear_yolov8n_seg/train/weights/last.pt` (Epoch 50)

---

## 3. Dataset & Taxonomy Architecture

### 3.1 Why SeaClear Segmentation was Selected
The SeaClear dataset provides high-quality polygon segmentations for underwater debris, marine life, and aquatic machinery. Unlike bounding-box-only datasets, instance segmentation delivers pixel-accurate masks essential for distinguishing object boundaries from murky seabed clutter and marine growth.

### 3.2 Dataset Preparation & Splits
The dataset is configured via `data/processed/seaclear_segmentation/data.yaml` and consists of 8,610 verified image-label pairs with 31,555 polygon instances:

| Dataset Split | Image Count | Segmentation Label Files | Verification Status | Missing / Corrupt | Split Role |
|---|---|---|---|---|---|
| **Train** | 6,027 | 6,027 | 100% paired | 0 | Optimization |
| **Validation** | 1,722 | 1,722 | 100% paired | 0 | Model checkpoint selection & hyperparameter tracking |
| **Held-Out Test** | 861 | 861 | 100% paired | 0 | Final unbiased generalization evaluation |
| **Total** | **8,610** | **8,610** | **100% paired** | **0** | **31,555 polygon instances** |

The held-out test split remained strictly untouched during training and was only evaluated after all 50 epochs were completed.

### 3.3 Taxonomy Consistency Across Multi-Sensor Modalities
* **Total MarineGuard Classes**: 50 classes (`nc: 50`), defined strictly in [`marineguard_classes.yaml`](file:///d:/Marine%20Drive/marineguard-mcp/marineguard_classes.yaml) (indices `0` to `49`).
* **Active Optical Classes**: 35 active classes from the SeaClear dataset map directly to their exact official IDs (e.g., `bottle` = 0, `can` = 1, `tire` = 8, `cement-tube` = 21, `animal` = 23, `glass-bottle` = 25).
* **Reserved Acoustic Classes**: The remaining 15 classes (e.g., `chain`, `drink-carton`, `hook`, `propeller`, `valve`, `plane`, `rov`) represent sonar/acoustic modalities (FLS/UATD) and are preserved with 0 optical instances to ensure project-wide taxonomy alignment and prevent class-index collisions during multimodal fusion.

### 3.4 Polygon Segmentation Label Quality
* **Format**: Standard YOLO polygon format (`class_id x_1 y_1 x_2 y_2 ... x_n y_n`).
* **Coordinate Space**: Normalized $[0.0, 1.0]$.
* **Total Instances**: 31,555 valid polygon instances.
* **Vertex Density**: Minimum 3 vertices, maximum 320 vertices, average 28.44 vertices per instance.
* **Quality**: 0 invalid lines, 0 out-of-bounds coordinates, 0 degenerate polygons.

---

## 4. Training Configuration & Methodology

The training was launched using the dedicated pipeline script `train_yolov8_seg.py` under the following verified configuration:

| Configuration Parameter | Verified Value | Rationale / Notes |
|---|---|---|
| **Base Architecture** | `yolov8n-seg.pt` | Lightweight nano segmentation backbone for real-time edge deployment |
| **Task** | `segment` | Instance segmentation (bounding box + pixel-accurate polygon mask) |
| **Image Resolution (`imgsz`)** | `512` | Balanced resolution for underwater object clarity and inference speed |
| **Planned Epochs** | `50` | Full convergence schedule |
| **Completed Epochs** | `50` | 100% completed without interruption |
| **Batch Size** | `16` | Optimal throughput |
| **Workers** | `0` | Windows multiprocessing stability |
| **Device** | `cpu` | Executed via PyTorch CPU runtime |
| **Automatic Mixed Precision (`amp`)** | `True` | Standard training precision setting |
| **Optimizer** | `auto` | Auto-configured SGD/AdamW (`lr0=0.01`, `lrf=0.01`, `momentum=0.937`, `weight_decay=0.0005`) |
| **Warmup** | `3.0 epochs` | Linear warmup (`warmup_momentum=0.8`, `warmup_bias_lr=0.1`) |
| **Patience** | `100` | Early stopping threshold (did not trigger; all 50 epochs completed) |
| **Dataset Configuration** | `data/processed/seaclear_segmentation/data.yaml` | Dedicated SeaClear segmentation YAML |
| **Output Directory** | `runs/seaclear_yolov8n_seg/train/` | Dedicated run artifacts directory |
| **Total Duration** | `69,013.97 seconds (~19.17 hours)` | Completed normally on 2026-09-07 |

---

## 5. Checkpoints & Generated Artifacts

All training weights, metric logs, and visualization curves were generated in `runs/seaclear_yolov8n_seg/`:

| Artifact Path | Size / Details | Description |
|---|---|---|
| [`runs/seaclear_yolov8n_seg/train/weights/best.pt`](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/train/weights/best.pt) | 6,769,652 bytes (~6.46 MB) | **Best checkpoint** saved at **Epoch 48** (highest validation mask mAP50-95). Selected for downstream inference and ONNX export. |
| [`runs/seaclear_yolov8n_seg/train/weights/last.pt`](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/train/weights/last.pt) | 6,769,652 bytes (~6.46 MB) | Final checkpoint saved at **Epoch 50**. |
| [`runs/seaclear_yolov8n_seg/train/results.csv`](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/train/results.csv) | 52 lines (50 epoch records) | Full tabular progression of training/validation losses and metrics. |
| [`runs/seaclear_yolov8n_seg/training_summary.json`](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/training_summary.json) | 445 lines (JSON format) | Structured evaluation metrics summary covering validation, held-out test, and per-class metrics. |
| [`runs/seaclear_yolov8n_seg/val_evaluation/`](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/val_evaluation/) | Directory with plots & metrics | Dedicated post-training validation evaluation run artifacts. |
| [`runs/seaclear_yolov8n_seg/test_evaluation/`](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/test_evaluation/) | Directory with plots & metrics | Dedicated post-training held-out test split evaluation run artifacts. |
| **Visualizations & Curves** | `results.png`, `confusion_matrix.png`, `confusion_matrix_normalized.png`, Box/Mask PR/P/R/F1 curves | Complete set of diagnostic plots and batch prediction visual samples. |

> [!IMPORTANT]
> **Checkpoint Distinction**:
> * `best.pt` represents the optimal validation performance checkpoint (achieved at **Epoch 48** with validation Mask mAP50-95 of 0.3806 / Box mAP50 of 0.6522).
> * `last.pt` represents the final epoch (**Epoch 50**).
> * `best.pt` is the designated checkpoint for downstream ONNX export and inference integration.
> * Training reached full convergence; no resumption or retraining is needed.

---

## 6. Verified Validation Results

Validation was performed on the full **validation split (1,722 images)**:

| Metric Modality | Precision ($P$) | Recall ($R$) | mAP@0.50 | mAP@0.50:0.95 | $F_1$ Score |
|---|---|---|---|---|---|
| **Bounding Box (Detection)** | **0.8012** (80.12%) | **0.5968** (59.68%) | **0.6522** (65.22%) | **0.4791** (47.91%) | **0.6840** |
| **Mask (Segmentation)** | **0.7827** (78.27%) | **0.5779** (57.79%) | **0.6268** (62.68%) | **0.3806** (38.06%) | **0.6649** |

---

## 7. Verified Held-Out Test Results

Evaluation was executed on the independent, untouched **held-out test split (861 images)**:

| Metric Modality | Precision ($P$) | Recall ($R$) | mAP@0.50 | mAP@0.50:0.95 | $F_1$ Score |
|---|---|---|---|---|---|
| **Bounding Box (Detection)** | **0.8179** (81.79%) | **0.5922** (59.22%) | **0.6867** (68.67%) | **0.4921** (49.21%) | **0.6870** |
| **Mask (Segmentation)** | **0.8149** (81.49%) | **0.5570** (55.70%) | **0.6435** (64.35%) | **0.3938** (39.38%) | **0.6617** |

### Key Observations:
1. **Generalization Consistency**: Test performance matches and slightly exceeds validation performance (Test Mask mAP50: 64.35% vs Val Mask mAP50: 62.68%; Test Box mAP50: 68.67% vs Val Box mAP50: 65.22%), confirming robust generalization without overfitting to train/val distributions.
2. **High Precision**: The model demonstrates strong precision ($>81\%$ on test box and mask), effectively suppressing false alarms in challenging marine imagery.

---

## 8. Important Technical Distinctions

1. **Optical Segmentation vs. Acoustic Detection**:
   * This model (`yolov8n-seg.pt` trained on SeaClear) is strictly an **optical instance segmentation model**.
   * It is distinct from Member 1's YOLOv8n **bounding-box detector** (`runs/marineguard_full_512_b16-2/weights/best.pt`).
   * The segmentation model does not replace the acoustic/sonar detector; rather, it provides precise pixel masks for the optical camera channel.
2. **Role in Multimodal Fusion Pipeline**:
   * In the MarineGuard architecture, optical segmentation masks provide spatial extent, boundary definition, and visual class probabilities.
   * Sonar detections provide range and robust detection under zero-visibility turbidity.
   * Bathymetric data provides seabed elevation and seafloor context.
   * Multimodal fusion (`fusion.py`) combines these independent sensor streams. Training this segmentation model is an essential prerequisite, but does not by itself complete multimodal fusion.

---

## 9. Limitations

Based strictly on verified training data and outputs:
1. **Dataset Domain**: The model is trained on the SeaClear underwater optical dataset. Generalization is highest in comparable shallow-water and coastal optical conditions.
2. **Scope of Test Metrics**: The reported test metrics apply specifically to the 861-image held-out SeaClear test split.
3. **Single-Sensor Scope**: This segmentation model represents the optical modality alone and should not be treated as the full multimodal MarineGuard system.
4. **Integration Status**: Downstream ONNX export, runtime integration in `optical.py`, and fusion retuning in `fusion.py` are separate downstream engineering steps.

---

## 10. Recommended Next Steps

The recommended sequence for downstream integration is:

1. **Checkpoint Selection**: Deploy `runs/seaclear_yolov8n_seg/train/weights/best.pt` as the selected optical segmentation checkpoint.
2. **ONNX Export**: Export the PyTorch segmentation model to ONNX format.
3. **Validation of ONNX Inference**: Validate ONNX inference output against the PyTorch model.
4. **Optical Path Integration**: Integrate the segmentation model into the optical inference pipeline (`optical.py`).
5. **Multimodal Fusion Calibration**: Evaluate and retune fusion behavior (`fusion.py`) using real segmentation outputs.
6. **End-to-End System Evaluation**: Perform final end-to-end system evaluation across all sensor modalities.

