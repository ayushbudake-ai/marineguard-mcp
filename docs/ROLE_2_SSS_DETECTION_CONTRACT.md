\# MarineGuard SSS Detection Contract



\*\*Status:\*\* Implemented and verified

\*\*Scope:\*\* Role 2 — Side-Scan Sonar AI inference integration



\---



\## 1. Purpose



This document defines the detection contract between the dedicated

Side-Scan Sonar (SSS) detector and the existing MarineGuard detection

pipeline.



The SSS detector must produce the existing MarineGuard canonical

`Detection` and `DetectionResult` structures.



No second detection taxonomy is introduced.



\---



\## 2. SSS Detection Data Flow



```text

SSS YOLO class 0

&#x20;       |

&#x20;       v

MarineGuard class 29

&#x20;       |

&#x20;       v

class\_name = "net"

&#x20;       |

&#x20;       v

Detection

&#x20;       |

&#x20;       v

DetectionResult

&#x20;       |

&#x20;       +--------> Fusion

&#x20;       |

&#x20;       +--------> API

&#x20;       |

&#x20;       +--------> MCP

```



\---



\## 3. SSS Model Taxonomy



The current SSS YOLO model contains one native class:



```text

SSS class 0 = net

```



The authoritative MarineGuard taxonomy defines:



```text

MarineGuard class 29 = net

```



Therefore the integration mapping is:



```text

SSS native class 0

&#x20;       |

&#x20;       v

MarineGuard class 29

&#x20;       |

&#x20;       v

"net"

```



The global MarineGuard 50-class taxonomy must not be modified or

reordered.



\---



\## 4. Canonical Detection



Every accepted SSS model detection is converted into the existing

MarineGuard `Detection` structure.



Required fields:



```text

class\_name

class\_id

confidence

bbox

```



Current SSS mapping:



```text

class\_name = "net"

class\_id   = 29

confidence = model confidence

bbox       = \[x1, y1, x2, y2]

```



Additional metadata currently records:



```text

method = "SSS-YOLO"

native\_class\_id = 0

```



\---



\## 5. DetectionResult Compatibility



SSS inference returns the existing MarineGuard `DetectionResult`.



The result contains:



```text

detections

count

image\_width

image\_height

inference\_time\_ms

model\_name

status

```



Downstream components must consume the standard `DetectionResult`

without requiring an SSS-specific result type.



\---



\## 6. frame\_id and model\_version



The conceptual integration contract may require:



```text

frame\_id

model\_version

```



The current canonical MarineGuard `Detection` schema does not define

these as dedicated top-level fields.



A second incompatible detection schema must not be introduced.



If these values are required by an integration consumer, they may be

carried through the existing `metadata` field until the canonical

schema is formally extended.



\---



\## 7. Confidence



The SSS detector uses the existing model-loader confidence threshold.



Only detections accepted by the configured confidence threshold are

converted into canonical MarineGuard detections.



The canonical confidence value remains within:



```text

0.0 <= confidence <= 1.0

```



\---



\## 8. Bounding Box



The SSS model produces bounding boxes in:



```text

\[x1, y1, x2, y2]

```



The integration converts the coordinates into numeric values and stores

them in the canonical `Detection.bbox`.



Invalid or missing bounding boxes are rejected instead of producing an

invalid canonical detection.



\---



\## 9. Unsupported SSS Classes



If the SSS model produces a native class that is not present in the

SSS class mapping, that detection is ignored.



Current mapping:



```text

SSS class 0 -> MarineGuard class 29

```



This prevents an unknown SSS class from being accidentally mapped to an

incorrect MarineGuard class.



\---



\## 10. Detector Replacement



The SSS model is supplied through the existing:



```text

MarineDebrisModel

```



interface.



The side-scan detector does not depend on a specific checkpoint

filename.



Therefore the currently used engineering/test checkpoint can later be

replaced by Person A's selected final SSS checkpoint without changing

the canonical detection contract.



\---



\## 11. CA-CFAR Compatibility



CA-CFAR remains available as the side-scan anomaly/candidate detection

path.



CA-CFAR detections use:



```text

class\_id   = 27

class\_name = "unknown-object"

method     = "CA-CFAR"

```



The dedicated SSS YOLO path uses:



```text

class\_id   = 29

class\_name = "net"

method     = "SSS-YOLO"

```



These two mappings must not be conflated.



CA-CFAR must not be changed to report SSS YOLO class `net` unless a

separate validated classification stage is explicitly introduced.



\---



\## 12. Error Contract



SSS model loading or inference failures must produce an explicit

`DetectionResult` with an error status.



Errors must not silently become successful detections.



The error status must preserve enough information for the API and MCP

layers to report the failure.



\---



\## 13. Verified SSS Integration



The SSS integration was verified using the current engineering/test

ONNX checkpoint:



```text

runs/detect/runs/detect/marineguard\_sss\_yolov8n\_exp2\_augmented/weights/best.onnx

```



Test image:



```text

data/processed/marineguard\_sss/images/test/synth\_ghost\_net\_00001.png

```



Measured result:



```text

Status: ok

Count: 1



Class ID: 29

Class name: net

Confidence: 0.937634



BBox:

\[113.59512329101562,

&#x20;210.61488342285156,

&#x20;226.19735717773438,

&#x20;319.279296875]



Native SSS class ID: 0

Method: SSS-YOLO

```



The result was successfully serialized using:



```text

DetectionResult.to\_api\_dict()

```



This confirms the core engineering path:



```text

SSS image

&#x20;   |

&#x20;   v

SSS ONNX model

&#x20;   |

&#x20;   v

native class 0

&#x20;   |

&#x20;   v

MarineGuard class 29

&#x20;   |

&#x20;   v

Detection

&#x20;   |

&#x20;   v

DetectionResult

&#x20;   |

&#x20;   v

API-compatible output

```



\---



\## 14. Current ONNX Runtime Limitation



The installed environment currently exposes:



```text

TensorrtExecutionProvider

CUDAExecutionProvider

CPUExecutionProvider

```



However, the available CUDA execution provider cannot currently be

used because the required CUDA 13 / cuDNN 9 runtime dependencies are

not available in the environment.



Therefore the verified ONNX integration currently runs using:



```text

CPUExecutionProvider

```



This is an environment limitation and does not invalidate the SSS

detection contract.



GPU ONNX runtime verification remains pending until the required runtime

environment is available.



\---



\## 15. Contract Status



\### Implemented and verified



\* \[x] SSS native class mapping

\* \[x] MarineGuard class mapping

\* \[x] No second taxonomy

\* \[x] Canonical `Detection`

\* \[x] Canonical `DetectionResult`

\* \[x] Confidence handling

\* \[x] Bounding box conversion

\* \[x] Unsupported-class protection

\* \[x] Error status path

\* \[x] Replaceable model interface

\* \[x] API serialization

\* \[x] Side-scan SSS YOLO inference path



\### Pending



\* \[ ] Final SSS checkpoint selection by Person A

\* \[ ] Final selected-checkpoint verification

\* \[ ] Automated SSS integration test suite

\* \[ ] Full API regression

\* \[ ] MCP regression

\* \[ ] End-to-end downstream integration

\* \[ ] GPU ONNX runtime verification



\---



\## 16. Engineering Rules



The following rules apply to the SSS integration:



1\. Do not modify the frozen MarineGuard V1 taxonomy.

2\. Do not reorder existing MarineGuard class IDs.

3\. Do not introduce a second detection taxonomy.

4\. SSS native class `0` must map to MarineGuard class `29`.

5\. CA-CFAR class `27` (`unknown-object`) must remain separate from SSS

&#x20;  YOLO class `29` (`net`).

6\. The SSS detector must return the existing MarineGuard

&#x20;  `DetectionResult`.

7\. The SSS checkpoint must remain replaceable.

8\. Final SSS performance must not be claimed from engineering

&#x20;  verification alone.

9\. Person A's final model-selection result is authoritative for the

&#x20;  final SSS checkpoint.

10\. The frozen V1 checkpoint and V1 test split must remain untouched.



\---



\## 17. Final Integration Target



The final engineering target is:



```text

SSS image/frame

&#x20;      |

&#x20;      v

SSS preprocessing

&#x20;      |

&#x20;      v

Selected SSS YOLO model

&#x20;      |

&#x20;      v

SSS native detections

&#x20;      |

&#x20;      v

Class mapping

0 -> 29

&#x20;      |

&#x20;      v

MarineGuard Detection

&#x20;      |

&#x20;      v

DetectionResult

&#x20;      |

&#x20;      +--------> Fusion

&#x20;      |

&#x20;      +--------> API

&#x20;      |

&#x20;      +--------> MCP

```



The currently verified implementation establishes the detector-to-

`DetectionResult` portion of this pipeline.



Final checkpoint integration and complete downstream verification remain

pending.
