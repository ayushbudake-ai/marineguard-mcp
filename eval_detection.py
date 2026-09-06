"""
MarineGuard MCP — Role 2: Real Detection Benchmark

Computes actual F1 / precision / recall on held-out data using the trained
model, via ultralytics' built-in validation.

Usage:
    python eval_detection.py
    python eval_detection.py --weights models/best.pt --data data/processed/marineguard/data.yaml
"""

import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

REPO_ROOT = Path(__file__).resolve().parent
console = Console()


def main():
    parser = argparse.ArgumentParser(description="MarineGuard Real Detection Benchmark")
    parser.add_argument("--weights", default=str(REPO_ROOT / "models" / "best.pt"))
    parser.add_argument("--data", default=str(REPO_ROOT / "data" / "processed" / "marineguard" / "data.yaml"))
    parser.add_argument("--split", default="test", choices=["val", "test"])
    parser.add_argument("--out", default=str(REPO_ROOT / "data" / "reports" / "detection_metrics.json"))
    args = parser.parse_args()

    weights_path = Path(args.weights)
    data_path = Path(args.data)

    if not weights_path.exists():
        console.print(f"[bold red]No trained model at {weights_path}.[/bold red] "
                      f"Nothing real to benchmark yet — run training on Member 1's dataset first.")
        return
    if not data_path.exists():
        console.print(f"[bold red]No dataset config at {data_path}.[/bold red] "
                      f"The labeled dataset has not been dropped into the repo yet.")
        return

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        console.print(f"[bold red]Ultralytics is required for benchmark evaluation: {exc}[/bold red]")
        sys.exit(1)

    model = YOLO(str(weights_path))
    metrics = model.val(data=str(data_path), split=args.split)

    # Ultralytics exposes these on the results-box object
    precision = float(metrics.box.mp)   # mean precision across classes
    recall = float(metrics.box.mr)      # mean recall across classes
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    map50 = float(metrics.box.map50)
    map5095 = float(metrics.box.map)

    table = Table(title="MarineGuard — Real Detection Benchmark (held-out data, no synthetic numbers)",
                  border_style="green")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Precision (mean)", f"{precision:.3f}")
    table.add_row("Recall (mean)", f"{recall:.3f}")
    table.add_row("F1-score", f"{f1:.3f}")
    table.add_row("mAP@50", f"{map50:.3f}")
    table.add_row("mAP@50:95", f"{map5095:.3f}")
    console.print(table)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "map50": map50,
            "map50_95": map5095,
            "split": args.split,
            "weights": str(weights_path),
        }, f, indent=2)
    console.print(f"\nMetrics written to {out_path}")


if __name__ == "__main__":
    main()
