"""
Role 3 — Evidence / Explainability Layer for MarineGuard MCP

Generates human-readable and structured evidence reports for
FilteredDetection objects produced by the filtering layer.

This module extends (not duplicates) the existing ExplainableTracer
and EvidenceOverlayFormatter in marineguard/trace/.

Those existing classes work with TraceEvent / ClassifiedTarget (the
AUV mission-level schema). This module works with Detection /
FilteredDetection (the detector-level schema from Role 2/3).

Design:
    - EvidenceRecord: structured evidence dict for a single detection
    - DetectionEvidenceBuilder: produces EvidenceRecord from FilteredDetection
    - format_evidence_card(): human-readable plain-text card
    - format_evidence_html(): HTML card for dashboard rendering

All evidence fields correspond to actual processing steps.
No explanations are fabricated.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from marineguard.detection.filtering import FilteredDetection, FilteredResult
from marineguard.detection.confidence import CONFIDENCE_METHOD, CONFIDENCE_METHOD_DESCRIPTION


# ---------------------------------------------------------------------------
# EvidenceRecord
# ---------------------------------------------------------------------------

class EvidenceRecord:
    """Structured evidence for a single detection after Role 3 processing."""

    def __init__(
        self,
        class_name: str,
        class_id: Optional[int],
        raw_confidence: float,
        calibrated_confidence: int,
        confidence_method: str,
        confidence_threshold: float,
        bbox: List[float],
        filter_status: str,
        filter_reason: Optional[str],
        rejection_rule: Optional[str],
        applied_rules: List[str],
        source_sensor: str,
        metadata: Dict[str, Any],
    ):
        self.class_name = class_name
        self.class_id = class_id
        self.raw_confidence = raw_confidence
        self.calibrated_confidence = calibrated_confidence
        self.confidence_method = confidence_method
        self.confidence_threshold = confidence_threshold
        self.bbox = bbox
        self.filter_status = filter_status
        self.filter_reason = filter_reason
        self.rejection_rule = rejection_rule
        self.applied_rules = applied_rules
        self.source_sensor = source_sensor
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_name": self.class_name,
            "class_id": self.class_id,
            "raw_confidence": round(self.raw_confidence, 6),
            "calibrated_confidence": self.calibrated_confidence,
            "confidence_method": self.confidence_method,
            "confidence_threshold": self.confidence_threshold,
            "bbox": [round(v, 2) for v in self.bbox],
            "filter_status": self.filter_status,
            "filter_reason": self.filter_reason,
            "rejection_rule": self.rejection_rule,
            "applied_rules": self.applied_rules,
            "source_sensor": self.source_sensor,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# EvidenceBuilder
# ---------------------------------------------------------------------------

class DetectionEvidenceBuilder:
    """Builds EvidenceRecord objects from FilteredDetection instances."""

    def build(self, fd: FilteredDetection) -> EvidenceRecord:
        """Convert a FilteredDetection to a structured EvidenceRecord."""
        det = fd.raw_detection
        source = det.metadata.get("source_sensor", "unknown")
        return EvidenceRecord(
            class_name=det.class_name,
            class_id=det.class_id,
            raw_confidence=fd.raw_confidence,
            calibrated_confidence=fd.calibrated_confidence,
            confidence_method=fd.confidence_method,
            confidence_threshold=fd.confidence_threshold,
            bbox=list(det.bbox),
            filter_status=fd.filter_status,
            filter_reason=fd.filter_reason,
            rejection_rule=fd.rejection_rule,
            applied_rules=list(fd.applied_rules),
            source_sensor=str(source),
            metadata=dict(det.metadata),
        )

    def build_all(self, result: FilteredResult) -> List[EvidenceRecord]:
        """Build EvidenceRecord for every detection in a FilteredResult."""
        return [self.build(fd) for fd in result.filtered_detections]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_evidence_card(record: EvidenceRecord) -> str:
    """Render a plain-text evidence card for a single detection.

    The card corresponds to actual processing. No field is fabricated.
    """
    status_icon = "✅" if record.filter_status == "accepted" else "❌"
    lines = [
        f"{'=' * 60}",
        f"{status_icon} [{record.filter_status.upper()}] {record.class_name}"
        + (f" (class_id={record.class_id})" if record.class_id is not None else ""),
        f"{'=' * 60}",
        f"  Source sensor   : {record.source_sensor}",
        f"  Raw confidence  : {record.raw_confidence:.4f}  ({record.raw_confidence * 100:.2f}%)",
        f"  Calib. conf.    : {record.calibrated_confidence}/100",
        f"  Conf. method    : {record.confidence_method}",
        f"  Threshold used  : {record.confidence_threshold:.2f}",
        f"  BBox            : {record.bbox}",
    ]

    if record.filter_status == "rejected":
        lines.append(f"  REJECTION REASON: {record.filter_reason}")
        lines.append(f"  Rejection rule  : {record.rejection_rule}")
    else:
        lines.append("  Filter result   : All rules PASSED")

    lines.append(f"  Rules checked   : {', '.join(record.applied_rules)}")
    if record.metadata:
        lines.append(f"  Raw metadata    : {record.metadata}")
    lines.append("")
    return "\n".join(lines)


def format_evidence_html(record: EvidenceRecord) -> str:
    """Render an HTML evidence card for a single detection.

    Consistent with EvidenceOverlayFormatter style in marineguard/trace/.
    """
    status_color = "#4ade80" if record.filter_status == "accepted" else "#ef4444"
    status_label = record.filter_status.upper()
    reason_html = ""
    if record.filter_status == "rejected" and record.filter_reason:
        reason_html = (
            f"<p><b>Rejection Reason:</b> "
            f"<span style='color:#ef4444'>{record.filter_reason}</span></p>"
            f"<p><b>Rejection Rule:</b> {record.rejection_rule}</p>"
        )
    rules_joined = ", ".join(record.applied_rules) if record.applied_rules else "none"
    return f"""
    <div style="background-color:#0f172a;padding:12px;border-radius:8px;
                border:1px solid #1e293b;color:white;margin-bottom:8px;">
        <h4 style="color:{status_color};margin-top:0;">
            [{status_label}] {record.class_name}
            {"(class_id=" + str(record.class_id) + ")" if record.class_id is not None else ""}
        </h4>
        <p><b>Source Sensor:</b> {record.source_sensor}</p>
        <p><b>Raw Confidence:</b>
            <span style="color:#38bdf8">{record.raw_confidence:.4f}</span>
            ({record.raw_confidence * 100:.2f}%)
        </p>
        <p><b>Calibrated Confidence:</b>
            <span style="color:#38bdf8">{record.calibrated_confidence}/100</span>
        </p>
        <p><b>Confidence Method:</b> {record.confidence_method}</p>
        <p><b>Threshold:</b> {record.confidence_threshold:.2f}</p>
        <p><b>BBox:</b> {record.bbox}</p>
        {reason_html}
        <p><b>Rules Checked:</b> {rules_joined}</p>
    </div>
    """


def format_result_summary(result: FilteredResult) -> str:
    """Plain-text summary of a FilteredResult."""
    accepted = result.accepted
    rejected = result.rejected
    lines = [
        "=" * 60,
        "ROLE 3 FILTER SUMMARY",
        "=" * 60,
        f"  Raw detections  : {len(result.filtered_detections)}",
        f"  Accepted        : {len(accepted)}",
        f"  Rejected        : {len(rejected)}",
        f"  Threshold       : {result.confidence_threshold}",
        f"  Method          : {CONFIDENCE_METHOD}",
    ]
    if rejected:
        reason_counts: Dict[str, int] = {}
        for fd in rejected:
            reason = fd.filter_reason or "UNKNOWN"
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        lines.append("  Rejection breakdown:")
        for reason, count in sorted(reason_counts.items()):
            lines.append(f"    {reason}: {count}")
    lines.append("")
    return "\n".join(lines)
