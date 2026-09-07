# MarineGuard — Role Dependency Matrix

## Source of Truth

GitHub repository:

`https://github.com/ayushbudake-ai/marineguard-mcp`

GitHub is the authoritative handoff source. No downstream role should depend on another developer's local filesystem.

---

## Role Dependency Matrix

| From   | To     | Required artifact/interface  | GitHub location                                   | Status       |
| ------ | ------ | ---------------------------- | ------------------------------------------------- | ------------ |
| Role 1 | Role 2 | V1 YOLO detector checkpoint  | `runs/marineguard_full_512_b16-2/weights/best.pt` | READY        |
| Role 1 | Role 2 | V1 processed dataset         | `data/processed/marineguard/`                     | REPRODUCIBLE |
| Role 1 | Role 2 | Dataset YAML                 | `data/processed/marineguard/data.yaml`            | REPRODUCIBLE |
| Role 1 | Role 2 | 50-class taxonomy            | `marineguard_classes.yaml`                        | READY        |
| Role 1 | Role 2 | V1 metrics                   | `ROLE1_FINAL_RESULTS.md`                          | READY        |
| Role 1 | Role 2 | Handoff instructions         | `ROLE1_TO_ROLE2_HANDOFF.md`                       | READY        |
| Role 1 | Role 2 | Artifact registry            | `docs/MODEL_REGISTRY.md`                          | READY        |
| Role 2 | Role 3 | Detection JSON contract      | `docs/DETECTION_SCHEMA.json`                      | READY        |
| Role 2 | Role 3 | class_id / class_name        | `marineguard_classes.yaml`                        | READY        |
| Role 2 | Role 3 | confidence                   | `docs/DETECTION_SCHEMA.json`                      | READY        |
| Role 2 | Role 3 | bbox                         | `docs/DETECTION_SCHEMA.json`                      | READY        |
| Role 2 | Role 3 | frame_id                     | `docs/DETECTION_SCHEMA.json`                      | READY        |
| Role 2 | Role 3 | model_version                | `docs/DETECTION_SCHEMA.json`                      | READY        |
| Role 3 | Role 4 | filter_status                | `docs/HANDOFF_CONTRACT.md`                        | READY        |
| Role 3 | Role 4 | preserved detection identity | `docs/HANDOFF_CONTRACT.md`                        | READY        |
| Role 4 | Role 5 | geolocation                  | `docs/HANDOFF_CONTRACT.md`                        | READY        |
| Role 4 | Role 5 | timestamp                    | `docs/HANDOFF_CONTRACT.md`                        | READY        |
| Role 4 | Role 5 | detection identity           | `docs/HANDOFF_CONTRACT.md`                        | READY        |

---

## Role 1 -> Role 2 Dependency Details

### V1 Model

The V1 detector checkpoint is directly distributed through Git LFS:

```text
runs/marineguard_full_512_b16-2/weights/best.pt
```

Role 2 can obtain it by cloning the repository and running:

```powershell
git lfs install
git lfs pull
```

The model is therefore a **directly available GitHub artifact**.

### V1 Processed Dataset

The complete processed V1 dataset contains:

```text
18,073 images
18,073 labels
46,209 valid bounding boxes

Train: 12,652
Val:    3,613
Test:   1,808
```

The processed dataset is approximately 27.9 GB and is **not stored directly in the normal Git repository**.

It must be reproduced from the documented source datasets and conversion pipeline.

The authoritative reproduction instructions are:

```text
docs/V1_DATASET_MANIFEST.md
```

Therefore the dataset status is:

```text
REPRODUCIBLE
```

rather than:

```text
READY
```

This distinction prevents downstream roles from incorrectly assuming that the 18,073-image processed dataset can be downloaded directly from GitHub.

### Dataset YAML

The V1 `data.yaml` belongs to the generated processed dataset:

```text
data/processed/marineguard/data.yaml
```

The repository defines the required portable format and uses:

```yaml
path: .
train: images/train
val: images/val
test: images/test
```

The generated dataset configuration is therefore reproducible together with the processed dataset.

---

## Role 1 -> downstream dependency rule

Roles 2-5 must be able to obtain their required Role-1 interfaces from GitHub without requesting files from Role 1's local computer.

For generated large artifacts that are intentionally not stored in GitHub, the repository must provide sufficient source information, conversion scripts, validation rules, and reproduction instructions to recreate the artifact.

No downstream role should depend on:

* `C:\aaaa\...`
* another developer's local absolute paths
* uncommitted files
* undocumented local datasets
* undocumented local model checkpoints

---

## V1 baseline

V1 remains the official baseline until a controlled V2 comparison replaces it.

The V1 model is frozen.

The V1 test split is frozen and must remain untouched during model development.

---

## V2

V2 is experimental and must not replace V1 until its:

* evaluation
* checksum
* manifest
* dataset definition
* model registry entry
* handoff documentation
* GitHub distribution/reproduction path

are complete.

V2 must not silently overwrite or replace V1 artifacts.

---

## Status Definitions

### READY

The artifact/interface is directly available through the GitHub repository or Git LFS and can be obtained by a downstream role without relying on Role 1's local computer.

### REPRODUCIBLE

The artifact is intentionally not directly stored in GitHub because of size or generation constraints, but the repository contains the required information and scripts to recreate it.

### BLOCKED

A required dependency cannot currently be obtained or reproduced from the repository.

---

## Current V1 Dependency Status

| Dependency                 | Status       |
| -------------------------- | ------------ |
| V1 model                   | READY        |
| V1 taxonomy                | READY        |
| V1 metrics                 | READY        |
| V1 detection schema        | READY        |
| V1 Role 1 -> Role 2 handoff | READY        |
| V1 processed dataset       | REPRODUCIBLE |
| V1 dataset YAML            | REPRODUCIBLE |
| Role 2 -> Role 3 contract   | READY        |
| Role 3 -> Role 4 contract   | READY        |
| Role 4 -> Role 5 contract   | READY        |
