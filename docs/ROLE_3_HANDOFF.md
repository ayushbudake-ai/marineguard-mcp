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
| Production pipeline integration (`ImageDetectionPipeline`) | ✅ |
| API integration (`/detect` & `/detect/side-scan`) | ✅ |
| MCP integration (`MarineGuardMCPServer`) | ✅ |
| Firewall audited & retained | ✅ |
| SSS 0 -> 29 taxonomy verified | ✅ |
| Role 3 targeted tests (75 pass) | ✅ |
| Full regression pass (150 pass, 0 fail) | ✅ |
| Documentation complete | ✅ |
| Git diff reviewed | ✅ |

---

## Files Created & Modified

### Implementation Files Created

| File | Purpose |
|------|---------|
| `marineguard/detection/confidence.py` | Deterministic piecewise linear confidence presentation mapping |
| `marineguard/detection/filtering.py` | False-positive filtering with per-detection reasons |
| `marineguard/detection/evidence.py` | Explainability / evidence records |

### Implementation Files Modified

| File | Changes |
|------|---------|
| `marineguard/detection/pipeline.py` | Integrated `DetectionFilter` into live `ImageDetectionPipeline.process()` |
| `marineguard/detection/schema.py` | Added `role3_summary` and `all_detections` to `DetectionResult` and `calibrated_confidence` to `Detection.to_dict()` |
| `marineguard/api/app.py` | Wired Role 3 filtering into `/detect/side-scan` endpoint (optical auto-integrated via pipeline) |
| `marineguard/mcp_server.py` | Integrated filtering in `detect_side_scan_waterfall` tool and tracer logging |
| `marineguard/trace/tracer.py` | Added `log_detection_filtering()` to `ExplainableTracer` |
| `marineguard/trace/evidence_overlay.py` | Added `format_detection_evidence_card()` and HTML formatting |

### Test Files

| File | Tests |
|------|-------|
| `tests/test_confidence.py` | 20 tests for confidence processing & boundaries |
| `tests/test_filtering.py` | 30 tests for filtering rules across modalities |
| `tests/test_evidence.py` | 13 tests for explainability cards & summaries |
| `tests/test_role3_production_integration.py` | 12 integration tests (TEST A through TEST J, API, MCP) |

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
python -m pytest tests/test_confidence.py tests/test_filtering.py tests/test_evidence.py tests/test_role3_production_integration.py -v
75 passed, 0 failed in 9.62s
```

All standard integration tests (TEST A through TEST J) passed:
- TEST A: Empty detections -> safe empty result
- TEST B: Valid detection -> accepted, raw confidence preserved, presentation score present, evidence present
- TEST C: Low confidence -> rejected with LOW_CONFIDENCE, evidence contains reason
- TEST D: Zero area -> rejected with ZERO_AREA_BBOX
- TEST E: Invalid bbox -> rejected with INVALID_BBOX
- TEST F: Out of bounds -> rejected with OUT_OF_BOUNDS
- TEST G: Extreme aspect ratio -> rejected with EXTREME_ASPECT
- TEST H: Confidence boundary values & monotonicity verified
- TEST I: Production ImageDetectionPipeline execution verified
- TEST J: Real SSS ML model -> MarineGuard class mapping 0 -> 29 -> Role 3 filtering -> evidence verified

### Full Regression

```
python -m pytest -q
150 passed, 2 skipped, 2 warnings in 50.75s
```

Role 2 baseline: **66 passed, 2 skipped**  
Role 3 result: **150 passed** (84 new Role 3 tests + 66 baseline), **2 skipped** (optional ONNX local weight checkpoints), **0 failed**.

---

## Firewall Status

**RETAINED — NOT REMOVED**
- **Reason:** `marineguard/firewall/` (`MissionFirewallPolicy`) is actively imported and invoked by `marineguard/mcp_server.py` (in `request_inspection_dive`) and `marineguard/exporters/pdf_report.py`.
- Deleting the firewall would break the MCP server dive tool and report generation.
- Role 3 detection filtering is fully decoupled from firewall mission controls.
- All firewall tests in `tests/test_firewall.py` continue to pass cleanly.

---

## Production Pipeline Integration Status

**CONNECTED & VERIFIED**
- `ImageDetectionPipeline` in `marineguard/detection/pipeline.py` directly executes `DetectionFilter` downstream of `PostProcessor`.
- Produces a fully backward-compatible `DetectionResult` with:
  - `.detections`: Accepted detections with preserved raw model confidence (`det.confidence`) and calibrated 0–100 score (`det.metadata["calibrated_confidence"]`).
  - `.role3_summary`: Counts of raw, accepted, and rejected detections, threshold, and confidence method.
  - `.all_detections`: Full list of accepted and rejected candidates with explicit rejection rules and reasons.
- `marineguard/trace/tracer.py` (`ExplainableTracer`) and `evidence_overlay.py` (`EvidenceOverlayFormatter`) are augmented with Role 3 detection filtering trace logging and evidence card generation.

---

## API Status

**INTEGRATED & VERIFIED**
- The FastAPI `/detect` endpoint runs `pipeline.process(content)` and returns `result.to_api_dict()`, which exposes `count`, `detections` (with `confidence` and `calibrated_confidence`), `role3_summary`, and `all_detections`.
- The `/detect/side-scan` endpoint filters CA-CFAR acoustic candidates through `filter_detection_result()` and returns the enriched schema.
- All existing API tests pass unchanged.

---

## MCP Status

**INTEGRATED & VERIFIED**
- `marineguard/mcp_server.py`:
  - `detect_marine_debris` calls `self.detection_pipeline.process()`, running live Role 3 filtering and calibration.
  - `detect_side_scan_waterfall` calls `filter_detection_result()` on CA-CFAR candidates.
  - Both tools log trace events via `ExplainableTracer.log_detection_filtering()`.

---

## Sonar Domain Heuristics Status

1. **Acoustic Shadow-Ratio:**
   - **NOT SCIENTIFICALLY SUPPORTED** on raw 2D pixel waterfall matrices without calibrated slant-range sonar geometry and grazing angles.
   - Optional metadata passthrough (`det.metadata["acoustic_shadow_ratio"]`) is supported without fabricating fake values.
2. **Rock-Cluster Suppression:**
   - **NOT SUPPORTED BY DATA**: The dataset contains no geological rock or seafloor clutter annotations.
   - Extensible architecture is maintained without fabricating rock classifications.

---

## Known Limitations

1. **No statistical calibration**: The confidence calibration is deterministic presentation mapping (`DETERMINISTIC_PIECEWISE_LINEAR_v1`). Statistical ECE cannot be computed without a labeled validation dataset.
2. **Synthetic evaluation only**: Before/after evaluation uses a constructed 10-detection regression test. Real FPR, precision, and recall are **NOT MEASURED** because no annotated ground-truth evaluation set is available.
3. **No temporal consistency filter**: Temporal tracking is not supported by the upstream detector layers.
4. **Provisional default threshold**: 0.30 is an operational default.

---

## Taxonomy Preservation

- SSS mapping: native class 0 → MarineGuard class 29 = `net` ✅  
- CA-CFAR: class_id 27 = `unknown-object` ✅  
- Optical taxonomy: 50-class MarineGuard taxonomy preserved unchanged ✅
