"""
Explainable Trace Logger for MarineGuard MCP
"""

import time
import json
from typing import List, Dict, Any, Optional
from marineguard.schemas import TraceEvent


class ExplainableTracer:
    """Step-by-step reasoning and model inference trace recorder."""

    def __init__(self):
        self.events: List[TraceEvent] = []

    def log(
        self,
        stage: str,
        input_summary: str,
        output_summary: str,
        model: str,
        confidence: float,
        reasoning: str,
        evidence_path: Optional[str] = None,
    ) -> TraceEvent:
        event = TraceEvent(
            event_id=f"EVT_{len(self.events) + 1:04d}",
            timestamp=time.time(),
            stage=stage,
            input_summary=input_summary,
            output_summary=output_summary,
            model=model,
            confidence=round(confidence, 3),
            reasoning=reasoning,
            evidence_overlay_path=evidence_path,
        )
        self.events.append(event)
        return event

    def get_history(self) -> List[TraceEvent]:
        return self.events

    def export_json(self) -> str:
        return json.dumps([e.model_dump() for e in self.events], indent=2)

    def log_detection_filtering(
        self,
        filtered_result: Any,
        stage: str = "ROLE_3_FILTERING",
    ) -> TraceEvent:
        """Convenience method to log a Role 3 filtering result directly to trace history."""
        raw_count = len(getattr(filtered_result, "filtered_detections", []))
        accepted_count = len(getattr(filtered_result, "accepted", []))
        rejected_count = len(getattr(filtered_result, "rejected", []))
        reasoning = f"Filtered {raw_count} raw detections: {accepted_count} accepted, {rejected_count} rejected."
        return self.log(
            stage=stage,
            input_summary=f"{raw_count} raw detections",
            output_summary=f"{accepted_count} accepted detections",
            model="DetectionFilter",
            confidence=1.0,
            reasoning=reasoning,
        )
