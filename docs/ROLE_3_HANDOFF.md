# Role 3 Handoff

**Project:** MarineGuard MCP  
**Role:** Role 3 — Confidence Scoring, False-Positive Suppression, Noise Filtering & Explainability  
**Date:** 2026-09-09  
**Author:** Role 3 implementation

---

## Role 3 Status: COMPLETE

---

## Completed Work

| Item | Status |
|------|--------|
| Repository audit (Phase 1) | ✅ |
| Role 2 architecture understood (Phase 2) | ✅ |
| Role 3 design (Phase 3) | ✅ |
| Confidence processing implemented | ✅ |
| Filtering implemented | ✅ |
| Explainability implemented | ✅ |
| Evaluation script implemented | ✅ |
| Threshold analysis documented | ✅ |
| Modality verification (optical, SSS, CA-CFAR, bathymetry) | ✅ |
| Firewall audited | ✅ |
| API compatibility verified | ✅ |
| MCP compatibility verified | ✅ |
| Role 3 tests (63 pass) | ✅ |
| Full regression pass | ✅ |
| Documentation complete | ✅ |
| Git diff reviewed | ✅ |
| Role 3 commit created | ✅ |

---

## Files Created

### Implementation

| File | Purpose |
|------|---------|
| `marineguard/detection/confidence.py` | Deterministic piecewise linear confidence calibration |
| `marineguard/detection/filtering.py` | False-positive filtering with per-detection reasons |
| `marineguard/detection/evidence.py` | Explainability / evidence records |

### Tests

| File | Tests |
|------|-------|
| `tests/test_confidence.py` | 22 tests for confidence processing |
| `tests/test_filtering.py` | 27 tests for filtering (all modalities) |
| `tests/test_evidence.py` | 14 tests for explainability |

### Scripts

| File | Purpose |
|------|---------|
| `scripts/evaluate_filtering.py` | Before/after evaluation script |

### Documentation

| File | Purpose |
|------|---------|
| `docs/ROLE_3_CONFIDENCE_FILTERING_AUDIT.md` | Repository audit and architecture |
| `docs/ROLE_3_CONFIDENCE_CALIBRATION.md` | Confidence method documentation |
| `docs/ROLE_3_FALSE_POSITIVE_EVALUATION.md` | Evaluation results and threshold analysis |
| `docs/ROLE_3_HANDOFF.md` | This document |

---

## Confidence Method

**Method:** DETERMINISTIC_PIECEWISE_LINEAR_v1

**NOT** statistical probability calibration.  
**IS** a deterministic monotonic rescaling of raw confidence [0.0–1.0] to calibrated [0–100].

### Curve

| Raw Range | Calibrated Range |
|-----------|-----------------|
| [0.00, 0.30) | [0, 20] |
| [0.30, 0.50) | [20, 40] |
| [0.50, 0.70) | [40, 65] |
| [0.70, 0.85) | [65, 82] |
| [0.85, 1.00] | [82, 100] |

Properties: monotone ✅, deterministic ✅, 0→0 ✅, 1→100 ✅.

Raw model confidence is preserved in `FilteredDetection.raw_confidence` unchanged.

---

## Filtering Rules

| Reason Code | Condition | Modality |
|-------------|-----------|---------|
| `LOW_CONFIDENCE` | confidence < threshold | All |
| `INVALID_BBOX` | len != 4 or NaN/Inf | All |
| `ZERO_AREA_BBOX` | width=0 or height=0 | All |
| `TINY_BBOX` | area < 4px² | All |
| `OUT_OF_BOUNDS` | bbox fully outside image | All (when dims known) |
| `EXTREME_ASPECT` | max ratio > 50 | All |
| `CFAR_GEOMETRY` | class_id=27 and area < 16px² or aspect > 30 | CA-CFAR only |
| `BATHYMETRY_GEOMETRY` | source=bathymetry and area < threshold | Bathymetry only |

---

## Explainability

Every `FilteredDetection` contains:
- `raw_confidence` — original model score
- `calibrated_confidence` — 0–100 presentation score
- `confidence_method` — method identifier
- `filter_status` — "accepted" | "rejected"
- `filter_reason` — machine-readable rejection reason (None if accepted)
- `applied_rules` — ordered list of rules checked
- `rejection_rule` — first rule that caused rejection

`DetectionEvidenceBuilder` produces `EvidenceRecord` objects with human/HTML formatting.

---

## Before/After Measurements (MEASURED — Synthetic Test Set)

```
BEFORE (Role 2 raw):
  Total: 10 synthetic detections
  Confidence range: 0.18–0.92

AFTER (Role 3, threshold=0.30):
  Accepted: 5
  Rejected: 5
    LOW_CONFIDENCE : 1
    CFAR_GEOMETRY  : 1
    ZERO_AREA_BBOX : 1
    EXTREME_ASPECT : 1
    OUT_OF_BOUNDS  : 1
```

**Precision / Recall / F1 / FPR: NOT MEASURED**  
Reason: No labelled ground-truth dataset available.

---

## Test Results

### Role 3 Targeted Tests

```
python -m pytest tests/test_confidence.py tests/test_filtering.py tests/test_evidence.py -v
63 passed, 0 failed
```

### Full Regression

```
python -m pytest -q
138 passed, 2 skipped, 2 warnings in 53.88s
```

Role 2 baseline: **66 passed, 2 skipped**  
Role 3 result: **138 passed** (75 base suite + 63 new Role 3 tests), **2 skipped** (test_optical_onnx_valid_image_inference, test_optical_onnx_annotation_with_segmentation)

---

## Firewall Status

**RETAINED — NOT REMOVED**

`marineguard/firewall/` is an AUV mission safety layer (action policy enforcement).
It is **not** a detection post-processor and is not obsolete.
Live tests in `tests/test_firewall.py` continue to pass.
No changes made to firewall code.

---

## API Status

**COMPATIBLE — NO BREAKING CHANGES**

- `FilteredResult.to_api_dict()` extends Role 2 format with additive `role3_summary` key
- `detections` + `count` keys remain backward-compatible (contain accepted dets only)
- All existing API tests (`tests/test_api.py`) pass unchanged

---

## MCP Status

**COMPATIBLE**

`marineguard/mcp_server.py` not modified. Role 3 modules can be integrated into MCP tools
when needed. All output is JSON-serializable.

---

## Known Limitations

1. **No statistical calibration**: The confidence calibration is deterministic/presentational only. Statistical ECE cannot be reported without labelled validation data.

2. **Synthetic evaluation only**: The before/after evaluation uses a constructed test set. Real FPR/precision/recall measurement requires labelled data.

3. **No temporal consistency filter**: The specification allows temporal consistency filtering "only if already supported by the repository". The video pipeline exists but provides no temporal tracking state, so this rule was not implemented.

4. **Default threshold is provisional**: The 0.30 secondary threshold is a conservative default, not scientifically optimised.

5. **MCP tool integration not automated**: Role 3 modules are available for use in MCP tools but no new MCP tools were added. MCP tool integration is a natural continuation for a future role.

---

## Remaining Work / Next Role

- Collect labelled evaluation data to enable true FPR/precision/recall measurement
- Replace deterministic calibration with Platt Scaling once calibration data exists
- Integrate `filter_detection_result()` into the MCP tool chain explicitly
- Add temporal consistency tracking to the video pipeline
- Select production confidence threshold based on domain expert review
- Integrate `FilteredResult` into the Streamlit demo UI

---

## Taxonomy Preservation

SSS mapping: native class 0 → MarineGuard class 29 = `net` ✅  
CA-CFAR: class_id 27 = `unknown-object` ✅  
No taxonomy changes made.
