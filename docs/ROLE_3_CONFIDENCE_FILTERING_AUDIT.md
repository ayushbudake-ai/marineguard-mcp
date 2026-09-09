# Role 3 Confidence Filtering Audit

**Project:** MarineGuard MCP  
**Role:** Role 3 — Confidence Scoring, False-Positive Suppression, Noise Filtering & Explainability  
**Date:** 2026-09-09  
**Status:** COMPLETE

---

## 1. Repository Audit

### Repository State at Role 3 Start

- Branch: `main`
- Modified files: `AGENTS.md` only (uncommitted user edit)
- Role 2 baseline: 66 passed, 2 skipped

### Architecture Discovered

```
marineguard/
├── detection/
│   ├── schema.py          # Detection, DetectionResult (Role 2)
│   ├── detector.py        # BaseDetector, MockDetector, YOLODetector (Role 2)
│   ├── pipeline.py        # ImageDetectionPipeline (Role 2)
│   ├── postprocessing.py  # PostProcessor — confidence threshold + bbox clipping (Role 2)
│   ├── optical.py         # OpticalDetector (Role 2)
│   ├── bathymetry.py      # BathymetryDetector (Role 2)
│   ├── side_scan.py       # SideScanDetector + CA-CFAR (Role 2)
│   ├── fusion.py          # MultiSensorFusionEngine (Role 2)
│   ├── confidence.py      # [NEW Role 3] confidence calibration
│   ├── filtering.py       # [NEW Role 3] false-positive filtering
│   └── evidence.py        # [NEW Role 3] explainability
├── firewall/              # AUV mission safety firewall (ACTIVE — not obsolete)
│   ├── policy.py
│   ├── operator_ui.py
│   └── risk_taxonomy.py
├── trace/
│   ├── tracer.py          # ExplainableTracer (TraceEvent domain)
│   └── evidence_overlay.py # EvidenceOverlayFormatter (ClassifiedTarget domain)
└── api/app.py             # FastAPI REST service (Role 2)
```

---

## 2. Detection Schema

### Detection (Role 2)

```python
Detection:
    class_name: str         # canonical class name
    class_id: Optional[int] # numeric taxonomy ID
    confidence: float       # raw model confidence [0.0, 1.0]
    bbox: List[float]       # [x1, y1, x2, y2] pixel coordinates
    segmentation: Optional  # polygon contour if segmentation model
    metadata: Dict          # source_sensor, engine, mock, etc.
```

### DetectionResult (Role 2)

```python
DetectionResult:
    detections: List[Detection]
    count: int
    image_width: Optional[int]
    image_height: Optional[int]
    inference_time_ms: Optional[float]
    model_name: Optional[str]
    status: str             # "SUCCESS"
```

---

## 3. Firewall Audit

**Location:** `marineguard/firewall/`  
**Decision: RETAINED — NOT OBSOLETE**

The firewall is an AUV **mission safety layer** (not a detection post-processor).  
It enforces safety policies on AUV actions (course changes, battery consumption, comms).  
It has live test coverage in `tests/test_firewall.py`.  
It imports from `marineguard.schemas` (Action, MissionContext, FirewallDecision, RiskLevel).  
It is referenced by `marineguard/mcp_server.py`.

**The firewall is unrelated to Role 3 confidence/filtering and must be preserved.**

---

## 4. Role 3 Insertion Point

Role 3 is implemented **downstream** of Role 2 `PostProcessor`:

```
Role 2 Detector
↓
DetectionResult
↓
[Role 2 PostProcessor: primary confidence threshold + bbox clipping]
↓
DetectionResult
↓
[Role 3 DetectionFilter: secondary confidence + geometry + modality rules]
↓
FilteredResult
↓
API / MCP / Fusion / Annotation
```

Role 3 does NOT modify `PostProcessor` or any Role 2 component.

---

## 5. Modality Verification

| Modality | Class ID | Class Name | Role 3 Behaviour |
|----------|----------|------------|-----------------|
| Optical  | Various  | e.g., plastic-bottle | Generic rules (confidence, bbox, area, aspect) |
| SSS YOLO | 29       | net        | Generic rules; no CFAR geometry |
| CA-CFAR  | 27       | unknown-object | Generic rules + CFAR_GEOMETRY (min_area=16px²) |
| Bathymetry | Various | Anomaly type | Generic rules + BATHYMETRY_GEOMETRY |

SSS taxonomy mapping preserved:
- Native SSS class 0 → MarineGuard class 29 = `net` ✅
- CA-CFAR → class 27 = `unknown-object` ✅

---

## 6. API Compatibility

- `FilteredResult.to_api_dict()` returns `detections` + `count` for **accepted** detections only
- Adds backward-compatible `role3_summary` key
- Existing API tests (`test_api.py`) continue to use `to_api_dict()` from `DetectionResult` directly and are unaffected
- New Role 3 API output is additive (no breaking changes)

---

## 7. MCP Compatibility

`marineguard/mcp_server.py` was not modified. Role 3 modules are importable and can be called from MCP tools when integrated. The `FilteredResult.to_api_dict()` output is JSON-serializable.
