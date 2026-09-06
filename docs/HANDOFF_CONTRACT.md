\# MarineGuard — Cross-Role Handoff Contract



\*\*Project:\*\* MarineGuard MCP

\*\*Current baseline:\*\* V1

\*\*V2 status:\*\* PAUSED

\*\*Owner:\*\* Role 1 — Data \& Preprocessing



\---



\# 1. Purpose



This document defines the machine-readable contracts between MarineGuard roles.



The objective is to ensure that every team member working on a different device can obtain the required artifacts and integrate their work without depending on another developer's local filesystem.



GitHub is the authoritative source for:



\* source code

\* configuration

\* documentation

\* schemas

\* dataset manifests

\* model metadata

\* artifact distribution instructions



No role may depend on a developer-specific Windows path.



\---



\# 2. Role Pipeline



```text

Role 1

Data + Model

&#x20;   ↓

Role 2

Detection

&#x20;   ↓

Role 3

Confidence Filtering

&#x20;   ↓

Role 4

Geotagging + Reporting

&#x20;   ↓

Role 5

UI + Integration

```



Each role must consume the documented interface of the previous role.



\---



\# 3. Dataset Contract



\## Dataset identity



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



\## Dataset sources



MarineGuard V1 combines:



\* FLS

\* UATD

\* SeaClear



The exact class mapping is defined by:



```text

marineguard\_classes.yaml

unified\_classes.yaml

```



Dataset conversion scripts:



```text

convert\_fls.py

convert\_uatd.py

convert\_seaclear.py

create\_combined\_dataset.py

```



\## Dataset rules



1\. Test data must remain untouched during model development.

2\. Dataset splits must be reproducible.

3\. Class IDs must never be reordered without creating a new dataset/model version.

4\. Dataset versions must be explicitly identified.

5\. Large image datasets must not be committed directly into normal Git history.

6\. Dataset distribution must be obtainable through the GitHub-controlled handoff process.



\---



\# 4. Model Contract



\## V1 baseline



```text

Model version: MarineGuard V1

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



The V1 checkpoint must be treated as immutable once the handoff is finalized.



\## Model selection



Downstream code must NOT hardcode:



```text

best.pt

```



Instead, model selection must be configurable.



Example:



```yaml

model:

&#x20; version: v1

&#x20; path: artifacts/models/v1/best.pt

```



A future V2 model must be represented as a separate version.



\---



\# 5. Detector Input Contract



The detector must explicitly document the supported input.



For the current V1 model:



```text

Task: image object detection

Expected input: image

Supported image formats: to be confirmed by the inference implementation

Input resolution: 512 × 512 preprocessing

```



The application must not assume that the current model accepts raw sonar files, video, telemetry, or other formats unless explicitly implemented and documented.



\---



\# 6. Detector Output Contract



Role 2 must produce detections in a standardized structure.



Example:



```json

{

&#x20; "frame\_id": "frame\_000001",

&#x20; "model\_version": "v1",

&#x20; "detections": \[

&#x20;   {

&#x20;     "class\_id": 0,

&#x20;     "class\_name": "bottle",

&#x20;     "confidence": 0.91,

&#x20;     "bbox": {

&#x20;       "x1": 120,

&#x20;       "y1": 80,

&#x20;       "x2": 310,

&#x20;       "y2": 350

&#x20;     }

&#x20;   }

&#x20; ]

}

```



\## Required detection fields



Every detection must contain:



| Field        | Type    | Description                     |

| ------------ | ------- | ------------------------------- |

| `class\_id`   | integer | MarineGuard class ID            |

| `class\_name` | string  | MarineGuard class name          |

| `confidence` | float   | Detector confidence from 0 to 1 |

| `bbox.x1`    | number  | Left coordinate                 |

| `bbox.y1`    | number  | Top coordinate                  |

| `bbox.x2`    | number  | Right coordinate                |

| `bbox.y2`    | number  | Bottom coordinate               |



The prediction container must also contain:



| Field           | Type   | Description                   |

| --------------- | ------ | ----------------------------- |

| `frame\_id`      | string | Unique image/frame identifier |

| `model\_version` | string | Model used for inference      |

| `detections`    | array  | List of detections            |



\---



\# 7. Role 2 → Role 3 Contract



Role 2 provides:



```text

frame\_id

model\_version

class\_id

class\_name

confidence

bounding box

```



Role 3 consumes these fields to perform:



\* confidence calibration

\* confidence thresholding

\* false-positive reduction

\* filtering



Role 3 must not modify the class taxonomy.



\---



\# 8. Role 3 → Role 4 Contract



Role 3 returns the same detection structure with filtering information.



Example:



```json

{

&#x20; "frame\_id": "frame\_000001",

&#x20; "model\_version": "v1",

&#x20; "detections": \[

&#x20;   {

&#x20;     "class\_id": 0,

&#x20;     "class\_name": "bottle",

&#x20;     "confidence": 0.91,

&#x20;     "bbox": {

&#x20;       "x1": 120,

&#x20;       "y1": 80,

&#x20;       "x2": 310,

&#x20;       "y2": 350

&#x20;     },

&#x20;     "filter\_status": "accepted"

&#x20;   }

&#x20; ]

}

```



Possible filter states:



```text

accepted

rejected

```



Role 4 uses accepted detections for reporting/geotagging.



\---



\# 9. Role 4 → Role 5 Contract



Reporting/geotagging output must preserve detection identity.



Example:



```json

{

&#x20; "frame\_id": "frame\_000001",

&#x20; "model\_version": "v1",

&#x20; "detections": \[],

&#x20; "geolocation": {

&#x20;   "latitude": 0.0,

&#x20;   "longitude": 0.0

&#x20; },

&#x20; "timestamp": null

}

```



Geolocation and timestamp fields must only contain real data when such data is actually available.



The system must not invent GPS coordinates or timestamps.



\---



\# 10. Class Taxonomy Contract



MarineGuard currently uses exactly 50 classes.



Class IDs are immutable for a model/dataset version.



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



The authoritative taxonomy files are:



```text

marineguard\_classes.yaml

unified\_classes.yaml

```



\---



\# 11. Model Versioning



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



\---



\# 12. Artifact Distribution



Normal Git repository:



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



Large artifacts:



```text

datasets

model checkpoints

large binary files

```



Large artifacts must use a GitHub-controlled distribution mechanism.



Each distributed artifact must have:



\* version

\* filename

\* size

\* checksum

\* source/version information

\* retrieval instructions



\---



\# 13. Reproducibility Rule



A new developer must be able to:



```text

clone GitHub repository

&#x20;       ↓

read handoff documentation

&#x20;       ↓

obtain required artifacts

&#x20;       ↓

run documented setup

&#x20;       ↓

run inference/training/evaluation

```



without requiring:



```text

C:\\aaaa\\SIH\\...

```



or any other developer-specific path.



\---



\# 14. V1 Freeze Rule



V1 is the current baseline.



Until the V2 comparison is completed:



\* V1 metrics must not be overwritten.

\* V1 checkpoint must not be replaced by V2.

\* V1 dataset identity must remain fixed.

\* Downstream roles may use V1.

\* V2 remains experimental and paused.



\---



\# 15. V2 Rule



V2 is a separate development line.



When resumed, V2 must produce:



```text

dataset version

model version

evaluation metrics

test-set results

model checksum

handoff documentation

```



V2 must not silently modify the V1 handoff.



\---



\# 16. Definition of Done



The cross-role handoff is complete when:



\* \[ ] Dataset can be obtained through GitHub-controlled distribution

\* \[ ] SeaClear YOLO dataset is obtainable

\* \[ ] V1 model is obtainable

\* \[ ] Portable dataset configuration exists

\* \[ ] Dataset manifest exists

\* \[ ] Test-set manifest exists

\* \[ ] Model registry exists

\* \[ ] Detection schema exists

\* \[ ] Role 2 → Role 3 interface is defined

\* \[ ] Role 3 → Role 4 interface is defined

\* \[ ] Role 4 → Role 5 interface is defined

\* \[ ] No local Windows paths are required

\* \[ ] V1 remains frozen

\* \[ ] V2 remains separate



