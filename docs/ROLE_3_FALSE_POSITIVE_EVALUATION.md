# Role 3 False-Positive Evaluation

**Project:** MarineGuard MCP  
**Role:** Role 3  
**Module:** `marineguard/detection/filtering.py`, `scripts/evaluate_filtering.py`  
**Date:** 2026-09-09

---

## Scientific Honesty Statement

**False-positive rate (FPR), precision, recall, and F1 are NOT MEASURED.**

These metrics cannot be computed because:
1. No labelled evaluation dataset exists in this repository.
2. The CA-CFAR detections are class-agnostic acoustic anomalies with no object-level ground truth.
3. The optical model test infrastructure uses `MockDetector` (not real inference + real labels).

Claiming FPR reduction without labelled ground truth would be scientifically dishonest
and violates the Role 3 specification.

What IS reported: deterministic operational metrics from a synthetic test set.

---

## Filtering Rules

| Rule Name | Reason Code | Condition | Modality |
|-----------|------------|-----------|---------|
| Confidence threshold | `LOW_CONFIDENCE` | `confidence < threshold` | All |
| BBox validity | `INVALID_BBOX` | len != 4 or NaN/Inf in coords | All |
| Zero area | `ZERO_AREA_BBOX` | width=0 or height=0 | All |
| Minimum area | `TINY_BBOX` | area < `min_area_px2` (default 4px²) | All |
| Image bounds | `OUT_OF_BOUNDS` | bbox fully outside image | All (when dims known) |
| Aspect ratio | `EXTREME_ASPECT` | max(w/h, h/w) > `max_aspect_ratio` (default 50) | All |
| CFAR geometry | `CFAR_GEOMETRY` | class_id=27 AND area < 16px² OR aspect > 30 | CA-CFAR only |
| Bathymetry geometry | `BATHYMETRY_GEOMETRY` | source=bathymetry AND area < min | Bathymetry only |

---

## Operational Evaluation (MEASURED)

Evaluation uses a **synthetic test set** of 10 detections constructed to exercise
all filter rules. No real labelled data is used.

### Synthetic Test Set

| # | Class | Confidence | BBox | Sensor | Expected |
|---|-------|-----------|------|--------|---------|
| 1 | plastic-bottle | 0.92 | valid | optical | ACCEPT |
| 2 | tire | 0.67 | valid | optical | ACCEPT |
| 3 | can | 0.18 | valid | optical | REJECT (LOW_CONFIDENCE @ t=0.30) |
| 4 | net (class_id=29) | 0.78 | valid | side_scan | ACCEPT |
| 5 | unknown-object (class_id=27) | 0.61 | valid area | ca_cfar | ACCEPT |
| 6 | unknown-object (class_id=27) | 0.55 | tiny area | ca_cfar | REJECT (CFAR_GEOMETRY) |
| 7 | plastic-bag | 0.75 | zero area | optical | REJECT (ZERO_AREA_BBOX) |
| 8 | rope | 0.70 | extreme aspect | optical | REJECT (EXTREME_ASPECT) |
| 9 | bottle | 0.80 | fully OOB | optical | REJECT (OUT_OF_BOUNDS) |
| 10 | ghost-net | 0.50 | valid | optical | ACCEPT |

### Results at Default Threshold (0.30)

```
Raw detections   : 10
Accepted         : 5
Rejected         : 5
  LOW_CONFIDENCE : 1
  CFAR_GEOMETRY  : 1
  ZERO_AREA_BBOX : 1
  EXTREME_ASPECT : 1
  OUT_OF_BOUNDS  : 1
```

### Threshold Sweep

| Threshold | Raw | Accepted | Rejected |
|-----------|-----|---------|---------|
| 0.10      | 10  | 6       | 4       |
| 0.20      | 10  | 5       | 5       |
| 0.30      | 10  | 5       | 5       |
| 0.40      | 10  | 5       | 5       |
| 0.50      | 10  | 5       | 5       |
| 0.60      | 10  | 4       | 6       |
| 0.70      | 10  | 2       | 8       |
| 0.80      | 10  | 1       | 9       |
| 0.90      | 10  | 1       | 9       |

**Precision / Recall / F1 / FPR: NOT MEASURED** (no ground truth)

---

## Default Threshold Selection

**Default threshold: 0.30 — PROVISIONAL**

Rationale:
- The Role 2 `PostProcessor` primary threshold (0.50) is applied upstream.
- Role 3's secondary threshold (0.30) adds a safety net for detections
  that may have bypassed the primary (e.g., when PostProcessor is not run).
- 0.30 is not scientifically optimised; it is a conservative default.

To select a production threshold scientifically:
1. Collect a labelled evaluation set with verified TP/FP labels
2. Run `scripts/evaluate_filtering.py --all-thresholds` with ground truth enabled
3. Plot Precision-Recall curve
4. Select threshold based on domain-acceptable FPR

---

## Reproducibility

```bash
python scripts/evaluate_filtering.py --all-thresholds --verbose
python scripts/evaluate_filtering.py --threshold 0.30 --output-json results.json
```

All results are deterministic. Same inputs produce identical outputs.
