# 🛠️ MarineGuard Pipeline Scripts

This directory contains standalone execution scripts organized by operational lifecycle stages:

## Subdirectories

- **[`preprocessing/`](./preprocessing/)**: Dataset ingestion, taxonomy normalization, validation, and format conversion scripts (FLS, UATD, SeaClear, TrashCan).
- **[`training/`](./training/)**: YOLOv8-seg and detection model training pipelines, hyperparameter tuning, and sanity checkpoints.
- **[`evaluation/`](./evaluation/)**: Model accuracy benchmarking (mAP50, Precision, Recall, F1), inference latency profiling, and ONNX verification tools.
