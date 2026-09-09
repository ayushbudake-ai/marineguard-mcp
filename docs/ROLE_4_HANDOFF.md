# Role 4 Handoff — Reporting, Geotagging & GIS Exporters

**Project:** MarineGuard MCP  
**Role:** Role 4 — Reporting, Geotagging & GIS Exporters  
**Status:** COMPLETE  
**Date:** 2026-09-09  
**Upstream:** Role 3 commit `eca7f6c8f380815f06161ebeaea30c10e55d6ae2`

---

## 1. Role 4 Purpose

Role 4 is the reporting and export layer of the MarineGuard detection pipeline.

It consumes the frozen **Role 3 DetectionResult** and produces:

- **GeoJSON** — standard GIS FeatureCollection for spatial analysis tools
- **S-100-inspired JSON** — partial hydrographic-inspired catalog
- **PDF** — professional inspection/detection report
- **CSV / JSON** — structured tabular export for data analysis

Pipeline position:

```
Optical / SSS data
      ↓
Role 1 (data/preprocessing)
      ↓
Role 2 (AI inference)
      ↓
Role 3 (confidence filtering + explainability)
      ↓
DetectionResult
      ↓
Role 4 (Reporting, Geotagging, Export)
      ↓
GeoJSON / S-100 / PDF / CSV / JSON
```

---

## 2. DetectionResult Input Contract

Role 4 consumes `marineguard.detection.schema.DetectionResult`:

| Field | Type | Description |
|---|---|---|
| `detections` | `List[Detection]` | **Accepted** detections only |
| `count` | `int` | Number of accepted detections |
| `role3_summary` | `Optional[Dict]` | raw_count, accepted_count, rejected_count, threshold, method |
| `all_detections` | `Optional[List[Dict]]` | All detections (accepted + rejected) with Role 3 metadata |
| `image_width` | `Optional[int]` | Input image width in pixels |
| `image_height` | `Optional[int]` | Input image height in pixels |
| `model_name` | `Optional[str]` | Model identifier |

Each `Detection`:

| Field | Type | Description |
|---|---|---|
| `class_name` | `str` | MarineGuard class name |
| `class_id` | `Optional[int]` | MarineGuard numeric class ID |
| `confidence` | `float` | Raw model confidence [0.0–1.0] |
| `bbox` | `List[float]` | [x1, y1, x2, y2] in **pixel coordinates** |
| `metadata` | `Dict` | May contain: `source_sensor`, `calibrated_confidence`, `role3`, `latitude`, `longitude` |

---

## 3. Geotagging

### Behavior

`marineguard/exporters/geotagging.py` — `Geotagger` class.

Coordinates are read **only from actual available data**. Sources (priority order):

1. `detection.metadata["latitude"]` + `detection.metadata["longitude"]`
2. `detection.metadata["coordinates"]["lat"]` + `["lon"]`
3. External `mission_metadata` dict (if caller provides it from real instrument data)

### Null behavior

If no real coordinates are available:

```python
latitude = None
longitude = None
```

**No coordinates are ever fabricated.**  
Pixel bounding boxes are NOT geographic coordinates and are NEVER converted.

### Current production state

The current `DetectionResult` pipeline does not inject GPS coordinates — all
production exports will have `latitude=null`, `longitude=null`. This is correct
behavior. If future data sources provide real coordinates via `metadata`, they
will be picked up automatically.

---

## 4. GeoJSON Structure

**File:** `marineguard/exporters/geojson_export.py`

Standard RFC 7946 GeoJSON FeatureCollection.

```json
{
  "type": "FeatureCollection",
  "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
  "features": [
    {
      "type": "Feature",
      "geometry": null,
      "properties": {
        "detection_id": 0,
        "class_id": 0,
        "class_name": "bottle",
        "raw_confidence": 0.88,
        "calibrated_confidence": 85,
        "source_sensor": "optical",
        "bbox": [10.0, 20.0, 110.0, 120.0],
        "filter_status": "accepted",
        "latitude": null,
        "longitude": null
      }
    }
  ],
  "properties": {
    "coordinate_note": "...",
    "accepted_count": 1,
    "rejected_audit": [...]
  }
}
```

**Coordinate order:** `[longitude, latitude]` (GeoJSON/RFC 7946 §3.1.1 standard).

**Null geometry:** A Feature with `geometry: null` is valid per RFC 7946 §3.2.
It preserves detection properties without fabricating a location.

**CRS assumption:** WGS84 geographic coordinates are assumed when coordinates
are present. No conversion is performed.

**Rejected detections:** Rejected detections appear in `properties.rejected_audit`
for audit purposes. They are NEVER mixed into the `features` list.

---

## 5. S-100/S-124 Exporter

**File:** `marineguard/exporters/s100_export.py`

### ⚠️ PARTIAL IMPLEMENTATION — NOT CERTIFIED

This exporter uses an S-100-inspired JSON structure. It is:

- **NOT** a certified IHO S-100 product
- **NOT** a certified S-124 navigational warning product  
- **NOT** claiming hydrographic survey accuracy
- **NOT** claiming navigational safety compliance

### Supported fields

| Field | Available |
|---|---|
| `classId` | ✅ |
| `className` | ✅ |
| `rawConfidence` | ✅ |
| `calibratedConfidence` | ✅ |
| `sourceSensor` | ✅ |
| `bboxPixels` | ✅ |
| `filterStatus` | ✅ |
| `position.latitude` | ✅ if in metadata |
| `position.longitude` | ✅ if in metadata |

### Unsupported fields (null — NOT fabricated)

| Field | Status |
|---|---|
| `depthMeters` | null — not in data pipeline |
| `bathymetry` | null — not in data pipeline |
| `horizontalAccuracyMeters` | null — not in data pipeline |
| `qualityOfSounding` | null — not in data pipeline |
| `navigationTrack` | null — not in data pipeline |
| `vesselInfo` | null — not in data pipeline |
| `s124HazardAttributes` | null — not in data pipeline |

---

## 6. PDF Report

**File:** `marineguard/exporters/pdf_report.py`

Uses `reportlab` (already in requirements.txt). Falls back to plain `.txt` if
reportlab layout fails.

### Report sections

1. **Header** — title, mission ID, generation timestamp
2. **Detection Summary** — model, status, raw/accepted/rejected counts, threshold, image size, inference time
3. **Accepted Detections Table** — class, raw conf, calibrated conf, sensor, bbox, coordinates (or "unavailable")
4. **Rejected Detections Audit Table** — class, raw conf, calibrated conf, rejection rule, reason
5. **Notes & Limitations** — scope, coordinate handling, sensor scope, rejection rules

### Not included

- Temperature, battery, depth sensor, IMU, compass, gyroscope
- Live GPS hardware, live telemetry, vehicle health

### Coordinate handling

If coordinates are unavailable: report shows `"unavailable"`. No fake values.

---

## 7. CSV / JSON Tabular Export

**File:** `marineguard/exporters/tabular_export.py`

### CSV fields (in order)

```
detection_id, class_id, class_name, raw_confidence, calibrated_confidence,
source_sensor, bbox_x1, bbox_y1, bbox_x2, bbox_y2, latitude, longitude,
timestamp, filter_status, rejection_rule, rejection_reason
```

- Null values → empty string in CSV, `null` in JSON
- Accepted detections are the primary output (filter_status="accepted")
- Rejected detections can be included as audit rows (filter_status="rejected")

---

## 8. Sensor Scope

Only two sensor modalities are supported:

| Sensor | Supported |
|---|---|
| Optical camera | ✅ |
| Side-scan sonar (SSS) | ✅ |

### SSS Taxonomy (preserved from Role 2/3)

| Native SSS class | MarineGuard class ID | MarineGuard class name |
|---|---|---|
| class 0 | 29 | net |
| CA-CFAR anomaly | 27 | unknown-object |

Not supported (out of scope): temperature, battery, depth sensor, IMU, compass,
accelerometer, gyroscope, motor telemetry, water-quality sensors, live AUV navigation.

---

## 9. MCP Integration

**New tool:** `export_detection_result()` in `marineguard/mcp_server.py`

Accepts a DetectionResult dict and exports to geojson / s100 / pdf / csv / json.

**Preserved:** `export_report()` for backward compatibility with `ClassifiedTarget`
workflow used by `marine_debris_survey()`.

---

## 10. API Integration

**New endpoint:** `POST /export` in `marineguard/api/app.py`

Accepts DetectionResult JSON body + `format` query param.  
Returns exported data. No existing endpoints modified.

---

## 11. Data Integrity Guarantees

- **No fabricated GPS** — coordinates only from real metadata
- **No fabricated depth** — depth fields are null
- **No fabricated telemetry** — no vehicle health fields
- **No fabricated temperature** — excluded entirely
- **No fabricated battery** — excluded entirely
- **No fabricated mission metadata** — only fields from actual data

---

## 12. Files Created / Modified

### New files

| File | Purpose |
|---|---|
| `marineguard/exporters/geotagging.py` | Geotagger — real coordinate extraction |
| `marineguard/exporters/tabular_export.py` | CSV/JSON tabular exporter |
| `marineguard/exporters/__init__.py` | Exporters package init |
| `tests/test_exporters.py` | Comprehensive exporter tests |
| `docs/ROLE_4_HANDOFF.md` | This document |

### Modified files

| File | Changes |
|---|---|
| `marineguard/exporters/geojson_export.py` | Rewritten for DetectionResult (was ClassifiedTarget) |
| `marineguard/exporters/pdf_report.py` | Rewritten for DetectionResult (was ClassifiedTarget) |
| `marineguard/exporters/s100_export.py` | Rewritten for DetectionResult (was ClassifiedTarget, fake fields) |
| `marineguard/mcp_server.py` | Added `export_detection_result()` MCP tool + imports |
| `marineguard/api/app.py` | Added `POST /export` endpoint + imports |

### Frozen files (NOT modified)

- `marineguard/detection/schema.py`
- `marineguard/detection/filtering.py`
- `marineguard/detection/pipeline.py`
- `marineguard/detection/evidence.py`
- `marineguard/detection/confidence.py`
- All Role 1 / Role 2 / Role 3 code

---

## 13. Testing

```bash
# Role 4 targeted tests
python -m pytest tests/test_exporters.py -v

# Role 3 regression
python -m pytest tests/test_role3_production_integration.py -q

# SSS regression
python -m pytest tests/test_side_scan.py tests/test_side_scan_model.py -q

# Full regression
python -m pytest -q
```

---

## 14. Known Limitations (Non-Blocking)

1. **No real GPS in current pipeline** — all production exports have null coordinates.
   This is correct behavior, not a bug. If real coordinate data is added to
   detection metadata in future, geotagging will pick it up automatically.

2. **S-100 is partial** — only detection-level attributes are exported. Full
   S-100/S-124 compliance would require bathymetry, navigation data, and
   hydrographic survey geometry not present in this data pipeline.

3. **PDF requires reportlab** — if reportlab is unavailable or a layout error
   occurs, a plain-text fallback is produced automatically.

4. **No ground-truth precision/recall** — Role 3 confidence calibration is a
   deterministic mapping, not statistically validated (inherited limitation from
   Role 3).
