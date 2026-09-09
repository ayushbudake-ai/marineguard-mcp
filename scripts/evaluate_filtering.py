"""
Role 3 — Reproducible Before/After Filtering Evaluation
scripts/evaluate_filtering.py

Usage:
    python scripts/evaluate_filtering.py [--threshold 0.30] [--all-thresholds]

This script compares Role 2 raw detections (BEFORE) with Role 3
filtered detections (AFTER) using a synthetic test set.

IMPORTANT SCIENTIFIC NOTE:
    - No labelled ground-truth dataset is available in this repository
      for the CA-CFAR or optical detections.
    - Therefore, precision / recall / F1 / FPR CANNOT be measured
      and are NOT reported. Claiming those metrics without valid ground
      truth would be scientifically dishonest.
    - What IS reported:
        * raw_count: total detections before filtering
        * accepted_count: detections passing all filters
        * rejected_count: detections rejected
        * rejection reasons: breakdown by reason
        * calibrated confidence distribution
    - These are deterministic operational measurements, not statistical
      accuracy metrics. They characterise the filter behaviour, not its
      correctness relative to ground truth.

If ground-truth labels are added to the repository in a future role,
extend this script with:
    from sklearn.metrics import precision_score, recall_score, f1_score
    and add a GroundTruthEvaluator class that loads labels.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure the project root is on the path when running as a script
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.filtering import filter_detection_result, FilteredResult
from marineguard.detection.confidence import calibrate_confidence, CONFIDENCE_METHOD
from marineguard.detection.evidence import format_result_summary


# ---------------------------------------------------------------------------
# Synthetic test detections (no model weights required)
# ---------------------------------------------------------------------------

SYNTHETIC_DETECTIONS: List[Dict[str, Any]] = [
    # Optical — high confidence, valid bbox
    {"class": "plastic-bottle", "class_id": 0, "confidence": 0.92,
     "bbox": [100.0, 80.0, 240.0, 310.0], "metadata": {"source_sensor": "optical"}},
    # Optical — medium confidence, valid bbox
    {"class": "tire", "class_id": 8, "confidence": 0.67,
     "bbox": [50.0, 60.0, 150.0, 180.0], "metadata": {"source_sensor": "optical"}},
    # Optical — low confidence (should be rejected)
    {"class": "can", "class_id": 1, "confidence": 0.18,
     "bbox": [200.0, 200.0, 280.0, 280.0], "metadata": {"source_sensor": "optical"}},
    # SSS net (class_id=29) — valid
    {"class": "net", "class_id": 29, "confidence": 0.78,
     "bbox": [30.0, 30.0, 200.0, 200.0], "metadata": {"source_sensor": "side_scan"}},
    # CA-CFAR (class_id=27) — valid area
    {"class": "unknown-object", "class_id": 27, "confidence": 0.61,
     "bbox": [50.0, 50.0, 120.0, 110.0], "metadata": {"source_sensor": "ca_cfar"}},
    # CA-CFAR (class_id=27) — tiny area (should be rejected)
    {"class": "unknown-object", "class_id": 27, "confidence": 0.55,
     "bbox": [10.0, 10.0, 12.0, 11.5], "metadata": {"source_sensor": "ca_cfar"}},
    # Zero-area bbox (should be rejected)
    {"class": "plastic-bag", "class_id": 3, "confidence": 0.75,
     "bbox": [100.0, 100.0, 100.0, 100.0], "metadata": {"source_sensor": "optical"}},
    # Extreme aspect ratio (should be rejected)
    {"class": "rope", "class_id": 10, "confidence": 0.70,
     "bbox": [0.0, 200.0, 639.0, 202.0], "metadata": {"source_sensor": "optical"}},
    # Fully out of bounds (should be rejected)
    {"class": "bottle", "class_id": 0, "confidence": 0.80,
     "bbox": [700.0, 500.0, 800.0, 600.0], "metadata": {"source_sensor": "optical"}},
    # Optical — good confidence at the boundary
    {"class": "ghost-net", "class_id": 20, "confidence": 0.50,
     "bbox": [10.0, 10.0, 300.0, 400.0], "metadata": {"source_sensor": "optical"}},
]

IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480


def build_synthetic_result() -> DetectionResult:
    """Build a DetectionResult from the synthetic test set."""
    detections = []
    for raw in SYNTHETIC_DETECTIONS:
        detections.append(Detection(
            class_name=raw["class"],
            class_id=raw.get("class_id"),
            confidence=raw["confidence"],
            bbox=raw["bbox"],
            metadata=raw.get("metadata", {}),
        ))
    return DetectionResult.from_detections(
        detections=detections,
        image_width=IMAGE_WIDTH,
        image_height=IMAGE_HEIGHT,
        model_name="SyntheticTestSet",
    )


def evaluate_threshold(
    result: DetectionResult,
    threshold: float,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run Role 3 filtering at a given threshold and return a metrics dict."""
    fr = filter_detection_result(
        result,
        confidence_threshold=threshold,
        min_area_px2=4.0,
        max_aspect_ratio=50.0,
        apply_modality_rules=True,
        image_width=IMAGE_WIDTH,
        image_height=IMAGE_HEIGHT,
    )

    # Rejection reason breakdown
    reason_counts: Dict[str, int] = {}
    for fd in fr.rejected:
        reason = fd.filter_reason or "UNKNOWN"
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    # Calibrated confidence distribution for accepted detections
    cal_confidences = [fd.calibrated_confidence for fd in fr.accepted]
    cal_mean = round(sum(cal_confidences) / len(cal_confidences), 2) if cal_confidences else None
    cal_min = min(cal_confidences) if cal_confidences else None
    cal_max = max(cal_confidences) if cal_confidences else None

    metrics = {
        "threshold": threshold,
        "raw_count": len(result.detections),
        "accepted_count": len(fr.accepted),
        "rejected_count": len(fr.rejected),
        "rejection_reasons": reason_counts,
        "calibrated_confidence_mean": cal_mean,
        "calibrated_confidence_min": cal_min,
        "calibrated_confidence_max": cal_max,
        "confidence_method": CONFIDENCE_METHOD,
        "precision_recall_f1": "NOT MEASURED — no labelled ground truth available",
        "false_positive_rate": "NOT MEASURED — no labelled ground truth available",
    }

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"THRESHOLD = {threshold:.2f}")
        print(f"{'=' * 60}")
        print(format_result_summary(fr))

    return metrics


def print_table(all_metrics: List[Dict[str, Any]]) -> None:
    """Print a summary table for multiple thresholds."""
    print("\nROLE 3 THRESHOLD ANALYSIS")
    print("=" * 60)
    print(f"{'Threshold':>10} {'Raw':>6} {'Accept':>8} {'Reject':>8}")
    print("-" * 60)
    for m in all_metrics:
        print(
            f"  {m['threshold']:.2f}      "
            f"{m['raw_count']:>4}   "
            f"{m['accepted_count']:>6}   "
            f"{m['rejected_count']:>6}"
        )
    print("-" * 60)
    print()
    print("NOTE: precision / recall / F1 / FPR are NOT MEASURED.")
    print("      No labelled ground truth exists in this repository.")
    print("      Reported counts are deterministic operational metrics only.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Role 3 before/after filtering evaluation"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.30,
        help="Single confidence threshold to evaluate (default: 0.30)"
    )
    parser.add_argument(
        "--all-thresholds", action="store_true",
        help="Evaluate across thresholds 0.10–0.90"
    )
    parser.add_argument(
        "--output-json", type=str, default=None,
        help="Optional path to write JSON results"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print per-threshold detail"
    )
    args = parser.parse_args()

    result = build_synthetic_result()

    print(f"\nBEFORE (Role 2 raw):")
    print(f"  Total detections: {len(result.detections)}")
    print(f"  Confidence values: {[round(d.confidence, 3) for d in result.detections]}")

    if args.all_thresholds:
        thresholds = [round(t * 0.1, 2) for t in range(1, 10)]
    else:
        thresholds = [args.threshold]

    all_metrics = []
    for t in thresholds:
        m = evaluate_threshold(result, t, verbose=args.verbose)
        all_metrics.append(m)

    print(f"\nAFTER (Role 3 filtered):")
    print_table(all_metrics)

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(all_metrics, f, indent=2)
        print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
