"""
Role 4 — PDF Inspection/Mission Report for MarineGuard MCP

Generates a professional detection report from DetectionResult (Role 3 output).

Report contents (where data is actually available):
    - Report title and generation timestamp
    - Detection summary (accepted / rejected counts from role3_summary)
    - Per-detection table: class, raw confidence, calibrated confidence,
      sensor, bounding box, filter status
    - Coordinates: shown if present in metadata; "unavailable" otherwise
    - Rejected detections audit table (from all_detections)
    - Evidence/filter information per detection (rules checked, rejection reason)
    - Notes on scope and data limitations

Report explicitly OMITS (not in data pipeline):
    - Temperature
    - Battery level
    - Depth sensor
    - IMU / compass / gyroscope
    - Live GPS hardware
    - Live telemetry
    - Vehicle health

If coordinates are unavailable, the report states "Coordinates: unavailable"
and does NOT generate fake values.

Dependencies:
    reportlab >= 3.6.0 (already in requirements.txt)
    Falls back to plain-text .txt if reportlab layout fails.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from marineguard.detection.schema import Detection, DetectionResult
from marineguard.exporters.geotagging import Geotagger


class PDFReportExporter:
    """Generates a PDF detection/inspection report from DetectionResult.

    Consumes the frozen Role 3 DetectionResult output.
    Does NOT accept the legacy ClassifiedTarget schema.
    """

    def __init__(self):
        self._geotagger = Geotagger()

    def generate_report(
        self,
        result: DetectionResult,
        output_file: str = "data/reports/MarineGuard_Detection_Report.pdf",
        mission_id: Optional[str] = None,
        mission_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a PDF (or .txt fallback) detection report.

        Args:
            result: Role 3 DetectionResult.
            output_file: Output file path (.pdf or .txt).
            mission_id: Optional mission identifier string from actual data.
            mission_metadata: Optional real mission metadata dict.

        Returns:
            Path to the generated report file.
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True) if os.path.dirname(output_file) else None
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        try:
            return self._generate_pdf(result, output_file, mission_id, mission_metadata, generated_at)
        except Exception as pdf_err:
            # Graceful fallback to plain text
            txt_file = output_file.replace(".pdf", ".txt")
            self._generate_txt_fallback(result, txt_file, mission_id, generated_at)
            return txt_file

    # ------------------------------------------------------------------
    # PDF generation
    # ------------------------------------------------------------------

    def _generate_pdf(
        self,
        result: DetectionResult,
        output_file: str,
        mission_id: Optional[str],
        mission_metadata: Optional[Dict[str, Any]],
        generated_at: str,
    ) -> str:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        doc = SimpleDocTemplate(
            output_file,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = []
        styles = getSampleStyleSheet()

        # ----- Styles -----
        title_style = ParagraphStyle(
            "MG_Title", parent=styles["Heading1"],
            fontSize=16, textColor=colors.HexColor("#0f172a"), spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "MG_Subtitle", parent=styles["Normal"],
            fontSize=10, textColor=colors.HexColor("#475569"), spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "MG_Heading", parent=styles["Heading2"],
            fontSize=13, textColor=colors.HexColor("#1e293b"),
            spaceBefore=14, spaceAfter=6,
        )
        note_style = ParagraphStyle(
            "MG_Note", parent=styles["Normal"],
            fontSize=8, textColor=colors.HexColor("#64748b"), spaceAfter=4,
        )

        BLUE = colors.HexColor("#38bdf8")
        DARK = colors.HexColor("#0f172a")
        LIGHT_BG = colors.HexColor("#f8fafc")
        GRID_COLOR = colors.HexColor("#cbd5e1")

        # ----- Header -----
        story.append(Paragraph("MarineGuard MCP — Detection Report", title_style))
        mid = mission_id or "N/A"
        story.append(Paragraph(
            f"Mission ID: {mid} &nbsp;&nbsp;|&nbsp;&nbsp; Generated: {generated_at}",
            subtitle_style,
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=14))

        # ----- 1. Summary -----
        story.append(Paragraph("1. Detection Summary", heading_style))
        r3 = result.role3_summary or {}
        summary_data = [
            ["Model", result.model_name or "N/A",
             "Status", result.status or "N/A"],
            ["Raw Detections", str(r3.get("raw_count", "N/A")),
             "Accepted", str(r3.get("accepted_count", len(result.detections)))],
            ["Rejected", str(r3.get("rejected_count", "N/A")),
             "Threshold", str(r3.get("confidence_threshold", "N/A"))],
            ["Image Size",
             (f"{result.image_width}×{result.image_height}" if result.image_width else "N/A"),
             "Inference Time",
             (f"{result.inference_time_ms:.1f} ms" if result.inference_time_ms else "N/A")],
        ]
        t_summary = Table(summary_data, colWidths=[110, 130, 110, 130])
        t_summary.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("GRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ]))
        story.append(t_summary)
        story.append(Spacer(1, 12))

        # ----- 2. Accepted Detections Table -----
        story.append(Paragraph("2. Accepted Detections", heading_style))
        if result.detections:
            header = [
                "ID", "Class", "Raw Conf", "Cal. Conf", "Sensor", "BBox (px)", "Coordinates",
            ]
            rows = [header]
            for i, det in enumerate(result.detections):
                coord = self._geotagger.geotag(det, mission_metadata)
                meta = det.metadata or {}
                role3 = meta.get("role3", {}) or {}
                cal = meta.get("calibrated_confidence") or role3.get("calibrated_confidence")
                sensor = meta.get("source_sensor", "unknown")
                bbox_str = f"[{det.bbox[0]:.0f},{det.bbox[1]:.0f},{det.bbox[2]:.0f},{det.bbox[3]:.0f}]"
                if coord.is_available:
                    coord_str = f"lat={coord.latitude:.5f}\nlon={coord.longitude:.5f}"
                else:
                    coord_str = "unavailable"
                cal_str = f"{cal}/100" if cal is not None else "N/A"
                rows.append([
                    str(i),
                    det.class_name[:24],
                    f"{det.confidence:.4f}",
                    cal_str,
                    sensor[:16],
                    bbox_str,
                    coord_str,
                ])
            t_det = Table(rows, colWidths=[25, 95, 58, 55, 65, 85, 95])
            t_det.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
            ]))
            story.append(t_det)
        else:
            story.append(Paragraph(
                "No accepted detections in this result.", styles["Normal"]
            ))
        story.append(Spacer(1, 12))

        # ----- 3. Rejected Detections Audit -----
        rejected = []
        if result.all_detections:
            rejected = [
                d for d in result.all_detections
                if isinstance(d, dict)
                and (d.get("role3") or {}).get("filter_status") == "rejected"
            ]

        story.append(Paragraph("3. Rejected Detections (Audit)", heading_style))
        if rejected:
            rej_header = ["Class", "Raw Conf", "Cal. Conf", "Rejection Rule", "Reason"]
            rej_rows = [rej_header]
            for d in rejected:
                r3_d = d.get("role3", {}) or {}
                rej_rows.append([
                    (d.get("class") or d.get("class_name") or "N/A")[:24],
                    f"{r3_d.get('raw_confidence', 0):.4f}",
                    str(r3_d.get("calibrated_confidence", "N/A")),
                    str(r3_d.get("rejection_rule", "N/A"))[:20],
                    str(r3_d.get("filter_reason", "N/A"))[:28],
                ])
            t_rej = Table(rej_rows, colWidths=[100, 58, 55, 100, 165])
            t_rej.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7f1d1d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
            ]))
            story.append(t_rej)
        else:
            story.append(Paragraph("No rejected detections recorded.", styles["Normal"]))
        story.append(Spacer(1, 12))

        # ----- 4. Scope Notes -----
        story.append(Paragraph("4. Notes & Limitations", heading_style))
        notes = [
            "• Sensor scope: OPTICAL and SIDE-SCAN SONAR only.",
            "• Coordinates: Only real coordinates from detection metadata are shown. "
              "'unavailable' means no coordinate data was present in the source — no values were fabricated.",
            "• Confidence: Raw model confidence [0.0–1.0]. Calibrated confidence [0–100] uses "
              "DETERMINISTIC_PIECEWISE_LINEAR_v1 (Role 3 method).",
            "• This report does NOT include temperature, battery, depth sensor, IMU, compass, "
              "gyroscope, or any live telemetry — these are outside MarineGuard scope.",
            "• Rejection rules applied by Role 3: LOW_CONFIDENCE, INVALID_BBOX, ZERO_AREA_BBOX, "
              "OUT_OF_BOUNDS, TINY_BBOX, EXTREME_ASPECT, CFAR_GEOMETRY, BATHYMETRY_GEOMETRY.",
        ]
        for note in notes:
            story.append(Paragraph(note, note_style))

        doc.build(story)
        return output_file

    # ------------------------------------------------------------------
    # Plain-text fallback
    # ------------------------------------------------------------------

    def _generate_txt_fallback(
        self,
        result: DetectionResult,
        output_file: str,
        mission_id: Optional[str],
        generated_at: str,
    ) -> None:
        r3 = result.role3_summary or {}
        lines = [
            "=" * 70,
            "MarineGuard MCP — Detection Report (Plain-Text Fallback)",
            "=" * 70,
            f"Mission ID     : {mission_id or 'N/A'}",
            f"Generated      : {generated_at}",
            f"Model          : {result.model_name or 'N/A'}",
            f"Status         : {result.status}",
            f"Raw detections : {r3.get('raw_count', 'N/A')}",
            f"Accepted       : {r3.get('accepted_count', len(result.detections))}",
            f"Rejected       : {r3.get('rejected_count', 'N/A')}",
            f"Threshold      : {r3.get('confidence_threshold', 'N/A')}",
            "",
            "ACCEPTED DETECTIONS",
            "-" * 70,
        ]
        for i, det in enumerate(result.detections):
            meta = det.metadata or {}
            role3 = meta.get("role3", {}) or {}
            cal = meta.get("calibrated_confidence") or role3.get("calibrated_confidence")
            sensor = meta.get("source_sensor", "unknown")
            coord = self._geotagger.geotag(det)
            coord_str = (
                f"lat={coord.latitude}, lon={coord.longitude}"
                if coord.is_available else "unavailable"
            )
            lines.extend([
                f"[{i}] class={det.class_name} class_id={det.class_id}",
                f"    raw_conf={det.confidence:.4f}  cal_conf={cal}/100",
                f"    sensor={sensor}  bbox={det.bbox}",
                f"    coordinates={coord_str}",
            ])

        lines.extend(["", "REJECTED DETECTIONS (AUDIT)", "-" * 70])
        if result.all_detections:
            rej = [
                d for d in result.all_detections
                if isinstance(d, dict)
                and (d.get("role3") or {}).get("filter_status") == "rejected"
            ]
            for d in rej:
                r3_d = d.get("role3", {}) or {}
                lines.append(
                    f"  class={d.get('class') or d.get('class_name')}  "
                    f"rule={r3_d.get('rejection_rule')}  "
                    f"reason={r3_d.get('filter_reason')}"
                )
        else:
            lines.append("  No rejected detections recorded.")

        lines.extend([
            "",
            "NOTES",
            "-" * 70,
            "Coordinates unavailable means no coordinate data was present in source.",
            "No coordinates were fabricated.",
            "Sensor scope: OPTICAL and SIDE-SCAN SONAR only.",
        ])

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
