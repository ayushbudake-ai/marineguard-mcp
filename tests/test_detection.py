"""
Unit Tests for Module 2 — Detection & Multi-Sensor Fusion
"""

import pytest
from data.test_data.sample_frames import FrameReplayHarness
from marineguard.detection.side_scan import SideScanDetector
from marineguard.detection.sas import SASDetector
from marineguard.detection.optical import OpticalDetector
from marineguard.detection.bathymetry import BathymetryDetector
from marineguard.detection.fusion import MultiSensorFusionEngine


def test_detection_pipelines_and_fusion():
    harness = FrameReplayHarness()
    ping = harness.get_next_ping()

    side_scan = SideScanDetector()
    optical = OpticalDetector()
    bathy = BathymetryDetector()
    fusion = MultiSensorFusionEngine()

    c_sonar = side_scan.process_waterfall_ping(ping)
    c_optical = optical.process_optical_frame(ping)
    c_bathy = bathy.process_bathymetry_grid(ping)

    assert len(c_sonar) > 0
    assert len(c_optical) > 0
    assert len(c_bathy) > 0

    all_contacts = c_sonar + c_optical + c_bathy
    target = fusion.fuse(all_contacts)

    assert target.confidence >= 0.80
    assert "side_scan" in target.sensor_contributions
    assert "optical" in target.sensor_contributions
    assert "bathymetry" in target.sensor_contributions
    assert target.removal_priority in ["HIGH", "MEDIUM", "LOW"]
