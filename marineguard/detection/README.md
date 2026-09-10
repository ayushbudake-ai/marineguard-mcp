# 🧠 AI & Detection Pipeline Layer

This package contains the core object detection, Side-Scan Sonar (SSS) processing, and model loading infrastructure.

## Modules

- **`sss_yolo_adapter.py`**: Authoritative wrapper for the YOLOv8n SSS detection model, including SHA256 integrity verification.
- **`side_scan.py`**: Side-Scan Sonar acoustic normalization, noise filtering, and anomaly detector.
- **`detector.py`**: Optical debris detection engine.
- **`model_loader.py`**: Model weight checkpoint loader with format detection (PyTorch `.pt` / ONNX).
