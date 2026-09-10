# 📈 Evaluation & Benchmarking Scripts

This folder contains scripts for measuring model accuracy metrics, inference latency, and exporting models for edge deployment.

## Scripts

- **`eval_detection.py`**: Computes precision, recall, F1, and mAP metrics against held-out test splits.
- **`evaluate_test.py`**: Automated evaluation on the frozen V1 test set.
- **`benchmark_v1_latency.py`**: Measures real CPU/GPU batch and single-image inference latency (saved to `v1_latency_benchmark.json`).
- **`export_onnx.py`**: Exports PyTorch YOLO checkpoints to optimized ONNX format.
- **`verify_onnx.py` / `verify_sss_onnx.py`**: Validates numerical parity and output contract compliance between PyTorch and ONNX runtime.
