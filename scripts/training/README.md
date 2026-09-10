# 🏋️ Model Training Scripts

This folder contains scripts for training, fine-tuning, and evaluating MarineGuard object detection and instance segmentation models.

## Scripts

- **`train_yolov8_seg.py`**: Trains YOLOv8 segmentation on the combined marine dataset.
- **`run_full_training.py`**: Full 50-class production training executor.
- **`run_sanity.py`**: Quick sanity check on a small subset to verify loss convergence.
- **`run_v2_training.py` / `run_v2_smoke_test.py`**: Experimental V2 pipeline training scripts.
- **`resume_training.py`**: Resumes interrupted model training from the latest checkpoint.
- **`retune_fusion_weights.py`**: Multi-sensor fusion weight optimization script.
