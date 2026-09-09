# Role 3 Confidence Calibration

**Project:** MarineGuard MCP  
**Role:** Role 3  
**Module:** `marineguard/detection/confidence.py`  
**Date:** 2026-09-09

---

## Summary

Role 3 adds a **calibrated_confidence** (0–100) to each detection alongside
the preserved **raw_confidence** (0.0–1.0) from the Role 2 detector.

---

## Preserved Field

```python
Detection.confidence  # UNCHANGED — raw model confidence [0.0, 1.0]
```

This field is **never modified**. Role 3 reads it and adds additional fields.

---

## New Field

```python
FilteredDetection.calibrated_confidence  # int [0, 100]
FilteredDetection.confidence_method      # str: method name
```

---

## Method: DETERMINISTIC_PIECEWISE_LINEAR_v1

### Classification

**NOT** statistical probability calibration.  
**NOT** Platt Scaling.  
**NOT** Isotonic Regression.  
**IS** a deterministic piecewise linear rescaling.

### Why This Method

No calibration dataset exists for this project. Collecting one would require:
- Labelled images with known ground truth
- Multiple model score bins
- Sufficient samples per bin for reliable histogram counts

Without this data, any statistical calibration claim would be fabricated.

The chosen method is a transparent deterministic transformation that:
1. Maps [0.0, 1.0] → [0, 100] with no discontinuities
2. Is strictly monotonically non-decreasing
3. Is fully documented and reproducible
4. Can be replaced with learned calibration in a future role

### Curve Definition

| Raw Range | Calibrated Range | Description |
|-----------|-----------------|-------------|
| [0.00, 0.30) | [0, 20] | Low-confidence compression |
| [0.30, 0.50) | [20, 40] | Below-threshold region |
| [0.50, 0.70) | [40, 65] | Moderate confidence |
| [0.70, 0.85) | [65, 82] | Good confidence |
| [0.85, 1.00] | [82, 100] | High-confidence expansion |

### Properties

| Property | Status |
|---------|--------|
| Monotone non-decreasing | ✅ VERIFIED (test + utility function) |
| 0.0 → 0 | ✅ |
| 1.0 → 100 | ✅ |
| Deterministic | ✅ |
| Statistically calibrated | ❌ NOT applicable |
| Platt Scaling | ❌ NOT applicable |
| Isotonic Regression | ❌ NOT applicable |

### Validation

```
python -m pytest tests/test_confidence.py -v
# 22 tests, all pass
```

Monotonicity verified over 1000 uniformly spaced points (0.0–1.0).

---

## Future Work

When a labelled validation set is available:

1. Collect raw model scores and ground-truth labels
2. Fit Platt Scaling or Isotonic Regression
3. Replace `_CALIBRATION_SEGMENTS` with the learned calibration
4. Update `CONFIDENCE_METHOD` to reflect the new method
5. Report Expected Calibration Error (ECE) and Reliability Diagram

---

## Provisional Status

The current threshold analysis (from `scripts/evaluate_filtering.py`) uses the
default threshold of 0.30 as a **PROVISIONAL** operational setting.

A scientifically justified production threshold requires:
- A labelled evaluation set
- Precision/recall curves across thresholds
- Domain expert review of acceptable FPR

This is documented explicitly in the evaluation script and handoff.
