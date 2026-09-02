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
