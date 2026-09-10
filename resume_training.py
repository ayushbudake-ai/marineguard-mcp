from pathlib import Path
from ultralytics import YOLO

REPO = Path(__file__).resolve().parent

MODEL_PATH = REPO / "runs" / "marineguard_full_512_b16-2" / "weights" / "last.pt"


def main():
    model = YOLO(str(MODEL_PATH))
    model.train(resume=True)


if __name__ == "__main__":
    main()