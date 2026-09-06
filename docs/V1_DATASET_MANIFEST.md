\# MarineGuard V1 Dataset Manifest



\*\*Dataset version:\*\* V1

\*\*Status:\*\* FROZEN BASELINE

\*\*V2 status:\*\* PAUSED



\---



\## 1. Dataset Summary



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



\---



\## 2. Source Datasets



MarineGuard V1 is constructed from:



1\. FLS

2\. UATD

3\. SeaClear



The source datasets are converted into the MarineGuard 50-class taxonomy before combination.



\---



\## 3. Source Dataset Inventory



\### FLS



Local source audit:



```text

PNG images: 4,232

JSON files: 1

PT file: 1

XZ archive: 1

```



Conversion script:



```text

convert\_fls.py

```



\---



\### UATD



Local source audit:



```text

BMP images: 15,195

TXT files: 15,195

XML files: 7,600

YAML files: 2

ZIP archives: 2

```



Conversion script:



```text

convert\_uatd.py

```



\---



\### SeaClear



Local source audit:



```text

JPG images: 17,220

TXT files: 17,221

JSON files: 1

YAML files: 1

RAR archive: 1

ZIP archive: 1

```



SeaClear YOLO package:



```text

Images: 8,610

Labels: 8,610

YAML: 1

Approximate size: 1.75 GB

```



Conversion script:



```text

convert\_seaclear.py

```



\---



\# 4. MarineGuard Processing



The source datasets are transformed using:



```text

convert\_fls.py

convert\_uatd.py

convert\_seaclear.py

```



The converted datasets are combined using:



```text

create\_combined\_dataset.py

```



Validation is performed using:



```text

validate\_marineguard.py

```



The authoritative taxonomy is:



```text

marineguard\_classes.yaml

unified\_classes.yaml

```



\---



\# 5. V1 Dataset Structure



Expected processed structure:



```text

data/processed/marineguard/



├── data.yaml

├── images/

│   ├── train/

│   ├── val/

│   └── test/

└── labels/

&#x20;   ├── train/

&#x20;   ├── val/

&#x20;   └── test/

```



The processed dataset is a generated artifact and should not be committed to normal Git history.



\---



\# 6. Dataset Split



The frozen V1 split is:



```text

Train: 12,652

Val:    3,613

Test:   1,808

Total: 18,073

```



The test split must remain untouched during model development.



\---



\# 7. Test Set Rule



The V1 test set is the held-out evaluation set.



Any future V2 comparison must use the same held-out test methodology.



V2 must not replace or modify the V1 test set.



\---



\# 8. Class Taxonomy



MarineGuard uses exactly 50 classes.



Class IDs are defined by:



```text

marineguard\_classes.yaml

```



and:



```text

unified\_classes.yaml

```



Class IDs must not be reordered for V1.



\---



\# 9. Reproduction



A developer reproducing V1 should:



```text

1\. Obtain the required source datasets.

2\. Place them under data/raw/.

3\. Run the FLS conversion.

4\. Run the UATD conversion.

5\. Run the SeaClear conversion.

6\. Run the combined dataset creation.

7\. Run dataset validation.

8\. Verify the V1 counts.

9\. Use the resulting data.yaml for model evaluation/training.

```



The exact commands must be documented and verified before declaring the V1 reproduction process complete.



\---



\# 10. Expected Validation



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



\---



\# 11. Dataset Version Rule



Any change to:



\* source dataset

\* source dataset version

\* class mapping

\* preprocessing

\* split

\* filtering

\* annotation conversion



requires a new dataset version.



Example:



```text

V1

V2

V3

```



V1 must remain immutable.



\---



\# 12. Large Artifact Rule



The generated 27.9 GB V1 processed dataset must not be committed directly to normal Git history.



The repository contains the instructions and metadata required to reproduce it.



Large source datasets may be distributed separately through a GitHub-controlled artifact mechanism.



\---



\# 13. V1 Freeze



This manifest describes the frozen V1 baseline.



V2 is currently paused and must not modify this manifest until V2 becomes the selected baseline.



\---



\## Status



Current status:



\* \[x] Source datasets identified

\* \[x] Conversion scripts identified

\* \[x] Taxonomy identified

\* \[x] V1 image count recorded

\* \[x] V1 label count recorded

\* \[x] V1 split recorded

\* \[x] Test-set size recorded

\* \[ ] Exact file-level manifest/checksums

\* \[ ] Reproduction commands verified end-to-end

\* \[ ] Portable `data.yaml` finalized

\* \[ ] V1 artifact distribution finalized



