"""
MarineGuard — Member 2: Retune fusion.py's per-sensor weights against real output.

The current weights in marineguard/detection/fusion.py (side_scan: 0.40,
sas: 0.50, optical: 0.35, bathymetry: 0.25) are hand-guessed defaults, not
derived from data. Once the trained model is producing real per-sensor
confidences on a labeled validation set, this script grid-searches the
weight combination that maximizes F1 on that set, so the fusion weights
are backed by a number instead of a guess.

This needs a validation set of (per-sensor confidences, ground-truth label)
tuples — it does NOT need to be re-run through the detectors here, just
point it at a CSV/JSON of already-computed contact records once you have
one. Fill in `load_validation_contacts()` for your actual export format.
"""

import itertools
import json
from pathlib import Path
from typing import List, Dict, Any

from marineguard.detection.fusion import MultiSensorFusionEngine
from marineguard.schemas import DebrisContact

REPO_ROOT = Path(__file__).resolve().parent


def load_validation_contacts(path: Path) -> List[List[DebrisContact]]:
    """Expected input: a JSON file that's a list of "fusion groups", where each
    group is a list of DebrisContact dicts (one per sensor) that all refer to
    the same real-world object, plus a 'ground_truth_label' field on each
    contact for scoring. Adjust this loader to match whatever format the
    real evaluation pipeline actually exports.
    """
    with open(path) as f:
        raw_groups = json.load(f)
    groups = []
    for group in raw_groups:
        groups.append([DebrisContact(**c) for c in group])
    return groups


def score_weights(weights: Dict[str, float], groups: List[List[DebrisContact]]) -> float:
    """Returns F1 of (fused confidence >= 0.5) vs whether the group's label
    was actually correct. Placeholder scoring logic -- swap in whatever
    correctness signal your labeled validation set actually provides.
    """
    engine = MultiSensorFusionEngine(weights=weights)
    tp = fp = fn = 0
    for group in groups:
        if not group:
            continue
        target = engine.fuse(group)
        predicted_positive = target.confidence >= 0.5
        actually_positive = getattr(group[0], "ground_truth_positive", True)
        if predicted_positive and actually_positive:
            tp += 1
        elif predicted_positive and not actually_positive:
            fp += 1
        elif not predicted_positive and actually_positive:
            fn += 1
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def main():
    val_path = REPO_ROOT / "data" / "processed" / "marineguard" / "fusion_validation.json"
    if not val_path.exists():
        print(f"[retune_fusion_weights] No validation export at {val_path} yet — "
              f"nothing to retune against. This script is ready to run once one exists.")
        return

    groups = load_validation_contacts(val_path)

    sensor_weight_grid = [0.20, 0.30, 0.40, 0.50, 0.60]
    best_score, best_weights = -1.0, None

    for sc, ss, op, ba in itertools.product(sensor_weight_grid, repeat=4):
        weights = {"sas": sc, "side_scan": ss, "optical": op, "bathymetry": ba}
        score = score_weights(weights, groups)
        if score > best_score:
            best_score, best_weights = score, weights

    print(f"Best F1: {best_score:.3f}")
    print(f"Best weights: {best_weights}")
    print("\nUpdate MultiSensorFusionEngine.DEFAULT_WEIGHTS in "
          "marineguard/detection/fusion.py with these values.")


if __name__ == "__main__":
    main()
