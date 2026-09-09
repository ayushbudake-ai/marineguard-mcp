"""
Role 3 — False-Positive Filtering Layer for MarineGuard MCP

Consumes a DetectionResult (Role 2 output) and applies a set of
evidence-based deterministic rules to classify each Detection as
ACCEPTED or REJECTED, with a machine-readable reason.

Design principles:
    - Raw Detection objects are NEVER modified.
    - Filtering adds metadata; it does not drop records silently.
    - Every rule has a documented purpose, inputs, logic, and reason string.
    - Filtering is deterministic: same input → same output every time.
    - Role 2 PostProcessor confidence threshold is applied before this layer.
      Role 3 may apply a SECONDARY confidence threshold (default=0.30) to
      catch any additional low-confidence detections that slipped through.

Filter Status Values:
    "accepted"  — detection passed all filters
    "rejected"  — detection failed at least one filter

Rejection Reasons (machine-readable):
    LOW_CONFIDENCE      — confidence below threshold
    INVALID_BBOX        — bbox has fewer than 4 coordinates or NaN/Inf values
    ZERO_AREA_BBOX      — bbox encodes a point or line (zero width or height)
    OUT_OF_BOUNDS       — bbox fully outside image boundary (when dims known)
    TINY_BBOX           — bbox area below minimum pixels² threshold
    EXTREME_ASPECT      — aspect ratio exceeds maximum (e.g., >50:1)
    CFAR_GEOMETRY       — CA-CFAR bbox fails sonar-specific geometry rules
    BATHYMETRY_GEOMETRY — bathymetry bbox fails depth-anomaly geometry rules

Modality detection:
    Source sensor is read from Detection.metadata["source_sensor"] when present,
    or from the model_name of the DetectionResult.
    CA-CFAR detections have class_id=27 (unknown-object).
    SSS net detections have class_id=29 (net).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.confidence import (
    calibrate_confidence,
    CONFIDENCE_METHOD,
)


# ---------------------------------------------------------------------------
# Filter result dataclass — wraps a Detection with Role 3 metadata
# ---------------------------------------------------------------------------

@dataclass
class FilteredDetection:
    """A Detection with Role 3 confidence and filter annotations.

    raw_detection is preserved unchanged. All Role 3 metadata is in
    the additional fields.
    """
    raw_detection: Detection
    raw_confidence: float
    calibrated_confidence: int          # 0–100
    confidence_method: str
    confidence_threshold: float
    filter_status: str                  # "accepted" | "rejected"
    filter_reason: Optional[str]        # None when accepted
    applied_rules: List[str]            # ordered list of rules that were checked
    rejection_rule: Optional[str]       # first rule that rejected, or None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict for API/MCP consumers.

        The original detection fields are embedded for convenience.
        """
        d = self.raw_detection.to_dict()
        d["role3"] = {
            "raw_confidence": round(self.raw_confidence, 6),
            "calibrated_confidence": self.calibrated_confidence,
            "confidence_method": self.confidence_method,
            "confidence_threshold": self.confidence_threshold,
            "filter_status": self.filter_status,
            "filter_reason": self.filter_reason,
            "applied_rules": self.applied_rules,
            "rejection_rule": self.rejection_rule,
        }
        return d


@dataclass
class FilteredResult:
    """Role 3 output: wraps original DetectionResult with per-detection
    filter annotations.
    """
    original_result: DetectionResult
    filtered_detections: List[FilteredDetection]
    confidence_threshold: float
    image_width: Optional[int] = None
    image_height: Optional[int] = None

    @property
    def accepted(self) -> List[FilteredDetection]:
        return [fd for fd in self.filtered_detections if fd.filter_status == "accepted"]

    @property
    def rejected(self) -> List[FilteredDetection]:
        return [fd for fd in self.filtered_detections if fd.filter_status == "rejected"]

    def to_api_dict(self) -> Dict[str, Any]:
        """Returns a backward-compatible API dict that extends the Role 2
        to_api_dict() format. Existing 'detections' and 'count' keys refer
        to ACCEPTED detections only (preserving Role 2 contract).
        New 'role3_summary' key is additive.
        """
        accepted_list = self.accepted
        detections_out = [fd.raw_detection.to_dict() for fd in accepted_list]

        res: Dict[str, Any] = {
            "detections": detections_out,
            "count": len(detections_out),
            "role3_summary": {
                "raw_count": len(self.filtered_detections),
                "accepted_count": len(accepted_list),
                "rejected_count": len(self.rejected),
                "confidence_threshold": self.confidence_threshold,
                "confidence_method": CONFIDENCE_METHOD,
            },
        }
        if self.image_width is not None:
            res["image_width"] = self.image_width
        if self.image_height is not None:
            res["image_height"] = self.image_height
        if self.original_result.inference_time_ms is not None:
            res["inference_time_ms"] = round(self.original_result.inference_time_ms, 2)
        return res

    def to_full_api_dict(self) -> Dict[str, Any]:
        """Returns full Role 3 metadata for each detection, including
        rejected detections with reasons.
        """
        res = self.to_api_dict()
        res["all_detections"] = [fd.to_dict() for fd in self.filtered_detections]
        return res


# ---------------------------------------------------------------------------
# Individual filter functions
# Each returns (passed: bool, reason: str | None)
# ---------------------------------------------------------------------------

def _check_confidence(
    det: Detection,
    threshold: float,
) -> tuple[bool, Optional[str]]:
    """Rule: LOW_CONFIDENCE — confidence must be >= threshold."""
    if not (0.0 <= det.confidence <= 1.0):
        return False, "LOW_CONFIDENCE"
    if det.confidence < threshold:
        return False, "LOW_CONFIDENCE"
    return True, None


def _check_bbox_valid(det: Detection) -> tuple[bool, Optional[str]]:
    """Rule: INVALID_BBOX — bbox must be a list of exactly 4 finite numbers."""
    bbox = det.bbox
    if len(bbox) != 4:
        return False, "INVALID_BBOX"
    for v in bbox:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return False, "INVALID_BBOX"
        if not math.isfinite(f):
            return False, "INVALID_BBOX"
    return True, None


def _check_bbox_positive_area(det: Detection) -> tuple[bool, Optional[str]]:
    """Rule: ZERO_AREA_BBOX — bbox must have positive width and height."""
    x1, y1, x2, y2 = det.bbox
    w = abs(float(x2) - float(x1))
    h = abs(float(y2) - float(y1))
    if w <= 0.0 or h <= 0.0:
        return False, "ZERO_AREA_BBOX"
    return True, None


def _check_bbox_area(
    det: Detection,
    min_area_px2: float = 4.0,
) -> tuple[bool, Optional[str]]:
    """Rule: TINY_BBOX — area must be >= min_area_px2 pixels²."""
    x1, y1, x2, y2 = det.bbox
    area = abs(float(x2) - float(x1)) * abs(float(y2) - float(y1))
    if area < min_area_px2:
        return False, "TINY_BBOX"
    return True, None


def _check_bbox_in_bounds(
    det: Detection,
    image_width: Optional[int],
    image_height: Optional[int],
) -> tuple[bool, Optional[str]]:
    """Rule: OUT_OF_BOUNDS — bbox must not be fully outside image bounds.
    Only applied when image dimensions are known.
    """
    if image_width is None or image_height is None:
        return True, None
    x1, y1, x2, y2 = [float(v) for v in det.bbox]
    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)
    if x_max <= 0 or x_min >= image_width or y_max <= 0 or y_min >= image_height:
        return False, "OUT_OF_BOUNDS"
    return True, None


def _check_aspect_ratio(
    det: Detection,
    max_aspect: float = 50.0,
) -> tuple[bool, Optional[str]]:
    """Rule: EXTREME_ASPECT — aspect ratio must not exceed max_aspect in either direction.
    Very thin or very flat bboxes are likely sensor artifacts.
    """
    x1, y1, x2, y2 = det.bbox
    w = abs(float(x2) - float(x1))
    h = abs(float(y2) - float(y1))
    if h <= 0 or w <= 0:
        return True, None  # already caught by ZERO_AREA_BBOX
    ratio = max(w / h, h / w)
    if ratio > max_aspect:
        return False, "EXTREME_ASPECT"
    return True, None


def _check_cfar_geometry(
    det: Detection,
    image_width: Optional[int],
    image_height: Optional[int],
    min_area_px2: float = 16.0,
    max_aspect: float = 30.0,
) -> tuple[bool, Optional[str]]:
    """Rule: CFAR_GEOMETRY — CA-CFAR candidate geometry checks.
    CA-CFAR produces class_id=27 (unknown-object). These candidates
    represent raw acoustic highlights and require:
        - minimum area (larger than TINY_BBOX default, sonar context)
        - reasonable aspect (sonar highlights are rarely >30:1)
    These are sonar-specific thresholds distinct from optical thresholds.
    """
    x1, y1, x2, y2 = det.bbox
    w = abs(float(x2) - float(x1))
    h = abs(float(y2) - float(y1))
    area = w * h
    if area < min_area_px2:
        return False, "CFAR_GEOMETRY"
    if h > 0 and w > 0:
        ratio = max(w / h, h / w)
        if ratio > max_aspect:
            return False, "CFAR_GEOMETRY"
    return True, None


def _check_bathymetry_geometry(
    det: Detection,
    min_area_px2: float = 4.0,
) -> tuple[bool, Optional[str]]:
    """Rule: BATHYMETRY_GEOMETRY — bathymetry anomaly geometry check.
    Bathymetry uses heuristic anomaly bounding boxes from depth grids.
    Minimum area must be reasonable for the MBES grid resolution.
    """
    x1, y1, x2, y2 = det.bbox
    area = abs(float(x2) - float(x1)) * abs(float(y2) - float(y1))
    if area < min_area_px2:
        return False, "BATHYMETRY_GEOMETRY"
    return True, None


def _get_source_sensor(det: Detection, result: DetectionResult) -> str:
    """Infer source sensor from detection metadata or model name."""
    sensor = det.metadata.get("source_sensor", "")
    if sensor:
        return str(sensor).lower()
    model_name = (result.model_name or "").lower()
    if "optical" in model_name or "onnx" in model_name:
        return "optical"
    if "side" in model_name or "sss" in model_name or "sonar" in model_name:
        return "side_scan"
    # Infer from class_id
    if det.class_id == 27:
        return "ca_cfar"
    return "unknown"


# ---------------------------------------------------------------------------
# Main filtering class
# ---------------------------------------------------------------------------

class DetectionFilter:
    """Role 3 filtering engine.

    Applies an ordered sequence of evidence-based rules to each Detection
    in a DetectionResult. Returns a FilteredResult containing per-detection
    filter status and reasons.

    Parameters:
        confidence_threshold: Secondary confidence threshold [0.0, 1.0].
            Detections with confidence below this value are rejected with
            reason LOW_CONFIDENCE. Default 0.30 is deliberately low; the
            Role 2 PostProcessor already applies the primary threshold (0.50).
            Set to 0.0 to disable secondary confidence filtering.
        min_area_px2: Minimum bounding-box area in pixels².
            Default 4.0 (2x2 pixels). Very small boxes are artifact noise.
        max_aspect_ratio: Maximum width:height or height:width ratio.
            Default 50.0. Extremely elongated boxes are likely false positives.
        apply_modality_rules: Whether to apply modality-specific geometry
            rules (CA-CFAR, bathymetry). Default True.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.30,
        min_area_px2: float = 4.0,
        max_aspect_ratio: float = 50.0,
        apply_modality_rules: bool = True,
    ):
        self.confidence_threshold = float(confidence_threshold)
        self.min_area_px2 = float(min_area_px2)
        self.max_aspect_ratio = float(max_aspect_ratio)
        self.apply_modality_rules = apply_modality_rules

    def filter(
        self,
        result: DetectionResult,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> FilteredResult:
        """Filter all detections in result.

        Args:
            result: Role 2 DetectionResult.
            image_width: Image width in pixels (optional; enables OUT_OF_BOUNDS check).
            image_height: Image height in pixels (optional; enables OUT_OF_BOUNDS check).

        Returns:
            FilteredResult with per-detection filter status.
        """
        w = image_width if image_width is not None else result.image_width
        h = image_height if image_height is not None else result.image_height

        filtered: List[FilteredDetection] = []
        for det in result.detections:
            fd = self._filter_one(det, result, w, h)
            filtered.append(fd)

        return FilteredResult(
            original_result=result,
            filtered_detections=filtered,
            confidence_threshold=self.confidence_threshold,
            image_width=w,
            image_height=h,
        )

    def _filter_one(
        self,
        det: Detection,
        result: DetectionResult,
        image_width: Optional[int],
        image_height: Optional[int],
    ) -> FilteredDetection:
        """Apply all rules to a single Detection."""
        # Compute calibrated confidence (handles invalid raw gracefully)
        raw_conf = float(det.confidence)
        try:
            cal_conf = calibrate_confidence(raw_conf)
        except ValueError:
            cal_conf = 0

        source = _get_source_sensor(det, result)

        # Ordered rule pipeline
        rules_checked: List[str] = []
        first_rejection: Optional[str] = None

        def run_rule(rule_name: str, passed: bool, reason: Optional[str]) -> bool:
            rules_checked.append(rule_name)
            nonlocal first_rejection
            if not passed and first_rejection is None:
                first_rejection = reason
            return passed

        # 1. Confidence check (always first)
        ok, reason = _check_confidence(det, self.confidence_threshold)
        still_ok = run_rule("LOW_CONFIDENCE_CHECK", ok, reason)

        # 2. BBox validity (always applied)
        ok, reason = _check_bbox_valid(det)
        still_ok = run_rule("BBOX_VALID_CHECK", ok, reason) and still_ok

        # Only continue geometry checks if bbox is valid
        if _check_bbox_valid(det)[0]:
            # 3. Positive area
            ok, reason = _check_bbox_positive_area(det)
            still_ok = run_rule("BBOX_AREA_CHECK", ok, reason) and still_ok

            # 4. Area threshold
            ok, reason = _check_bbox_area(det, self.min_area_px2)
            still_ok = run_rule("TINY_BBOX_CHECK", ok, reason) and still_ok

            # 5. Image bounds
            ok, reason = _check_bbox_in_bounds(det, image_width, image_height)
            still_ok = run_rule("BOUNDS_CHECK", ok, reason) and still_ok

            # 6. Aspect ratio
            ok, reason = _check_aspect_ratio(det, self.max_aspect_ratio)
            still_ok = run_rule("ASPECT_RATIO_CHECK", ok, reason) and still_ok

            # 7. Modality-specific rules
            if self.apply_modality_rules:
                if source == "ca_cfar" or det.class_id == 27:
                    ok, reason = _check_cfar_geometry(det, image_width, image_height)
                    still_ok = run_rule("CFAR_GEOMETRY_CHECK", ok, reason) and still_ok
                elif source == "bathymetry":
                    ok, reason = _check_bathymetry_geometry(det, self.min_area_px2)
                    still_ok = run_rule("BATHYMETRY_GEOMETRY_CHECK", ok, reason) and still_ok

        status = "accepted" if still_ok else "rejected"
        return FilteredDetection(
            raw_detection=det,
            raw_confidence=raw_conf,
            calibrated_confidence=cal_conf,
            confidence_method=CONFIDENCE_METHOD,
            confidence_threshold=self.confidence_threshold,
            filter_status=status,
            filter_reason=first_rejection if not still_ok else None,
            applied_rules=rules_checked,
            rejection_rule=first_rejection if not still_ok else None,
        )


def filter_detection_result(
    result: DetectionResult,
    confidence_threshold: float = 0.30,
    min_area_px2: float = 4.0,
    max_aspect_ratio: float = 50.0,
    apply_modality_rules: bool = True,
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
) -> FilteredResult:
    """Convenience function: filter a DetectionResult in one call.

    Args:
        result: Role 2 DetectionResult.
        confidence_threshold: Min confidence for acceptance (0.0–1.0).
        min_area_px2: Min bbox area in pixels².
        max_aspect_ratio: Max aspect ratio (width/height or height/width).
        apply_modality_rules: Apply CA-CFAR / bathymetry geometry rules.
        image_width: Image width for bounds check.
        image_height: Image height for bounds check.

    Returns:
        FilteredResult with accepted/rejected breakdown.
    """
    f = DetectionFilter(
        confidence_threshold=confidence_threshold,
        min_area_px2=min_area_px2,
        max_aspect_ratio=max_aspect_ratio,
        apply_modality_rules=apply_modality_rules,
    )
    return f.filter(result, image_width=image_width, image_height=image_height)
