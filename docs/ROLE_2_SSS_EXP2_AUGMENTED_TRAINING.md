# Role 2 — SSS Experiment #2 (moderate augmentation)

**These metrics are synthetic-development validation metrics only.**

They must not be described as real-world SSS performance, real ghost-net detection accuracy, or production accuracy.

A higher synthetic validation score alone does **not** prove better real-world performance.

Experiment #1 GhostVision OOD stress test remains the available real-SSS observation (no ghost-net ground truth). Experiment #2 has **not** been OOD-tested in this run.

---

## 1. Objective

Investigate whether **moderate** training augmentation can improve robustness/generalization while preserving the ability to detect ghost-net targets on the controlled MarineGuard SSS development set.

This experiment was **not** run to chase higher synthetic validation numbers.

## 2. Dataset

Used exactly `data/processed/marineguard_sss/data.yaml` with no dataset edits.

| Split | Images | Labels | Used |
| --- | ---: | ---: | --- |
| train | 1400 | 1400 | yes |
| val | 190 | 190 | yes (model selection only) |
| test | 190 | 190 | **no — reserved** |

Taxonomy: `0: net` (MarineGuard global class ID 29).

## 3. Model

- Architecture: YOLOv8n detection
- Initialization: `yolov8n.pt`
- **Not** fine-tuned from Experiment #1 `best.pt`

## 4. Training configuration

| Item | Value |
| --- | --- |
| epochs | 75 (complete run; no early stop for high val scores) |
| imgsz | 640 |
| batch | 16 |
| device | 0 (NVIDIA GeForce RTX 3050) |
| workers | 0 |
| seed | 43 |
| project | `runs/detect` |
| name | `marineguard_sss_yolov8n_exp2_augmented` |
| exist_ok | False |
| plots | True |
| save | True |
| val | True |
| Python | 3.14.5 |
| PyTorch | 2.14.0+cu126 |
| Ultralytics | 8.4.143 |

Batch remained **16**; no OOM fallback was required.


## 5. Augmentation (Ultralytics; images on disk unchanged)

| Parameter | Exp #2 |
| --- | --- |
| degrees | 5 |
| translate | 0.05 |
| scale | 0.20 |
| shear | 2 |
| perspective | 0.0 |
| fliplr | 0.5 |
| flipud | 0.0 |
| hsv_h | 0.0 (disabled; sonar appearance) |
| hsv_s | 0.0 (disabled; sonar appearance) |
| hsv_v | 0.20 (moderate intensity only) |
| mosaic | 1.0 (same class of mix as Exp #1 default) |
| mixup / cutmix / copy_paste | 0.0 |

No extreme geometric transforms. No hue/saturation shifts that would recolor sonar tiles.

## 6. Experiment #2 validation results (best.pt, val split only)

Standalone `model.val(split='val')` of the Ultralytics best checkpoint (fitness-selected, **not** automatically epoch 75).

| Item | Value |
| --- | --- |
| Best epoch (Ultralytics / csv) | 66 |
| Precision | 0.998700 |
| Recall | 1.000000 |
| F1 | 0.999349 |
| mAP50 | 0.995000 |
| mAP50-95 | 0.937444 |
| Train box / cls / dfl (best epoch from results.csv) | 0.29642 / 0.17938 / 0.78019 |
| Val box / cls / dfl (best epoch from results.csv) | 0.25523 / 0.16785 / 0.53160 |
| Total training time | 16338.1 s (4.538 h) |
| GPU | NVIDIA GeForce RTX 3050 |
| Peak VRAM (PyTorch allocated) | 1.813 GiB |
| best.pt | `runs/detect/runs/detect/marineguard_sss_yolov8n_exp2_augmented/weights/best.pt` |
| last.pt | `runs/detect/runs/detect/marineguard_sss_yolov8n_exp2_augmented/weights/last.pt` |

Retained artifacts under `runs/detect/runs/detect/marineguard_sss_yolov8n_exp2_augmented`: `results.csv`, `results.png`, confusion matrix, PR/F1 curves, `weights/best.pt`, `weights/last.pt`.

## 7. Comparison vs Experiment #1

Both columns are **synthetic development validation** of `best.pt` on `images/val`. They are not real-world SSS accuracy.

| Metric | Exp #1 | Exp #2 |
| --- | ---: | ---: |
| Precision | 0.999468 | 0.998700 |
| Recall | 1.000000 | 1.000000 |
| F1 | 0.999734 | 0.999349 |
| mAP50 | 0.995000 | 0.995000 |
| mAP50-95 | 0.987390 | 0.937444 |
| Best epoch | 49 | 66 |
| Training time | ~5292 s (~1.47 h, 50 epochs) | 16338.1 s (4.538 h, 75 epochs) |

On this synthetic val set, Experiment #2 is **lower on Precision, F1, mAP50-95; essentially unchanged on Recall, mAP50**.

That statement is limited to the controlled synthetic-ghost-net development validation set. It does **not** imply better GhostVision OOD behavior or real ghost-net detection.

## 8. Overfitting / training health

- NaN losses observed: False
- CUDA OOM (after fallback if any): False
- Corrupt image/label errors reported: False
- Final epoch reached: 75 / 75
- Last-epoch vs best mAP50-95 (csv): last=0.926430, best_csv=0.937140

If last-epoch mAP50-95 is materially below the best-epoch csv value, later epochs did not improve fitness; `best.pt` is the selected checkpoint.

## 9. Test split

**Not evaluated.** The 190-image test split remains reserved for the eventual final candidate.

## 10. Integrity

- Experiment #1 `best.pt` MD5 before: `41726e8ea5a2f13b251a612927e65f4b`
- Experiment #1 `best.pt` MD5 after: `41726e8ea5a2f13b251a612927e65f4b`
- Experiment #1 untouched: True
- GhostVision / DRISHTI / production detectors / ONNX / `data.yaml` were not modified by this training script.

Timestamp UTC: 2026-09-08T02:06:43.818923+00:00
