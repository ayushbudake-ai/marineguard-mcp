# MarineGuard V1 Dataset Manifest:

**Dataset version:** V1
**Status:** FROZEN BASELINE
**V2 status:** PAUSED

---

## 1. Dataset Summary

| Property             |  Value |
| -------------------- | -----: |
| Dataset version      |     V1 |
| Classes              |     50 |
| Total images         | 18,073 |
| Total labels         | 18,073 |
| Valid bounding boxes | 46,209 |
| Train images         | 12,652 |
| Validation images    |  3,613 |
| Test images          |  1,808 |

---

## 2. Source Datasets

MarineGuard V1 is constructed from:

1. FLS
2. UATD
3. SeaClear

The source datasets are converted into the MarineGuard 50-class taxonomy before combination.

---

## 3. Source Dataset Inventory

### FLS

MarineGuard V1 uses the **Water Tank release (`watertank-v1.0`)** of the Marine Debris FLS Dataset.

Expected raw layout:

```text
data/raw/fls/
└── marine-debris-watertank-release-1.0/
    └── marine-debris-watertank-release/
        └── fls-images/
            ├── annotations.json
            └── image files
```

Source classes:

```text
bottle
can
chain
drink-carton
hook
propeller
shampoo-bottle
standing-bottle
tire
valve
```

V1 contribution:

```text
Train: 1,307
Val:     373
Test:    188
Total: 1,868
```

Conversion script:

```text
convert_fls.py
```

Local source audit:

```text
PNG images: 4,232
JSON files: 1
PT file: 1
XZ archive: 1
```

---

### UATD

MarineGuard V1 uses the official **UATD Training** package.

Source package:

```text
7,600 BMP images
7,600 XML annotations
```

Expected raw layout:

```text
data/raw/uatd/
└── UATD_Training/
    ├── annotations/
    │   └── *.xml
    └── image files
```

Original UATD classes:

```text
ball
circle cage
cube
cylinder
human body
metal bucket
plane
rov
square cage
tyre
```

The source class `tyre` is mapped to the MarineGuard class `tire`.

After annotation validation:

```text
Train: 5,318
Val:   1,518
Test:    759
Total: 7,595
```

Eleven invalid annotations were excluded, resulting in 7,595 usable labeled images and 12,296 valid bounding boxes.

Conversion script:

```text
convert_uatd.py
```

Local source audit:

```text
BMP images: 15,195
TXT files: 15,195
XML files: 7,600
YAML files: 2
ZIP archives: 2
```

---

### SeaClear

MarineGuard V1 uses the SeaClear YOLO package.

```text
Images: 8,610
Labels: 8,610
YAML: 1
Approximate size: 1.75 GB
```

The SeaClear V1 package is distributed through Git LFS in this repository.

Local source audit:

```text
JPG images: 17,220
TXT files: 17,221
JSON files: 1
YAML files: 1
RAR archive: 1
ZIP archive: 1
```

---

## 4. MarineGuard Processing

The source datasets are transformed using:

```text
convert_fls.py
convert_uatd.py
convert_seaclear.py
```

The converted datasets are combined using:

```text
create_combined_dataset.py
```

Validation is performed using:

```text
validate_marineguard.py
```

The authoritative taxonomy is:

```text
marineguard_classes.yaml
unified_classes.yaml
```

---

## 5. V1 Dataset Structure

Expected processed structure:

```text
data/processed/marineguard/

├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

The processed dataset is a generated artifact and should not be committed to normal Git history.

---

## 6. Portable Dataset Configuration

The V1 dataset configuration must be portable across all team members' machines.

The repository `data.yaml` uses:

```yaml
path: .
train: images/train
val: images/val
test: images/test
```

It must not contain a machine-specific absolute path such as:

```yaml
path: C:/aaaa/SIH/marineguard-mcp/data/processed/marineguard
```

This allows the same repository to be cloned to different Windows or Linux machines without modifying the dataset configuration.

The authoritative 50-class mapping is maintained in:

```text
marineguard_classes.yaml
```

---

## 7. Dataset Split

The frozen V1 split is:

```text
Train: 12,652
Val:    3,613
Test:   1,808
Total: 18,073
```

The test split must remain untouched during model development.

---

## 8. Test Set Rule

The V1 test set is the held-out evaluation set.

Any future V2 comparison must use the same held-out test methodology.

V2 must not replace or modify the V1 test set.

---

## 9. Class Taxonomy

MarineGuard uses exactly 50 classes.

Class IDs are defined by:

```text
marineguard_classes.yaml
```

and:

```text
unified_classes.yaml
```

Class IDs must not be reordered for V1.

The V1 taxonomy is:

```text
0 bottle
1 can
2 chain
3 drink-carton
4 hook
5 propeller
6 shampoo-bottle
7 standing-bottle
8 tire
9 valve
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

## 10. Reproduction

A developer reproducing V1 should:

```text
1. Obtain the required source datasets.
2. Place them under data/raw/.
3. Run the FLS conversion.
4. Run the UATD conversion.
5. Run the SeaClear conversion.
6. Run the combined dataset creation.
7. Run dataset validation.
8. Verify the V1 counts.
9. Use the portable data.yaml for model evaluation/training.
```

The exact commands must be documented and verified before declaring the V1 reproduction process complete.

---

## 11. Expected Validation

A successful V1 reproduction must produce:

```text
Images: 18,073
Labels: 18,073
Valid boxes: 46,209

Train: 12,652
Val:    3,613
Test:   1,808
```

If these values differ, the reproduction must be treated as a different dataset build until the cause is identified.

---

## 12. Dataset Version Rule

Any change to:

* source dataset
* source dataset version
* class mapping
* preprocessing
* split
* filtering
* annotation conversion

requires a new dataset version.

Example:

```text
V1
V2
V3
```

V1 must remain immutable.

---

## 13. Large Artifact Rule

The generated approximately 27.9 GB V1 processed dataset must not be committed directly to normal Git history.

The repository contains the instructions and metadata required to reproduce it.

Large source datasets may be distributed separately through a GitHub-controlled artifact mechanism.

---

## 14. Source Dataset Acquisition

### FLS

Official source:

**Marine Debris FLS Dataset — Water Tank release (`watertank-v1.0`)**

The FLS source must be obtained from its public source distribution and placed under:

```text
data/raw/fls/
```

before running:

```text
convert_fls.py
```

### UATD

Official source:

**UATD — Underwater Acoustic Target Detection Dataset**

DOI:

```text
10.6084/m9.figshare.21331143.v3
```

The UATD Training package must be placed under:

```text
data/raw/uatd/UATD_Training/
```

before running:

```text
convert_uatd.py
```

### SeaClear

The SeaClear YOLO package is distributed with this repository through Git LFS.

After cloning the repository, install Git LFS and retrieve the artifact before using the dataset.

---

## 15. V1 Freeze

This manifest describes the frozen V1 baseline.

V2 is currently paused and must not modify this manifest until V2 becomes the selected baseline.

The V1 dataset counts, split definition, class IDs, and test-set methodology are frozen.

---

## Status

Current status:

* [x] Source datasets identified
* [x] Conversion scripts identified
* [x] Taxonomy identified
* [x] V1 image count recorded
* [x] V1 label count recorded
* [x] V1 split recorded
* [x] Test-set size recorded
* [x] Portable `data.yaml` format defined
* [x] V1 SeaClear artifact distributed through Git LFS
* [ ] Exact file-level manifest/checksums
* [ ] Reproduction commands verified end-to-end
* [ ] Portable `data.yaml` verified on a clean machine
* [ ] V1 artifact distribution finalized
