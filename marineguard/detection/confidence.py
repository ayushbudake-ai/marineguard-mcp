"""
Role 3 — Confidence Processing Layer for MarineGuard MCP

Provides deterministic presentation confidence for Detection objects.

Design:
    Raw model confidence (0.0–1.0) is preserved unchanged.
    A calibrated_confidence (0–100 integer) is derived as a
    deterministic monotonic rescaling using a piecewise linear
    sharpening curve documented below.

Calibration method: DETERMINISTIC_PIECEWISE_LINEAR
    This is NOT statistical probability calibration (e.g., Platt Scaling
    or Isotonic Regression). No calibration dataset has been collected for
    this project. The method is a transparent deterministic transformation
    designed to:
        1. Preserve strict monotonicity (higher raw → higher calibrated)
        2. Sharpen the mid-range (0.50–0.80) to spread detections across
           the 0–100 scale more visually useful than raw * 100
        3. Map 0.0 → 0, 1.0 → 100 exactly

    The curve:
        [0.00, 0.30) → linear 0–20   (low-confidence compression)
        [0.30, 0.50) → linear 20–40  (below-threshold region)
        [0.50, 0.70) → linear 40–65  (moderate confidence)
        [0.70, 0.85) → linear 65–82  (good confidence)
        [0.85, 1.00] → linear 82–100 (high-confidence expansion)

    This choice is arbitrary in the absence of calibration data and is
    documented as PROVISIONAL. It should be replaced with statistically
    learned calibration once a labelled validation set exists.

Accuracy claims: NONE. This layer makes no accuracy claims.
"""

from __future__ import annotations

from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Piecewise linear calibration segments.
# Each entry: (raw_low, raw_high, cal_low, cal_high)
# ---------------------------------------------------------------------------
_CALIBRATION_SEGMENTS: Tuple[Tuple[float, float, float, float], ...] = (
    (0.00, 0.30, 0.0, 20.0),
    (0.30, 0.50, 20.0, 40.0),
    (0.50, 0.70, 40.0, 65.0),
    (0.70, 0.85, 65.0, 82.0),
    (0.85, 1.00, 82.0, 100.0),
)

CONFIDENCE_METHOD: str = "DETERMINISTIC_PIECEWISE_LINEAR_v1"
CONFIDENCE_METHOD_DESCRIPTION: str = (
    "Non-statistical deterministic piecewise linear rescaling. "
    "Preserves monotonicity. Not Platt Scaling or Isotonic Regression. "
    "Replace with learned calibration once validation labels are available."
)


def calibrate_confidence(raw_confidence: float) -> int:
    """Convert raw model confidence [0.0, 1.0] to a deterministic
    presentation confidence score [0, 100].

    Args:
        raw_confidence: Raw model confidence in [0.0, 1.0].

    Returns:
        Integer calibrated confidence in [0, 100].

    Raises:
        ValueError: If raw_confidence is outside [0.0, 1.0].
    """
    if not (0.0 <= raw_confidence <= 1.0):
        raise ValueError(
            f"raw_confidence must be in [0.0, 1.0], got {raw_confidence!r}"
        )

    # Clamp to exact boundaries to handle floating-point edge cases
    raw = float(raw_confidence)
    raw = max(0.0, min(1.0, raw))

    # Find the matching segment and interpolate
    for r_lo, r_hi, c_lo, c_hi in _CALIBRATION_SEGMENTS:
        if r_lo <= raw <= r_hi:
            if r_hi == r_lo:
                calibrated = c_lo
            else:
                t = (raw - r_lo) / (r_hi - r_lo)
                calibrated = c_lo + t * (c_hi - c_lo)
            return round(int(calibrated))

    # Should be unreachable for valid input after clamping
    return 100 if raw >= 1.0 else 0


def calibrate_confidence_float(raw_confidence: float) -> float:
    """Same as calibrate_confidence() but returns a float [0.0, 100.0]
    for use in computations that need fractional precision.
    """
    if not (0.0 <= raw_confidence <= 1.0):
        raise ValueError(
            f"raw_confidence must be in [0.0, 1.0], got {raw_confidence!r}"
        )
    raw = float(max(0.0, min(1.0, raw_confidence)))
    for r_lo, r_hi, c_lo, c_hi in _CALIBRATION_SEGMENTS:
        if r_lo <= raw <= r_hi:
            if r_hi == r_lo:
                return float(c_lo)
            t = (raw - r_lo) / (r_hi - r_lo)
            return round(c_lo + t * (c_hi - c_lo), 3)
    return 100.0 if raw >= 1.0 else 0.0


def is_monotonic() -> bool:
    """Verify that the calibration curve is strictly monotonically non-decreasing
    at a fine grid of points. Useful for CI sanity checks.
    """
    import math
    N = 1000
    prev = calibrate_confidence_float(0.0)
    for i in range(1, N + 1):
        raw = i / N
        cal = calibrate_confidence_float(min(raw, 1.0))
        if cal < prev - 1e-9:
            return False
        prev = cal
    return True
