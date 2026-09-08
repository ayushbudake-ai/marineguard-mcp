\# MarineGuard SSS ONNX Verification



\*\*Status:\*\* Verified

\*\*Scope:\*\* Role 2 — PyTorch to ONNX inference verification



\---



\## 1. Purpose



This document records the engineering verification of the dedicated

Side-Scan Sonar (SSS) YOLO model after ONNX export.



The objective is to verify that the exported ONNX model can:



\* load successfully

\* pass ONNX graph validation

\* run through ONNX Runtime

\* produce detections

\* preserve class IDs

\* preserve confidence values within measured tolerance

\* preserve bounding boxes within measured tolerance



This verification does not represent final SSS model evaluation or

model selection.



\---



\## 2. Model



Engineering/test checkpoint:



```text

runs/detect/runs/detect/marineguard\_sss\_yolov8n\_exp2\_augmented/weights/best.pt

```



Exported ONNX model:



```text

runs/detect/runs/detect/marineguard\_sss\_yolov8n\_exp2\_augmented/weights/best.onnx

```



Measured ONNX properties:



```text

ONNX version: 1.22.0

Opset: 17

Input shape: (1, 3, 640, 640)

Output shape: (1, 5, 8400)

ONNX file size: 12,265,746 bytes

```



\---



\## 3. Verification Script



Reusable verification script:



```text

scripts/verify\_sss\_onnx.py

```



The script compares PyTorch and ONNX inference on the same input image.



\---



\## 4. Test Input



Test image:



```text

data/processed/marineguard\_sss/images/test/synth\_ghost\_net\_00001.png

```



The same image was used for both PyTorch and ONNX inference.



\---



\## 5. PyTorch Result



Measured PyTorch result:



```text

Detections: 1



class\_id   = 0

confidence = 0.937634

bbox       = \[113.595, 210.615, 226.197, 319.279]

```



The native SSS model class `0` represents:



```text

net

```



\---



\## 6. ONNX Runtime Result



Measured ONNX Runtime result:



```text

Provider:

CPUExecutionProvider



Detections: 1



class\_id   = 0

confidence = 0.937634

bbox       = \[113.595, 210.615, 226.197, 319.279]

```



\---



\## 7. Parity Results



Measured comparison:



```text

PyTorch detections: 1

ONNX detections:    1



Class match: True



Confidence absolute difference:

0.0



Maximum bbox absolute difference:

7.62939453125e-06

```



Final verification result:



```text

PARITY: PASS

```



The class IDs match and the numerical outputs are comparable within

the measured differences above.



\---



\## 8. ONNX Runtime Environment



The environment exposes the following providers:



```text

TensorrtExecutionProvider

CUDAExecutionProvider

CPUExecutionProvider

```



However, the CUDA execution provider is currently unavailable for

actual inference because the required CUDA 13 / cuDNN 9 runtime

dependencies are not present.



Therefore the measured ONNX verification was performed using:



```text

CPUExecutionProvider

```



No GPU ONNX parity result is claimed.



\---



\## 9. Side-Scan MarineGuard Mapping



The native SSS model uses:



```text

SSS class 0 = net

```



MarineGuard's authoritative taxonomy uses:



```text

MarineGuard class 29 = net

```



The ONNX verification compares the native model output.



The conversion:



```text

SSS class 0 -> MarineGuard class 29

```



is performed by the SSS integration layer in `side\_scan.py`.



The global MarineGuard taxonomy is not modified.



\---



\## 10. Verification Limitations



This verification proves ONNX inference compatibility for the tested

input and environment.



It does not prove:



\* final SSS model accuracy

\* final SSS checkpoint selection

\* complete test-set performance

\* GPU ONNX performance

\* production latency

\* robustness across all SSS inputs



Those items require separate evaluation.



\---



\## 11. Verification Status



```text

\[x] PyTorch checkpoint loads

\[x] ONNX export completed

\[x] ONNX graph validation passed

\[x] ONNX Runtime loads model

\[x] ONNX inference completed

\[x] Detection count compared

\[x] Class IDs compared

\[x] Confidence values compared

\[x] Bounding boxes compared

\[x] Numerical parity passed

\[x] CPU ONNX verification completed



\[ ] GPU ONNX verification

\[ ] Final selected SSS checkpoint verification

\[ ] Full SSS test-set verification

\[ ] Production latency benchmark

```



\---



\## 12. Reproduction Command



From the repository root:



```powershell

python .\\scripts\\verify\_sss\_onnx.py

```



The command should be run after confirming that the referenced

engineering/test checkpoint and ONNX model exist.



\---



\## 13. Conclusion



The exported SSS YOLO ONNX model successfully loads and performs

inference through ONNX Runtime.



For the tested image, PyTorch and ONNX produced:



```text

1 detection

same native class ID

same confidence

numerically comparable bounding box

```



Therefore the measured PyTorch-to-ONNX verification result is:



```text

PASS

```



This is an engineering verification result only and must not be

interpreted as final SSS model performance.
