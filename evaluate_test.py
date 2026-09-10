from pathlib import Path
from ultralytics import YOLO

REPO = Path(__file__).resolve().parent

MODEL_PATH = REPO / "runs" / "marineguard_full_512_b16-2" / "weights" / "best.pt"
DATA_PATH = REPO / "data" / "processed" / "marineguard" / "data.yaml"
RUNS_DIR = REPO / "runs"


def main():
    model = YOLO(str(MODEL_PATH))

    results = model.val(
        data=str(DATA_PATH),
        split="test",
        imgsz=512,
        batch=16,
        device=0,
        workers=0,
        plots=True,
        project=str(RUNS_DIR),
        name="marineguard_test_evaluation",
    )

    print("\nTEST EVALUATION COMPLETE")
    print(f"Precision: {results.box.mp}")
    print(f"Recall:    {results.box.mr}")
    print(f"mAP50:     {results.box.map50}")
    print(f"mAP50-95:  {results.box.map}")


if __name__ == "__main__":
    main()