"""
MarineGuard MCP — Role 2: Export trained checkpoint to ONNX for edge inference.

Usage:
    python export_onnx.py
    python export_onnx.py --weights models/best.pt --imgsz 640 --opset 12
"""

import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def export_model_to_onnx(
    weights_path: Path,
    output_path: Path,
    imgsz: int = 640,
    opset: int = 12,
    simplify: bool = True,
) -> Path:
    """Exports a trained YOLO model to ONNX format.

    Args:
        weights_path: Path to input PyTorch weights (e.g., models/best.pt).
        output_path: Target destination for the ONNX file.
        imgsz: Image input dimensions for export.
        opset: ONNX opset version.
        simplify: Whether to run onnxsim simplification.

    Returns:
        Path to exported ONNX model.
    """
    if not weights_path.exists():
        raise FileNotFoundError(
            f"Trained checkpoint not found at '{weights_path}'. "
            f"ONNX export requires Member 1's final trained model (models/best.pt)."
        )

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            f"Ultralytics is required for ONNX export: {exc}. "
            f"Run 'pip install ultralytics onnx onnxruntime' in your Python 3.10-3.12 environment."
        ) from exc

    print(f"[export_onnx] Loading trained checkpoint from: {weights_path}")
    model = YOLO(str(weights_path))

    print(f"[export_onnx] Starting export (imgsz={imgsz}, opset={opset}, simplify={simplify})...")
    exported = model.export(format="onnx", imgsz=imgsz, opset=opset, simplify=simplify)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if str(exported) != str(output_path):
        import shutil
        shutil.copy2(exported, output_path)

    print(f"[export_onnx] SUCCESS: Production ONNX model written to {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="MarineGuard YOLO to ONNX Exporter")
    parser.add_argument("--weights", default=str(REPO_ROOT / "models" / "best.pt"), help="Path to input weights")
    parser.add_argument("--out", default=str(REPO_ROOT / "models" / "best.onnx"), help="Path to output ONNX model")
    parser.add_argument("--imgsz", type=int, default=640, help="Export image dimensions")
    parser.add_argument("--opset", type=int, default=12, help="ONNX opset version")
    parser.add_argument("--simplify", action="store_true", default=True, help="Run ONNX graph simplification")
    args = parser.parse_args()

    weights = Path(args.weights)
    target = Path(args.out)

    try:
        export_model_to_onnx(
            weights_path=weights,
            output_path=target,
            imgsz=args.imgsz,
            opset=args.opset,
            simplify=args.simplify,
        )
    except FileNotFoundError as fnf:
        print(f"[export_onnx] ERROR: {fnf}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[export_onnx] EXPORT FAILED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
