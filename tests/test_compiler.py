"""
Unit Tests for Module 1 — Sensor Suite Compiler
"""

import pytest
from marineguard.compiler.sensor_parser import SensorParser
from marineguard.compiler.geometry_solver import GeometrySolver
from marineguard.compiler.pipeline_generator import PipelineGenerator
from marineguard.compiler.mcp_emitter import MCPEmitter


def test_sagar_netra_parser():
    parser = SensorParser()
    spec = parser.parse("data/sensor_specs/sagar_netra.yaml")
    assert spec.name == "Sagar Netra (AUV-01)"
    assert len(spec.sensors) == 5
    assert spec.sensors[0].sub_type == "side_scan"


def test_hugin_parser():
    parser = SensorParser()
    spec = parser.parse("data/sensor_specs/hugin_3000.yaml")
    assert spec.name == "Kongsberg HUGIN 3000"
    assert spec.sensors[0].sub_type == "sas"


def test_geometry_solver():
    solver = GeometrySolver()
    parser = SensorParser()
    spec = parser.parse("data/sensor_specs/sagar_netra.yaml")

    auv_pose = {"lat": 13.0827, "lon": 80.2707, "depth_m": 20.0, "heading_deg": 90.0}
    pos = solver.calculate_sensor_position(auv_pose, spec.sensors[0])
    assert pos["sensor_id"] == "side_scan_01"
    assert pos["depth_m"] == 19.8

    swath, res = solver.compute_swath_coverage(spec.sensors[0], altitude_m=10.0)
    assert swath > 0
    assert res > 0


def test_mcp_emitter_swap():
    emitter = MCPEmitter()
    parser = SensorParser()

    spec_sagar = parser.parse("data/sensor_specs/sagar_netra.yaml")
    reg_sagar = emitter.compile(spec_sagar)
    tool_names_sagar = [t["name"] for t in reg_sagar.tools_emitted]
    assert "start_side_scan_survey" in tool_names_sagar

    spec_hugin = parser.parse("data/sensor_specs/hugin_3000.yaml")
    reg_hugin = emitter.compile(spec_hugin)
    tool_names_hugin = [t["name"] for t in reg_hugin.tools_emitted]
    assert "start_sas_survey" in tool_names_hugin
    assert "detect_debris_sas" in tool_names_hugin
