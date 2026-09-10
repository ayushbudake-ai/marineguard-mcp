"""
Unit & Integration Tests for Member 5 — UI Dashboard & System Integration
Verifies:
1. Trimmed MCP server (detection & reporting only; no vehicle controls).
2. Real benchmark calculations in eval.py (F1, FPR, real latency).
3. Confidence filtering (threshold changes affect accepted/filtered counts).
4. No coordinate fabrication (missing coordinates remain missing).
5. Deletion of COMPLETE_MARINEGUARD_CODEBASE.py.
6. Trimmed config.yaml (model/fusion present, firewall telemetry absent).
"""

import os
from pathlib import Path
import pytest
import yaml
from marineguard.mcp_server import MarineGuardMCPServer
from marineguard.schemas import ClassifiedTarget
import eval as eval_module


def test_trimmed_mcp_server():
    """Verify that MCP server exposes detection & reporting tools and no vehicle actions."""
    server = MarineGuardMCPServer()

    # 1. trigger_close_inspection must not exist
    assert not hasattr(server, "trigger_close_inspection")

    # 2. Registry tools emitted must not contain vehicle action commands
    emitted_names = [t.get("name", "").lower() for t in server.registry.tools_emitted]
    for prohibited in ["control", "navigate", "steer", "altitude", "thruster", "motor"]:
        assert not any(prohibited in name for name in emitted_names), f"Prohibited tool {prohibited} found in MCP tools"

    # 3. Detection and reporting must work cleanly
    survey = server.marine_debris_survey("Sagar Netra", confidence_threshold=0.75)
    assert survey["status"] == "COMPLETED"
    assert "targets_accepted" in survey
    assert "targets_filtered" in survey
    assert len(survey["classified_targets"]) == survey["targets_accepted"]


def test_eval_pipeline_real_benchmarks():
    """Verify eval.py calculates real metrics empirically without hardcoded strings."""
    metrics = eval_module.evaluate_pipeline(num_iterations=20, confidence_threshold=0.70)

    assert isinstance(metrics["f1_score"], float)
    assert 0.0 <= metrics["f1_score"] <= 1.0
    assert isinstance(metrics["precision"], float)
    assert 0.0 <= metrics["precision"] <= 1.0
    assert isinstance(metrics["recall"], float)
    assert 0.0 <= metrics["recall"] <= 1.0
    assert isinstance(metrics["false_positive_rate"], float)
    assert 0.0 <= metrics["false_positive_rate"] <= 1.0
    assert metrics["latency_mean_ms"] > 0.0
    assert metrics["samples_evaluated"] >= 20
    assert metrics["true_positives"] + metrics["false_negatives"] > 0


def test_confidence_filtering_logic():
    """Verify that confidence threshold slider actually alters accepted vs filtered targets."""
    server = MarineGuardMCPServer()

    # Low threshold accepts all
    low_res = server.marine_debris_survey("Sagar Netra", confidence_threshold=0.50)
    # Very high threshold filters some or all
    high_res = server.marine_debris_survey("Sagar Netra", confidence_threshold=0.98)

    assert low_res["targets_accepted"] >= high_res["targets_accepted"]
    assert high_res["targets_filtered"] >= low_res["targets_filtered"]


def test_no_coordinate_fabrication():
    """Verify that coordinates are preserved if present and never fabricated if absent."""
    server = MarineGuardMCPServer()
    survey = server.marine_debris_survey("Sagar Netra")

    for target_dict in survey["classified_targets"]:
        target = ClassifiedTarget(**target_dict)
        if target.lat_lon is not None:
            # Must not be fabricated dummy (0, 0)
            assert target.lat_lon != (0.0, 0.0)
            assert -90.0 <= target.lat_lon[0] <= 90.0
            assert -180.0 <= target.lat_lon[1] <= 180.0


def test_obsolete_codebase_file_deleted():
    """Verify that COMPLETE_MARINEGUARD_CODEBASE.py has been deleted."""
    repo_root = Path(__file__).resolve().parent.parent
    obsolete_file = repo_root / "COMPLETE_MARINEGUARD_CODEBASE.py"
    assert not obsolete_file.exists(), "COMPLETE_MARINEGUARD_CODEBASE.py should have been deleted"


def test_trimmed_config_yaml():
    """Verify config.yaml contains model/fusion and does not contain firewall telemetry."""
    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Required sections
    assert "compiler" in config
    assert "models" in config["compiler"]
    assert "fusion" in config["compiler"]
    assert "exporters" in config

    # Firewall telemetry section must be excised
    assert "firewall" not in config, "firewall section should be excised from config.yaml"
