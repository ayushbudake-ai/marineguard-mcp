from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
DATA_YAML = ROOT / "data" / "processed_v2" / "marineguard" / "data.yaml"
RUNS_DIR = ROOT / "runs"


def main():
    model = YOLO("yolov8n.pt")

    model.train(
        data=str(DATA_YAML),
        epochs=1,
        imgsz=512,
        batch=16,
        device=0,
        workers=0,
        amp=True,
        patience=1,
        save=True,
        plots=True,
        project=str(RUNS_DIR),
        name="marineguard_v2_smoke_test",
    )


if __name__ == "__main__":
    main()
