"""
MarineGuard — Member 2: YOLOv8-seg Training Entry Point

Portable rewrite of the original script (which hardcoded a Windows path and a
specific GPU index, so it only ran on one person's laptop).

Usage:
    python run_full_training.py
    python run_full_training.py --epochs 100 --batch 32
    python run_full_training.py --data data/processed/marineguard/data.yaml --device cpu

Requires `models/` and a populated `data/processed/marineguard/images/{train,val,test}`
+ `labels/{train,val,test}` tree (see DATA_HANDOFF.md for the exact layout Member 1's
dataset needs to match). This script does NOT download or generate that data.
"""

import argparse
from pathlib import Path

from ultralytics import YOLO

REPO_ROOT = Path(__file__).resolve().parent


def detect_device() -> str:
    """Use a GPU if one is actually available, otherwise fall back to CPU
    instead of hardcoding device=0 and crashing on machines without a GPU."""
    try:
        import torch
        if torch.cuda.is_available():
            return "0"
    except ImportError:
        pass
    return "cpu"


def main():
    parser = argparse.ArgumentParser(description="Fine-tune YOLOv8-seg on the MarineGuard debris dataset.")
    parser.add_argument("--data", default=str(REPO_ROOT / "data" / "processed" / "marineguard" / "data.yaml"),
                         help="Path to the dataset's data.yaml")
    parser.add_argument("--model", default="yolov8n-seg.pt",
                         help="Base checkpoint to fine-tune from (use *-seg.pt for segmentation, plain *.pt for detection-only)")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=512)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default=None, help="e.g. '0', 'cpu'. Auto-detected if omitted.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--project", default=str(REPO_ROOT / "runs"))
    parser.add_argument("--name", default="marineguard_train")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset config not found at {data_path}.\n"
            f"This means the labeled dataset hasn't been dropped into the repo yet — "
            f"see DATA_HANDOFF.md for the folder layout that needs to exist before this can run."
        )

    device = args.device or detect_device()
    print(f"[run_full_training] Using device: {device}")

    model = YOLO(args.model)
    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        workers=args.workers,
        amp=(device != "cpu"),
        patience=args.patience,
        save=True,
        plots=True,
        project=args.project,
        name=args.name,
    )

    # Convenience: copy/symlink the best checkpoint to models/best.pt so every
    # other Member-2 script (model_loader.py, export_onnx.py, eval.py) can find
    # it in one predictable place without hunting through runs/.
    best_ckpt = Path(args.project) / args.name / "weights" / "best.pt"
    models_dir = REPO_ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    target = models_dir / "best.pt"
    if best_ckpt.exists():
        import shutil
        shutil.copy2(best_ckpt, target)
        print(f"[run_full_training] Copied best checkpoint to {target}")
    else:
        print(f"[run_full_training] WARNING: expected checkpoint not found at {best_ckpt}")


if __name__ == "__main__":
    main()