# MarineGuard MCP — Role 2: AI Inference & Integration Architecture

## 1. Overview & Architecture

Role 2 is responsible for **AI Inference, Service Abstraction, REST API, MCP Tooling, and Integration**. The architecture cleanly decouples the application, API, and MCP layers from the underlying YOLO/Ultralytics implementation details.

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                      Callers                            │
                    │  • REST API: POST /detect                               │
                    │  • MCP Tool: detect_marine_debris                       │
                    │  • Python API: ImageDetectionPipeline / VideoPipeline   │
                    │  • Sensor Modules: side_scan / optical / bathymetry     │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │              ImageDetectionPipeline                     │
                    │  1. Input Validation (File / Bytes / Numpy / PIL)       │
                    │  2. Preprocessing Hook (BasePreprocessor)               │
                    │  3. Model Execution (BaseDetector)                      │
                    │  4. Post-Processing (PostProcessor)                     │
                    │  5. Structured Schema (DetectionResult)                 │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    ▼                         ▼
                    ┌───────────────────────────┐ ┌───────────────────────────┐
                    │       YOLODetector        │ │   MockDetector (Testing)  │
                    │  • Loads models/best.pt   │ │  • Predictable Fixtures   │
                    │  • Official Class YAML    │ │  • Unit / API / MCP Tests │
                    │  • Raises if missing      │ │  • Zero Synthetic Weights │
                    └───────────────────────────┘ └───────────────────────────┘
```

---

## 2. Status: READY FOR MEMBER 1 MODEL

> [!IMPORTANT]
> **Zero Synthetic Weights or Fake Accuracy**:
> The entire Role 2 software architecture is 100% complete and fully verified. It is awaiting Member 1's final deliverables:
> 1. `models/best.pt` (Trained YOLOv8 weights)
> 2. `marineguard_classes.yaml` (Official 50-class taxonomy)
>
> The moment `models/best.pt` is placed in `models/`, the production detector activates automatically across all entry points without any code modifications.

---

## 3. Environment & Installation

### Recommended Production GPU Environment (CUDA)
- **Python Version**: Python 3.10, 3.11, or 3.12
- **Command**:
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # On Windows: .venv\Scripts\activate
  pip install --upgrade pip
  pip install -r requirements.txt
  # Install PyTorch with CUDA support:
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
  ```

### Development / Unit Test Environment (CPU / Python 3.14)
The test suite and MockDetector operate on standard Python without requiring GPU binaries:
```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## 4. Structured Detection Schema

All inference entry points return standardized schema objects defined in `marineguard/detection/schema.py`:

```json
{
  "detections": [
    {
      "class": "plastic-bottle",
      "class_id": 0,
      "confidence": 0.9123,
      "bbox": [120.0, 80.0, 240.0, 310.0]
    }
  ],
  "count": 1,
  "image_width": 640,
  "image_height": 480,
  "inference_time_ms": 14.2
}
```

---

## 5. Python API Usage

### Image Detection
```python
from marineguard.detection.pipeline import ImageDetectionPipeline
from marineguard.detection.annotator import ImageAnnotator

# Initialize pipeline (uses YOLODetector by default)
pipeline = ImageDetectionPipeline(confidence_threshold=0.50)

# Accepts image file paths, raw bytes, numpy arrays, or PIL Images
result = pipeline.process("path/to/sonar_or_optical_frame.png")

print(f"Detected {result.count} targets in {result.inference_time_ms:.1f}ms")
for det in result.detections:
    print(f"- {det.class_name} ({det.confidence*100:.1f}%) at bbox {det.bbox}")

# Generate annotated visualization
annotator = ImageAnnotator()
annotated_img = annotator.annotate("path/to/sonar_or_optical_frame.png", result)
annotated_img.save("annotated_result.png")
```

### Video / Stream Processing
```python
from marineguard.detection.video_pipeline import VideoDetectionPipeline

video_pipeline = VideoDetectionPipeline()

# Process offline video file with annotated output
summary = video_pipeline.process_video_file(
    video_path="rov_dive_feed.mp4",
    output_annotated_path="annotated_dive_feed.mp4",
    frame_stride=2,
)
print(f"Processed {summary['processed_frames']} frames, found {summary['total_detections']} items.")

# Or stream frames live from camera / ROV feed
def frame_stream():
    while True:
        frame = get_camera_frame() # [H, W, 3] numpy array
        yield frame

for detection_result, annotated_frame in video_pipeline.process_frame_stream(frame_stream()):
    handle_live_telemetry(detection_result, annotated_frame)
```

---

## 6. REST API Service

Start the FastAPI REST server:
```bash
uvicorn marineguard.api.app:app --host 0.0.0.0 --port 8000
```

### Endpoints
- `POST /detect`: Upload image frame (multipart/form-data)
  - Parameter: `file` (image file)
  - Parameter (optional): `confidence` (float [0.0, 1.0])
  - Responses:
    - `200 OK`: Structured JSON `{ "detections": [...], "count": N }`
    - `400 Bad Request`: Invalid image or unreadable payload
    - `503 Service Unavailable`: Production model weights (`models/best.pt`) not found
- `GET /health`: Healthcheck & model readiness status
- `GET /classes`: List of 50 classes from `marineguard_classes.yaml`

---

## 7. Model Context Protocol (MCP) Tool

The MCP server exposes `detect_marine_debris` in `marineguard/mcp_server.py`:
- **Tool Name**: `detect_marine_debris`
- **Inputs**: `image_input` (file path, raw bytes, or base64 data URI), `confidence_threshold` (optional float)
- **Error Handling**: Returns structured JSON errors (`INVALID_IMAGE`, `MODEL_NOT_FOUND`, `INFERENCE_ERROR`) without crashing the MCP transport session.

---

## 8. ONNX Export

When `models/best.pt` is provided by Member 1:
```bash
python export_onnx.py --weights models/best.pt --out models/best.onnx --imgsz 640
```

---

## 9. Benchmarking & Retuning

- **Benchmark Evaluation**:
  ```bash
  python eval_detection.py --weights models/best.pt --data data/processed/marineguard/data.yaml --split test
  ```
- **Sensor Fusion Retuning**:
  ```bash
  python retune_fusion_weights.py
  ```
