# MarineGuard MCP — Role 2: SeaClear YOLOv8-Seg Dataset

**Creation Date**: 2026-09-06  
**Author**: Role 2 AI Inference & Integration Lead  
**Scope**: Documentation of the genuine polygon segmentation dataset derived from original SeaClear COCO annotations for `YOLOv8-seg` optical underwater segmentation.

---

## 1. Source Dataset & Lineage

* **Origin**: Original SeaClear Underwater Optical Dataset (`data/raw/seaclear/seaclear.rar -> dataset.json`).
* **Source Annotation Standard**: COCO format (`categories`, `images`, `annotations`).
* **Source Quality**: 100% genuine manual polygon segmentations across all 8,610 images and 31,555 annotations.
* **Separation**: Stored in a distinct directory (`data/processed/seaclear_segmentation/`) without altering the existing bounding-box dataset (`data/processed/marineguard/`).

---

## 2. Annotation Format

The dataset uses standard **Ultralytics YOLOv8-seg segmentation format**. Each object is stored as a single line in `<image_name>.txt`:

$$\text{class\_id } x_1\ y_1\ x_2\ y_2\ x_3\ y_3 \dots x_n\ y_n$$

* **$\text{class\_id}$**: Integer in $[0, 49]$ mapped to the official MarineGuard taxonomy.
* **$x_i, y_i$**: Normalized polygon contour vertex coordinates:
  $$x_i = \frac{X_{\text{pixel}}}{W_{\text{image}}} \in [0.0, 1.0], \quad y_i = \frac{Y_{\text{pixel}}}{H_{\text{image}}} \in [0.0, 1.0]$$
* **Resolution**: All SeaClear source frames have a native resolution of $1920 \times 1080\text{ px}$.

---

## 3. Taxonomy Mapping

All 40 SeaClear source categories map losslessly into the official 50-class MarineGuard taxonomy defined in [`marineguard_classes.yaml`](file:///d:/Marine%20Drive/marineguard-mcp/marineguard_classes.yaml):

| SeaClear Category | SeaClear ID | MarineGuard Class | MarineGuard ID | Instances |
|---|---:|---|---:|---:|
| `bottle_plastic` | 4 | `bottle` | 0 | 1,261 |
| `can_metal` | 1 | `can` | 1 | 1,130 |
| `tire_rubber` | 25 | `tire` | 8 | 2,556 |
| `container_middle_size_metal` | 7 | `metal-bucket` | 10 | 60 |
| `tarp_plastic` | 2 | `tarp` | 19 | 31 |
| `container_plastic` | 3 | `plastic-container` | 20 | 84 |
| `tube_cement` | 5 | `cement-tube` | 21 | 1,404 |
| `plant` | 6 | `plant` | 22 | 472 |
| `animal_etc` / `animal_urchin` | 8, 17 | `animal` | 23 | 10,211 |
| `animal_sponge` | 9 | `sponge` | 24 | 1,110 |
| `bottle_glass` | 10 | `glass-bottle` | 25 | 2,331 |
| `wreckage_metal` | 11 | `metal-wreckage` | 26 | 265 |
| `unknown_instance` | 12 | `unknown-object` | 27 | 1,195 |
| `pipe_plastic` | 13 | `plastic-pipe` | 28 | 155 |
| `net_plastic` | 14 | `net` | 29 | 960 |
| `animal_shells` | 15 | `shell` | 30 | 995 |
| `rope_fiber` / `rope_plastic` | 16, 34 | `rope` | 31 | 2,047 |
| `cup_plastic` | 18 | `plastic-cup` | 32 | 329 |
| `brick_clay` | 19 | `brick` | 33 | 606 |
| `bag_plastic` | 20 | `plastic-bag` | 34 | 882 |
| `sanitaries_plastic` | 21 | `sanitary-waste` | 35 | 55 |
| `clothing_fiber` | 22 | `clothing` | 36 | 298 |
| `cup_ceramic` | 23 | `ceramic-cup` | 37 | 123 |
| `boot_rubber` | 24 | `rubber-boot` | 38 | 161 |
| `jar_glass` | 26 | `glass-jar` | 39 | 62 |
| `rov_cable` | 27 | `rov-cable` | 40 | 389 |
| `rov_tortuga` / `vehicle_leg` / `bluerov` | 28, 38, 39 | `rov-part` | 41 | 574 |
| `branch_wood` | 29 | `wood-branch` | 42 | 430 |
| `furniture_wood` | 30 | `furniture` | 43 | 15 |
| `snack_wrapper_plastic` / `paper` | 31, 37 | `snack-wrapper` | 44 | 180 |
| `lid_plastic` | 32 | `plastic-lid` | 45 | 20 |
| `cardboard_paper` | 33 | `cardboard` | 46 | 13 |
| `cable_metal` | 35 | `metal-cable` | 47 | 149 |
| `animal_fish` | 36 | `fish` | 48 | 985 |
| `animal_starfish` | 40 | `starfish` | 49 | 17 |

---

## 4. Dataset Structure & Configuration

```text
data/processed/seaclear_segmentation/
├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/       (6,027 files, 21,967 polygon instances)
    ├── val/         (1,722 files, 6,360 polygon instances)
    └── test/        (861 files, 3,228 polygon instances)
```

### Dataset YAML (`data.yaml`)
```yaml
path: data/processed/seaclear_segmentation
train: images/train
val: images/val
test: images/test
nc: 50
names:
  0: bottle
  1: can
  ...
  49: starfish
```

---

## 5. Split Strategy

Because the source `dataset.json` did not contain pre-defined split flags, the dataset was partitioned following the deterministic repository standard:

* **Train (70%)**: 6,027 images (21,967 polygon instances)
* **Validation (20%)**: 1,722 images (6,360 polygon instances)
* **Test (10%)**: 861 images (3,228 polygon instances)
* **Random Seed**: `42` with sorted image ID ordering.
* **Disjointness**: Verified 0% image/label overlap across splits.

---

## 6. Comprehensive Validation Results

* **Total Source Images**: 8,610
* **Total Source Annotations**: 31,555
* **Valid Polygon Instances Converted**: **31,555 (100.0%)**
* **Invalid Polygons / Lines**: **0 (0.0%)**
* **Out-of-Bounds Coordinates**: **0 (0.0%)**
* **Polygons with $< 3$ Vertices**: **0 (0.0%)**
* **Minimum Vertices per Polygon**: 3 vertices
* **Maximum Vertices per Polygon**: 320 vertices
* **Average Vertices per Polygon**: **28.44 vertices**

---

## 7. Class Distribution & Imbalance Analysis

* **Active Classes in SeaClear**: 35 MarineGuard classes.
* **Zero-Instance Classes (Sonar/Acoustic only)**: 15 classes (`chain`, `drink-carton`, `hook`, `propeller`, `shampoo-bottle`, `standing-bottle`, `valve`, `ball`, `cube`, `cylinder`, `circle-cage`, `square-cage`, `human-body`, `plane`, `rov`).
* **Top 5 Most Frequent Classes**:
  1. `animal` (ID 23): 10,211 instances in 2,945 images
  2. `tire` (ID 8): 2,556 instances in 2,260 images
  3. `glass-bottle` (ID 25): 2,331 instances in 1,355 images
  4. `rope` (ID 31): 2,047 instances in 1,364 images
  5. `cement-tube` (ID 21): 1,404 instances in 1,139 images
* **Rare Classes**:
  * `tarp` (ID 19): 31 instances
  * `plastic-lid` (ID 45): 20 instances
  * `starfish` (ID 49): 17 instances
  * `furniture` (ID 43): 15 instances
  * `cardboard` (ID 46): 13 instances

---

## 8. Important Multimodal Limitation

> [!WARNING]
> **Optical Domain Scope**:
> This dataset contains **optical underwater imagery only**. It is suitable for training an optical `YOLOv8-seg` model.
>
> The Forward-Looking Sonar (FLS) and UATD acoustic sonar sources do **not** contain polygon annotations (they are bounding-box only). Therefore, the overall multimodal system uses:
> * **Optical feed**: Object Detection + Instance Segmentation (`YOLOv8-seg`).
> * **Sonar feeds**: Object Detection (`YOLOv8n` bounding boxes).

---

## 9. Next Steps
* Review dataset statistics and validation metrics.
* When approved, train `YOLOv8-seg` (`yolov8n-seg.pt` or `yolov8s-seg.pt`) on `data/processed/seaclear_segmentation/data.yaml`.
