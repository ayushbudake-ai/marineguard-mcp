# MarineGuard — Cross-Role Handoff Contract

**Project:** MarineGuard MCP
**Current baseline:** V1
**V2 status:** PAUSED
**Owner:** Role 1 — Data & Preprocessing

---

## 1. Purpose

This document defines the machine-readable contracts between MarineGuard roles.

The objective is to ensure that every team member working on a different device can obtain the required artifacts and integrate their work without depending on another developer's local filesystem.

GitHub is the authoritative source for:

* source code
* configuration
* documentation
* schemas
* dataset manifests
* model metadata
* artifact distribution instructions

No role may depend on a developer-specific Windows path.

---

## 2. Role Pipeline

```text
Role 1
Data + Model
    ↓
Role 2
Detection
    ↓
Role 3
Confidence Filtering
    ↓
Role 4
Geotagging + Reporting
    ↓
Role 5
UI + Integration
```

Each role must consume the documented interface of the previous role.

---

## 3. Dataset Contract

### Dataset identity

Current baseline:

```text
Dataset: MarineGuard V1
Classes: 50
Total images: 18,073
Total valid boxes: 46,209

Train: 12,652
Validation: 3,613
Test: 1,808
```

### Dataset sources

MarineGuard V1 combines:

* FLS
* UATD
* SeaClear

The authoritative class mapping is defined by:

```text
marineguard_classes.yaml
```

`unified_classes.yaml` is retained as a supporting taxonomy file.

Dataset conversion scripts:

```text
convert_fls.py
convert_uatd.py
convert_seaclear.py
create_combined_dataset.py
```

### Dataset distribution

The complete processed V1 dataset is approximately 27.9 GB and is not stored directly in the normal Git repository.

It is reproducible from the documented source datasets and conversion pipeline.

SeaClear's prepared YOLO package is distributed through Git LFS.

The V1 reproduction instructions are documented in:

```text
docs/V1_DATASET_MANIFEST.md
```

### Dataset rules

1. Test data must remain untouched during model development.
2. Dataset splits must be reproducible.
3. Class IDs must never be reordered without creating a new dataset/model version.
4. Dataset versions must be explicitly identified.
5. Large image datasets must not be committed directly into normal Git history.
6. Directly distributed artifacts must use the GitHub-controlled distribution mechanism.
7. Generated datasets must have documented reproduction instructions.

---

## 4. Model Contract

### V1 baseline

```text
Model version: v1
Model: MarineGuard V1
Architecture: YOLOv8n
Task: Object Detection
Classes: 50
Input size: 512 × 512
```

Current V1 evaluation:

```text
Precision: 89.70%
Recall: 71.90%
F1: 79.94%
mAP50: 80.69%
mAP50-95: 55.74%
Test images: 1,808
```

The V1 checkpoint is immutable once the handoff is finalized.

### V1 checkpoint

```text
runs/marineguard_full_512_b16-2/weights/best.pt
```

The checkpoint is distributed through Git LFS.

SHA-256:

```text
18C9E560B9E82BB6EFE3A108584497C4979A9E135BED578DB179341E0778E0D1
```

### Model selection

Downstream code must not hardcode a developer-specific absolute path.

Model selection must be configurable.

Example:

```yaml
model:
  version: v1
  path: runs/marineguard_full_512_b16-2/weights/best.pt
```

A future V2 model must be represented as a separate version.

---

## 5. Detector Input Contract

For the current V1 model:

```text
Task: image object detection
Expected input: image
Input preprocessing resolution: 512 × 512
```

Supported image formats must be determined by the actual inference implementation.

The application must not assume that the current model accepts raw sonar files, video, telemetry, or other formats unless explicitly implemented and documented.

---

## 6. Detector Output Contract

Role 2 must produce detections in the standardized structure defined by:

```text
docs/DETECTION_SCHEMA.json
```

Example:

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

Every detection must contain:

| Field        | Type    | Description                     |
| ------------ | ------- | ------------------------------- |
| `class_id`   | integer | MarineGuard class ID            |
| `class_name` | string  | MarineGuard class name          |
| `confidence` | number  | Detector confidence from 0 to 1 |
| `bbox.x1`    | number  | Left coordinate                 |
| `bbox.y1`    | number  | Top coordinate                  |
| `bbox.x2`    | number  | Right coordinate                |
| `bbox.y2`    | number  | Bottom coordinate               |

The prediction container must contain:

| Field           | Type   | Description                   |
| --------------- | ------ | ----------------------------- |
| `frame_id`      | string | Unique image/frame identifier |
| `model_version` | string | Model used for inference      |
| `detections`    | array  | List of detections            |

---

## 7. Role 2 → Role 3 Contract

Role 2 provides:

```text
frame_id
model_version
class_id
class_name
confidence
bounding box
```

Role 3 consumes these fields to perform:

* confidence calibration
* confidence thresholding
* false-positive reduction
* filtering

Role 3 must not modify the MarineGuard class taxonomy.

The canonical schema is:

```text
docs/DETECTION_SCHEMA.json
```

---

## 8. Role 3 → Role 4 Contract

Role 3 returns the same detection structure with filtering information.

Example:

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
      },
      "filter_status": "accepted"
    }
  ]
}
```

Possible filter states:

```text
accepted
rejected
```

Role 4 uses accepted detections for reporting/geotagging.

Role 3 must preserve:

* `frame_id`
* `model_version`
* `class_id`
* `class_name`
* `confidence`
* `bbox`

---

## 9. Role 4 → Role 5 Contract

Reporting/geotagging output must preserve detection identity.

Example:

```json
{
  "frame_id": "frame_000001",
  "model_version": "v1",
  "detections": [],
  "geolocation": {
    "latitude": 0.0,
    "longitude": 0.0
  },
  "timestamp": null
}
```

Geolocation and timestamp fields must only contain real data when such data is actually available.

The system must not invent GPS coordinates or timestamps.

Role 5 consumes the reporting output for UI/MCP integration.

---

## 10. Class Taxonomy Contract

MarineGuard currently uses exactly 50 classes.

Class IDs are immutable for a model/dataset version.

The authoritative taxonomy is:

```text
marineguard_classes.yaml
```

The V1 class IDs are:

```text
0  bottle
1  can
2  chain
3  drink-carton
4  hook
5  propeller
6  shampoo-bottle
7  standing-bottle
8  tire
9  valve
10 metal-bucket
11 ball
12 cube
13 cylinder
14 circle-cage
15 square-cage
16 human-body
17 plane
18 rov
19 tarp
20 plastic-container
21 cement-tube
22 plant
23 animal
24 sponge
25 glass-bottle
26 metal-wreckage
27 unknown-object
28 plastic-pipe
29 net
30 shell
31 rope
32 plastic-cup
33 brick
34 plastic-bag
35 sanitary-waste
36 clothing
37 ceramic-cup
38 rubber-boot
39 glass-jar
40 rov-cable
41 rov-part
42 wood-branch
43 furniture
44 snack-wrapper
45 plastic-lid
46 cardboard
47 metal-cable
48 fish
49 starfish
```

---

## 11. Model Versioning

Model versions must never silently replace one another.

Required naming:

```text
v1
v2
v3
...
```

Example:

```text
MarineGuard V1
MarineGuard V2
```

The selected production model must be explicitly configured.

---

## 12. Artifact Distribution

Normal Git repository contains:

```text
source code
configuration
documentation
schemas
manifests
taxonomy
conversion scripts
validation scripts
```

Large artifacts may include:

```text
datasets
model checkpoints
large binary files
```

Large artifacts must use a GitHub-controlled distribution mechanism or documented reproduction process.

Each directly distributed artifact must have:

* version
* filename
* size
* checksum
* source/version information
* retrieval instructions

Generated large datasets must additionally have:

* source dataset information
* conversion instructions
* validation rules
* expected output counts

---

## 13. Reproducibility Rule

A new developer must be able to:

```text
clone GitHub repository
        ↓
read handoff documentation
        ↓
obtain directly distributed artifacts
        ↓
reproduce generated datasets when required
        ↓
run documented setup
        ↓
run inference/training/evaluation
```

without requiring:

```text
C:\aaaa\SIH\...
```

or any other developer-specific path.

---

## 14. V1 Freeze Rule

V1 is the current baseline.

Until the V2 comparison is completed:

* V1 metrics must not be overwritten.
* V1 checkpoint must not be replaced by V2.
* V1 dataset identity must remain fixed.
* V1 test split must remain untouched.
* Downstream roles may use V1.
* V2 remains experimental and paused.

---

## 15. V2 Rule

V2 is a separate development line.

When resumed, V2 must produce:

```text
dataset version
model version
evaluation metrics
test-set results
model checksum
handoff documentation
GitHub distribution/reproduction path
```

V2 must not silently modify the V1 handoff.

---

## 16. Definition of Done

The cross-role handoff is complete when:

* [x] V1 model is obtainable through GitHub-controlled distribution
* [x] SeaClear YOLO dataset is obtainable through GitHub-controlled distribution
* [x] V1 processed dataset is reproducible
* [x] Portable dataset configuration exists
* [x] Dataset manifest exists
* [x] Test-set manifest exists
* [x] Model registry exists
* [x] Detection schema exists
* [x] Role 2 → Role 3 interface is defined
* [x] Role 3 → Role 4 interface is defined
* [x] Role 4 → Role 5 interface is defined
* [x] No local Windows paths are required
* [x] V1 remains frozen
* [x] V2 remains separate
