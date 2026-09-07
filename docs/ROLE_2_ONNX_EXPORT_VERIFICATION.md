# MarineGuard MCP — Role 2: YOLOv8n-Seg ONNX Export & PyTorch-vs-ONNX Verification Report

**Document Date**: 2026-09-07  
**Author**: Role 2 AI Inference & Integration Lead  
**Status**: **VERIFIED WITH MINOR NUMERICAL DIFFERENCES**  
**Source Checkpoint**: 
uns/seaclear_yolov8n_seg/train/weights/best.pt  
**ONNX Artifact**: 
uns/seaclear_yolov8n_seg/onnx/best.onnx  

---

## 1. Purpose & Scope

This document records the official **ONNX export** and **PyTorch vs. ONNX parity verification** for the trained **YOLOv8n-seg** instance segmentation model on the SeaClear dataset.

The objective of this verification stage is to:
1. Export the verified PyTorch training checkpoint (est.pt) to an ONNX graph.
2. Validate ONNX model structural integrity, operator support, and I/O shapes using the ONNX checker and ONNX Runtime.
3. Quantify numerical output parity (confidences, bounding boxes, and segmentation masks) between the native PyTorch model and ONNX Runtime on identical validation inputs.
4. Establish a benchmarked, standalone ONNX artifact prior to downstream integration into optical.py and usion.py.

> [!NOTE]
> This stage strictly covers model export and comparative verification. Downstream runtime integration into the production optical pipeline is a separate subsequent step.

---

## 2. Source Checkpoint

* **Checkpoint Path**: [
uns/seaclear_yolov8n_seg/train/weights/best.pt](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/train/weights/best.pt)
* **Training Run**: 50-epoch SeaClear YOLOv8n-seg run
* **Optimal Epoch**: **Epoch 48** (achieved highest validation mask mAP50-95 of 0.3806 / box mAP50 of 0.6522)
* **Architecture**: YOLOv8n-seg (85 fused layers, 3,267,814 parameters, 7.3 GFLOPs)
* **Task**: segment (Instance Segmentation, 50-class taxonomy)

---

## 3. Export Configuration & Environment

The export was performed directly from the trained PyTorch checkpoint using Ultralytics with the following verified parameters:

| Parameter | Configured Value | Description / Rationale |
|---|---|---|
| **Format** | onnx | Open Neural Network Exchange graph format |
| **Input Image Size (imgsz)** | 512 | Matches native training resolution (512x512) |
| **Batch Size** | 1 | Single-frame edge stream inference |
| **Dynamic Shapes** | False | Static tensor shapes for predictable edge latency |
| **Precision (half)** | False | FP32 standard precision baseline |
| **Device** | cpu | Host CPU export |
| **Opset Version** | 18 | Standard ONNX operator set for YOLOv8 segmentation ops |
| **Simplify** | False | Clean baseline graph export |

### Software Environment
* **PyTorch**: 2.14.0+cpu
* **Ultralytics**: 8.4.142
* **ONNX**: 1.22.0
* **ONNX Runtime**: 1.29.0
* **Execution Provider**: CPUExecutionProvider

---

## 4. ONNX Model Artifact & Graph I/O

The exported model is stored in the dedicated ONNX directory:

* **Artifact Path**: [
uns/seaclear_yolov8n_seg/onnx/best.onnx](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/onnx/best.onnx)
* **File Size**: **13,235,431 bytes (~12.62 MB)**
* **Verification Report**: [
uns/seaclear_yolov8n_seg/onnx/onnx_verification.json](file:///d:/Marine%20Drive/marineguard-mcp/runs/seaclear_yolov8n_seg/onnx/onnx_verification.json)

### Graph Input & Output Specifications

| Name | Type | Tensor Shape | Semantic Meaning |
|---|---|---|---|
| **images** *(Input)* | 	ensor(float) | [1, 3, 512, 512] | RGB image batch normalized to $[0.0, 1.0]$ |
| **output0** *(Output)* | 	ensor(float) | [1, 86, 5376] | Detection head output: 4 box coords + 50 class scores + 32 mask coefficients per anchor |
| **output1** *(Output)* | 	ensor(float) | [1, 32, 128, 128] | Prototype mask prototypes ( \times 128 \times 128$) |

---

## 5. Structural & Graph Validation

1. **onnx.checker Validation**: **PASSED** (0 structural, type, or shape errors).
2. **ONNX Runtime InferenceSession**: **PASSED** (InferenceSession initialized cleanly with CPUExecutionProvider).
3. **Raw Tensor Parity (Pre-NMS)**:
   * output0 (Box & Class predictions): Maximum absolute difference = **0.001526**, Mean difference = **2.47e-06**.
   * output1 (Proto masks): Maximum absolute difference = **0.0000165**, Mean difference = **8.60e-07**.

---

## 6. Controlled PyTorch vs. ONNX Parity Evaluation

Inference was executed on a representative sample of validation images from data/processed/seaclear_segmentation/images/val/ using identical preprocessing (512x512 square letterbox, normalization) and post-processing (confidence threshold = 0.25, NMS IoU threshold = 0.70):

| Sample Image | PT Detections | ONNX Detections | Class Agreement | Max Conf Diff | Max Box Diff (px) | Mask Agreement |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1009.jpg** | 1 (nimal) | 1 (nimal) | **100% Match** | .30 \times 10^{-7}$ | .0000\text{ px}$ | **100% Match** |
| **1017.jpg** | 2 (glass-bottle, nimal) | 2 (glass-bottle, nimal) | **100% Match** | .88 \times 10^{-6}$ | .0001\text{ px}$ | **100% Match** |
| **1019.jpg** | 2 (metal-wreckage, metal-wreckage) | 2 (metal-wreckage, metal-wreckage) | **100% Match** | .36 \times 10^{-6}$ | .0007\text{ px}$ | **100% Match** |
| **1037.jpg** | 9 (mixed classes) | 9 (mixed classes) | **100% Match** | .83 \times 10^{-6}$ | .0004\text{ px}$ | **100% Match** |
| **1043.jpg** | 4 (
ope, shell, 
ope, shell) | 4 (
ope, shell, 
ope, shell) | **100% Match** | .23 \times 10^{-6}$ | .0007\text{ px}$ | **100% Match** |

### Detailed Metric Findings:
* **Detection Count Parity**: **100%** (Identical count across all samples).
* **Class Identification Parity**: **100%** (All predicted class IDs and names match identically in order).
* **Confidence Parity**: Average difference $< 5.0 \times 10^{-6}$, maximum difference across all predictions $= 8.88 \times 10^{-6}$.
* **Bounding Box Alignment**: Maximum coordinate delta $< 0.001\text{ pixels}$.
* **Segmentation Mask Alignment**: Pixel-for-pixel exact match on thresholded segmentation masks.

---

## 7. Conclusion

### Overall Result: **VERIFIED WITH MINOR NUMERICAL DIFFERENCES**

The exported ONNX model (
uns/seaclear_yolov8n_seg/onnx/best.onnx) achieves exceptional floating-point fidelity with the original PyTorch checkpoint (est.pt). The minor numerical differences observed are well within standard floating-point execution provider tolerance ($\le 8.88 \times 10^{-6}$ on confidences, $< 0.001\text{ px}$ on bounding boxes) and have zero impact on detection counts, class assignments, or segmentation masks.

---

## 8. Downstream Next Steps (Pending Authorization)

The following integration steps are identified for subsequent execution:

1. **Optical Inference Pipeline Integration**: Wire 
uns/seaclear_yolov8n_seg/onnx/best.onnx into marineguard/detection/ / optical.py for ONNX Runtime acceleration.
2. **Multimodal Fusion Calibration**: Ingest real ONNX segmentation masks into usion.py to evaluate spatial IoU against acoustic detections.
3. **End-to-End System Benchmark**: Validate full multimodal pipeline throughput and latency with ONNX Runtime.

*(Note: Production integration was intentionally NOT performed during this verification task).*
