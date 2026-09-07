# MarineGuard MCP — Role 2: Segmentation Dataset Feasibility Audit

**Audit Date**: 2026-09-06  
**Auditor**: Role 2 AI Inference & Integration Lead  
**Scope**: Technical assessment of Member 1's dataset for `YOLOv8-seg` / `U-Net` instance/semantic segmentation feasibility.

---

## 1. Executive Summary & Verdict

> [!CAUTION]
> ### Verdict: **NOT READY FOR YOLOv8-SEG — BOUNDING BOXES ONLY** (Option B)
> 
> A thorough technical audit of all dataset conversion scripts (`convert_fls.py`, `convert_seaclear.py`, `convert_uatd.py`, `create_combined_dataset.py`), raw data formats, and processed label files confirms that **100% of Member 1's 46,209 annotations across 18,073 images are 2D Bounding Boxes (`class_id center_x center_y width height`)**.
>
> Zero polygon coordinates or segmentation masks exist in the prepared dataset. Per project safety and integrity rules, pseudo-masks (converting rectangle boxes into fake polygons) are strictly prohibited. Therefore, `YOLOv8-seg` training cannot be legitimately performed on this dataset.

---

## 2. Dataset Location & Lineage

### Training Dataset Configuration
* **Config File**: `data/processed/marineguard/data.yaml`
* **Dataset Root**: `data/processed/marineguard` (generated via `create_combined_dataset.py`)
* **Source Datasets Ingested by Member 1**:
  1. **FLS (Forward Looking Sonar)**: Marine Debris Watertank Release (1,868 images, 2,364 boxes)
  2. **UATD (Underwater Acoustic Target Detection)**: Sonar imagery (Pascal VOC XML bounding boxes)
  3. **SeaClear**: Underwater optical imagery (COCO format, converted bounding boxes)

### Dataset Split Breakdown

| Split | Image Count | % of Dataset | Bounding Box Annotations | Segmentation Masks |
|---|---:|---:|---:|---:|
| **Train** | 12,652 | 69.98% | ~32,346 | **0 (0.0%)** |
| **Validation** | 3,613 | 19.99% | ~9,242 | **0 (0.0%)** |
| **Test (Held-Out)** | 1,808 | 10.00% | ~4,621 | **0 (0.0%)** |
| **Total** | **18,073** | **100.0%** | **46,209** | **0 (0.0%)** |

---

## 3. Annotation Format Audit

Each label file was inspected across the pipeline:

### A. FLS Sonar Labels (`data/processed/fls/labels/`)
* **Raw Format**: JSON (`annotations.json`) with keys `bounding-boxes` -> `[top-left-x, top-left-y, width, height]`.
* **Processed Format**: YOLO standard 5-token text lines:
  ```text
  1 0.511000 0.270248 0.162000 0.110744
  3 0.430365 0.450608 0.116438 0.074468
  ```
* **Polygon Points**: None. Exactly 5 numbers per line across all 2,364 annotations.

### B. UATD Sonar Labels (`data/raw/uatd/`)
* **Raw Format**: Pascal VOC XML with `<bndbox>` elements (`<xmin>`, `<ymin>`, `<xmax>`, `<ymax>`).
* **Processed Format**: Standard YOLO 5-token bounding boxes.
* **Polygon Points**: None.

### C. SeaClear Optical Labels (`convert_seaclear.py`)
* **Raw Format**: COCO format (`dataset.json`).
* **Conversion Code**: `convert_seaclear.py` strictly extracted `ann["bbox"]` and explicitly notes:
  > *"Segmentation polygons were intentionally not converted. Only bounding boxes were converted for the YOLO detection pipeline."*
* **Processed Format**: Standard YOLO 5-token bounding boxes.

### D. Combined Dataset Pipeline (`create_combined_dataset.py`)
* **Line Filter**:
  ```python
  parts = line.split()
  if len(parts) != 5:
      continue  # Strictly requires 5-token bounding box format
  ```

---

## 4. Class Taxonomy Verification

* **Taxonomy File**: `marineguard_classes.yaml`
* **Class Count**: Exactly **50 classes** (indices `0` to `49`).
* **Mapping Consistency**: All 3 source datasets map cleanly into the 50 classes with 0 class-ID shifts.
* **Segmentation Annotation Count per Class**: **0 for all 50 classes**.

---

## 5. Technical Assessment: Why YOLOv8-seg Cannot Train

1. **Ultralytics YOLO Segmentation Architecture**:
   * YOLOv8-seg models (e.g. `yolov8n-seg.pt`) require label lines formatted as polygons with $\ge 6$ coordinates:
     $$\text{class\_id } x_1\ y_1\ x_2\ y_2\ x_3\ y_3 \dots x_n\ y_n$$
   * When supplied with 5-token bounding box lines (`class_id cx cy w h`), the segmentation loss (Mask Proto loss) cannot be computed.
2. **Prohibition of Fabricated / Pseudo-Masks**:
   * Converting 4-corner bounding boxes into 4-point rectangle polygons produces trivial box-masks that do not represent true object contours, distorting segmentation metrics ($mAP_{mask}$) and creating false capabilities.
3. **Alignment with Role 1 Handoff**:
   * Member 1's handoff explicitly states:
     > *"This checkpoint is an object detector, not a segmentation model."*
     > *"YOLOv8-seg is a future Version 2 task."*

---

## 6. Actionable Recommendations & Next Steps

1. **Do NOT Start Segmentation Training**: Halt any attempt to train `YOLOv8-seg` or `U-Net` on the current dataset.
2. **Proceed with Role 2 Object Detection Deliverables**:
   * Integrate Member 1's delivered `best.pt` (YOLOv8n object detector: **89.70% Precision, 71.90% Recall, 79.94% F1, 80.69% mAP50**).
   * Complete ONNX export of `best.pt` (`export_onnx.py`).
   * Verify real-time inference across optical, side-scan sonar, and bathymetry sensor modules.
   * Expose structured detections via FastAPI (`POST /detect`) and MCP (`detect_marine_debris`).
   * Retune multi-sensor fusion weights using real detection confidences.
3. **Future Segmentation Roadmap (Version 2)**:
   * If segmentation is required in a future release, ingest true instance segmentation datasets (e.g., TrashCan 1.0 instance segmentation split or raw SeaClear polygon masks) and establish a dedicated segmentation annotation pipeline.
