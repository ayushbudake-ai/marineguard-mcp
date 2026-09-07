from pathlib import Path
from ultralytics import YOLO

REPO = Path(__file__).resolve().parent
DATA = REPO / "data" / "processed" / "marineguard" / "data.yaml"
RUNS = REPO / "runs"

model = YOLO("yolov8n.pt")

model.train(
    data=str(DATA),
    epochs=50,
    imgsz=512,
    batch=16,
    device=0,
    workers=0,
    project=str(RUNS),
    name="marineguard_full_512_b16-2",
)

