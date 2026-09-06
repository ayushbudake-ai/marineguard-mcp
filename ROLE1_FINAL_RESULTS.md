# MarineGuard — Role 1 Final Results

## 1. Role 1 contribution

Role 1 covers the data and AI-training foundation of MarineGuard:

- Multi-source dataset ingestion and annotation conversion
- Unified MarineGuard class taxonomy
- Dataset cleaning and validation
- Train / validation / test organization
- YOLO model training
- Held-out test evaluation
- Model handoff to Role 2

## 2. Prepared dataset

| Split | Images |
|---|---:|
| Train | 12,652 |
| Validation | 3,613 |
| Test | 1,808 |
| Total | 18,073 |

Unified taxonomy: **50 classes**

Final validated annotations: **46,209 bounding boxes**

Final label validation result: **0 invalid boxes**

## 3. Training configuration

- Model: **YOLOv8n object detection**
- Epoch target: **50**
- Image size: **512**
- Batch size: **16**
- Device: **NVIDIA GeForce RTX 3050 Laptop GPU**
- Workers: **0**
- AMP: **enabled**

Training completed successfully and produced:

```text
C:\aaaa\SIH\marineguard-mcp\runs\marineguard_full_512_b16-2\weights\best.pt
```

## 4. Final held-out TEST results

The final `best.pt` checkpoint was evaluated on the separate **1,808-image test split**.

| Metric | TEST result |
|---|---:|
| Precision | **89.70%** |
| Recall | **71.90%** |
| mAP50 | **80.69%** |
| mAP50-95 | **55.74%** |
| Calculated F1 | **79.94%** |

### F1 calculation

F1 was calculated from the held-out test precision and recall:

**F1 = 2 × Precision × Recall / (Precision + Recall)**

Using Precision = 0.8970301124 and Recall = 0.7190083251:

**F1 ≈ 0.7994 = 79.94%**

## 5. Diagnostic evidence

The test evaluation generated:

- `confusion_matrix.png`
- `confusion_matrix_normalized.png`
- `BoxF1_curve.png`
- `BoxPR_curve.png`
- `BoxP_curve.png`
- `BoxR_curve.png`
- test batch label/prediction visualizations

The normalized confusion matrix is predominantly diagonal, indicating generally correct class predictions, while weaker/rare classes require further review.

The prediction visualizations show the trained detector locating underwater objects and assigning class confidence scores.

## 6. Current interpretation

The headline result is:

> **89.70% Precision, 71.90% Recall, 79.94% calculated F1, 80.69% mAP50, and 55.74% mAP50-95 on the held-out test split.**

This demonstrates that the trained detector is functioning on unseen test data.

## 7. Important limitations / honest reporting

1. The current trained model is **YOLOv8n object detection**, not YOLOv8-seg instance segmentation.
2. The reported test metrics are for the detector and should not be presented as segmentation metrics.
3. The test-set F1 above is **calculated from test precision and recall**.
4. The full multi-sensor inference integration, ONNX deployment, confidence-filtering layer, real sensor fusion retuning, geotagging pipeline and final web integration are downstream tasks.
5. Some classes are rare in the dataset and therefore need special attention during later evaluation/tuning.

## 8. Handoff to Role 2

Role 2 can continue from:

```text
best.pt
```

and should then:

1. Export the trained model to ONNX.
2. Replace fallback inference in the detection modules with the real trained model.
3. Produce real model outputs/confidences for the downstream pipeline.
4. Retune sensor-fusion weights using real outputs.
5. Continue end-to-end evaluation.

## 9. Recommended PPT headline

> **MarineGuard trained a 50-class YOLO-based underwater detector and achieved 89.70% precision, 71.90% recall, 79.94% calculated F1, 80.69% mAP50 and 55.74% mAP50-95 on the held-out test set.**

*These figures are the current reported results from the test evaluation run and should be updated only if a later controlled experiment replaces them.*
