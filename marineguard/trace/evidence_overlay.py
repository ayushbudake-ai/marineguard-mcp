"""
Evidence Overlay Formatter for MarineGuard MCP
"""

from marineguard.schemas import ClassifiedTarget, TraceEvent


class EvidenceOverlayFormatter:
    """Formats evidence reasoning cards for CLI and HTML UI Renders."""

    def format_trace_card(self, event: TraceEvent) -> str:
        lines = []
        lines.append(f"[{event.stage.upper()}] Step {event.event_id}")
        lines.append(f"  • Model:       {event.model}")
        lines.append(f"  • Inputs:      {event.input_summary}")
        lines.append(f"  • Output:      {event.output_summary}")
        lines.append(f"  • Confidence:  {event.confidence * 100:.1f}%")
        lines.append(f"  • Reasoning:   {event.reasoning}")
        return "\n".join(lines)

    def format_html_summary(self, target: ClassifiedTarget) -> str:
        contributions_html = "".join(
            f"<li><b>{k.upper()}:</b> {v*100:.1f}%</li>"
            for k, v in target.sensor_contributions.items()
        )
        return f"""
        <div style="background-color: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #1e293b; color: white;">
            <h4 style="color: #38bdf8; margin-top: 0;">🎯 Classified Contact: {target.target_id}</h4>
            <p><b>Species:</b> {target.species}</p>
            <p><b>Fused Confidence:</b> <span style="color: #4ade80; font-size: 1.1em;">{target.confidence * 100:.1f}%</span></p>
            <p><b>Location & Depth:</b> {target.lat_lon[0]:.4f} N, {target.lat_lon[1]:.4f} E at {target.depth_m}m depth</p>
            <p><b>Dimensions:</b> {target.geometry_m[0]}m × {target.geometry_m[1]}m × {target.geometry_m[2]}m</p>
            <p><b>Multi-Sensor Contributions:</b></p>
            <ul>{contributions_html}</ul>
            <p><b>Removal Priority:</b> <span style="color: #f59e0b;">{target.removal_priority}</span> | <b>Entanglement Risk:</b> <span style="color: #ef4444;">{target.entanglement_risk}</span></p>
        </div>
        """
