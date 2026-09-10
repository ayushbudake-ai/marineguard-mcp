# 🛡️ Post-Processing & Confidence Filtering Layer

This package contains confidence calibration, domain-specific sonar filtering heuristics, and visual explainability tools.

## Modules

- **`confidence_filter.py`**: Heuristic false-positive filtering using acoustic shadow ratios and silhouette aspect ratios.
- **`../compiler/filtering_layer.py`**: Accepted vs Rejected classification pipeline.
- **`../confidence.py`**: Platt scaling and Isotonic confidence calibration.
- **`../evidence.py`**: Forensic bounding-box crop extraction for the visual audit trail.
