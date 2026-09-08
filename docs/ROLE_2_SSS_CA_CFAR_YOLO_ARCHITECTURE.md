\# MarineGuard SSS CA-CFAR + YOLO Architecture



\*\*Status:\*\* Engineering architecture documented

\*\*Scope:\*\* Role 2 — Side-Scan Sonar detection and inference integration



\---



\## 1. Purpose



This document defines the current architecture for Side-Scan Sonar (SSS)

detection in MarineGuard.



The purpose is to clearly separate:



\* the existing CA-CFAR anomaly/candidate detector

\* the dedicated SSS YOLO detector

\* the canonical MarineGuard detection contract

\* downstream Fusion, API, and MCP components



The architecture is based on the currently implemented code and

verified integration behavior.



\---



\## 2. Current Implemented Architecture



The current SSS detector supports two distinct processing paths.



\### Path A — CA-CFAR



```text

Raw SSS / waterfall matrix

&#x20;       |

&#x20;       v

Input validation

&#x20;       |

&#x20;       v

2D CA-CFAR

&#x20;       |

&#x20;       v

Acoustic anomaly candidates

&#x20;       |

&#x20;       v

MarineGuard Detection

&#x20;       |

&#x20;       +--> class\_id = 27

&#x20;       +--> class\_name = "unknown-object"

&#x20;       +--> method = "CA-CFAR"

&#x20;       |

&#x20;       v

DetectionResult

```



\### Path B — Dedicated SSS YOLO



```text

SSS image / waterfall matrix

&#x20;       |

&#x20;       v

Input validation

&#x20;       |

&#x20;       v

SSS YOLO

&#x20;       |

&#x20;       v

Native SSS detections

&#x20;       |

&#x20;       v

Class mapping

&#x20;       |

&#x20;       +--> SSS class 0

&#x20;       |

&#x20;       v

MarineGuard class 29

&#x20;       |

&#x20;       +--> class\_name = "net"

&#x20;       +--> method = "SSS-YOLO"

&#x20;       |

&#x20;       v

DetectionResult

```



Both paths produce the same canonical `DetectionResult`.



\---



\## 3. Why CA-CFAR and YOLO Are Currently Separate



CA-CFAR and YOLO perform different functions.



CA-CFAR is a signal-processing/anomaly-detection method. It identifies

local acoustic highlights or statistically unusual regions.



The dedicated SSS YOLO model is a learned object detector trained to

recognize the SSS target class represented by the current model.



The current implementation does not have sufficient validated evidence

to claim that CA-CFAR should always be placed before YOLO.



Therefore the two processing paths remain explicitly selectable rather

than being blindly chained.



\---



\## 4. Architecture Options Considered



\### Option A — Raw SSS -> CA-CFAR -> YOLO



```text

Raw SSS

&#x20;  |

&#x20;  v

CA-CFAR

&#x20;  |

&#x20;  v

Candidate regions

&#x20;  |

&#x20;  v

YOLO

&#x20;  |

&#x20;  v

Final detections

```



Potential advantages:



\* CA-CFAR may reduce the search region.

\* Signal-processing logic can provide candidate localization.

\* Potentially useful for high-noise or sparse-target scenarios.



Potential risks:



\* A true target missed by CA-CFAR may never reach YOLO.

\* CA-CFAR parameters can affect recall.

\* Additional processing increases complexity and latency.

\* Candidate cropping/resizing can change YOLO input characteristics.

\* No current measured experiment proves that this cascade improves

&#x20; SSS detection quality.



\*\*Status:\*\* Not selected as the default architecture.



\---



\### Option B — Raw SSS -> YOLO



```text

Raw SSS

&#x20;  |

&#x20;  v

SSS preprocessing

&#x20;  |

&#x20;  v

Dedicated SSS YOLO

&#x20;  |

&#x20;  v

DetectionResult

```



Advantages:



\* Simple inference path.

\* Direct use of the trained SSS detector.

\* No CA-CFAR-dependent candidate filtering before YOLO.

\* Lower architectural coupling.

\* Easier model replacement.

\* Direct compatibility with the existing detector interface.



Risks:



\* YOLO must process the complete SSS input.

\* CA-CFAR signal-processing information is not used by the YOLO path.

\* Performance depends on the quality and distribution of the SSS model

&#x20; training data.



\*\*Status:\*\* Recommended current SSS AI inference path.



\---



\### Option C — CA-CFAR and YOLO as Separate Complementary Detectors



```text

&#x20;                   +--> CA-CFAR

&#x20;                   |      |

Raw SSS ------------+      v

&#x20;                   |  unknown-object

&#x20;                   |

&#x20;                   +--> SSS YOLO

&#x20;                          |

&#x20;                          v

&#x20;                          net

```



The outputs can subsequently be consumed by downstream components.



Advantages:



\* Preserves the existing CA-CFAR functionality.

\* Allows the dedicated SSS model to operate independently.

\* Avoids making CA-CFAR a mandatory recall gate for YOLO.

\* Keeps both signal-processing and learned detection available.

\* Makes future controlled comparison possible.



Risks:



\* Running both independently can increase computation.

\* Duplicate detections may require a validated fusion strategy.

\* There is currently insufficient co-registered ground truth to claim

&#x20; that combining both outputs improves final detection quality.



\*\*Status:\*\* Supported architecture for future experimentation.



\---



\## 5. Selected Engineering Architecture



The current recommended architecture is:



```text

SSS input

&#x20;  |

&#x20;  v

SSS preprocessing

&#x20;  |

&#x20;  v

Dedicated SSS YOLO

&#x20;  |

&#x20;  v

Class mapping

SSS class 0 -> MarineGuard class 29

&#x20;  |

&#x20;  v

Detection

&#x20;  |

&#x20;  v

DetectionResult

&#x20;  |

&#x20;  +--> Fusion

&#x20;  +--> API

&#x20;  +--> MCP

```



CA-CFAR remains available as a separate side-scan anomaly/candidate

processing path.



It is not currently mandatory that every YOLO detection pass through

CA-CFAR first.



\---



\## 6. Detection Class Separation



The two implemented paths use different semantic outputs.



\### CA-CFAR



```text

class\_id   = 27

class\_name = "unknown-object"

method     = "CA-CFAR"

```



\### SSS YOLO



```text

native class\_id = 0

MarineGuard class\_id = 29

class\_name = "net"

method = "SSS-YOLO"

```



The global MarineGuard taxonomy must not be modified to make these paths

appear identical.



\---



\## 7. Downstream Compatibility



Both processing paths produce the existing canonical:



```text

DetectionResult

```



Therefore downstream components do not need separate result types for

CA-CFAR and SSS YOLO.



The expected downstream flow is:



```text

DetectionResult

&#x20;      |

&#x20;      +--> Fusion

&#x20;      |

&#x20;      +--> API

&#x20;      |

&#x20;      +--> MCP

```



\---



\## 8. Performance and Quality Considerations



No final claim is made that CA-CFAR + YOLO is more accurate than direct

YOLO inference.



A valid comparison would require controlled evaluation using the same

SSS test set and the same evaluation protocol.



Important metrics for such a future comparison would include:



\* recall

\* precision

\* false-positive rate

\* false-negative rate

\* detection count

\* localization quality

\* inference latency

\* robustness across different SSS conditions



Until such an experiment is completed, architecture selection is based

on interface simplicity, preservation of recall opportunities, current

implementation, and engineering risk.



\---



\## 9. Current Verification Evidence



The dedicated SSS YOLO path has been verified with the current

engineering/test ONNX checkpoint.



Measured result on the controlled SSS test image:



```text

Status: ok

Detections: 1

MarineGuard class\_id: 29

Class name: net

Confidence: 0.937634

```



PyTorch-to-ONNX parity was also verified:



```text

PyTorch detections: 1

ONNX detections:    1

Class match: True

Confidence difference: 0.0

Maximum bbox difference: 7.62939453125e-06

PARITY: PASS

```



These results verify engineering compatibility only. They do not

establish final SSS model performance or prove superiority of one

architecture over another.



\---



\## 10. Architecture Status



\### Implemented



\* \[x] CA-CFAR side-scan path

\* \[x] Dedicated SSS YOLO path

\* \[x] SSS class mapping

\* \[x] Canonical Detection output

\* \[x] Canonical DetectionResult output

\* \[x] API-compatible serialization

\* \[x] MCP-compatible downstream structure

\* \[x] Explicit separation between CA-CFAR and SSS YOLO



\### Recommended



\* \[x] Use direct SSS YOLO as the current dedicated SSS AI inference path

\* \[x] Keep CA-CFAR available as a separate anomaly/candidate detector

\* \[x] Keep the detector/model interface replaceable



\### Pending



\* \[ ] Controlled CA-CFAR + YOLO comparison

\* \[ ] Controlled direct-YOLO comparison on the final selected model

\* \[ ] Validated multimodal/co-registered fusion experiment

\* \[ ] Final SSS checkpoint selection by Person A

\* \[ ] Production latency benchmark

\* \[ ] GPU ONNX runtime verification



\---



\## 11. Engineering Decision



\*\*Current decision:\*\*



> Use the dedicated SSS YOLO model as the primary SSS AI detection path,

> while retaining CA-CFAR as a separate side-scan anomaly/candidate

> detection capability.



CA-CFAR must not be placed as a mandatory pre-filter in front of YOLO

without controlled evidence showing that the cascade improves the

required detection metrics.



This decision keeps the current implementation modular and allows future

experiments without changing the canonical MarineGuard detection

contract.



\---



\## 12. Important Constraints



The following must remain unchanged:



1\. Frozen MarineGuard V1 dataset.

2\. Frozen MarineGuard V1 test split.

3\. Frozen MarineGuard V1 checkpoint.

4\. MarineGuard 50-class taxonomy ordering.

5\. Existing canonical `Detection` structure.

6\. Existing canonical `DetectionResult` structure.



The current engineering/test SSS checkpoint is not the final SSS model

selection.



Person A's final model-selection result is authoritative for the final

SSS checkpoint.
