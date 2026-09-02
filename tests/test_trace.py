"""
Unit Tests for Module 4 — Explainable Trace & Visualizer
"""

import pytest
from marineguard.trace.tracer import ExplainableTracer
from marineguard.trace.visualizer import EvidenceVisualizer
from marineguard.detection.fusion import MultiSensorFusionEngine
from marineguard.detection.side_scan import SideScanDetector
from data.test_data.sample_frames import FrameReplayHarness


def test_explainable_tracer():
    tracer = ExplainableTracer()
    evt = tracer.log(
        stage="TEST_STAGE",
        input_summary="Input ping",
        output_summary="Output target",
        model="TestModel",
        confidence=0.95,
        reasoning="Valid detection",
    )
    assert len(tracer.get_history()) == 1
    assert evt.stage == "TEST_STAGE"


def test_evidence_visualizer():
    harness = FrameReplayHarness()
    ping = harness.get_next_ping()
    side_scan = SideScanDetector()
    fusion = MultiSensorFusionEngine()

    contacts = side_scan.process_waterfall_ping(ping)
    target = fusion.fuse(contacts)

    viz = EvidenceVisualizer()
    out_path = viz.generate_evidence_overlay(target, ping)
    assert out_path.endswith(".png")
