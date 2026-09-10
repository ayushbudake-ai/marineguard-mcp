"""
Tests for Role 3 — Confidence Processing Layer
marineguard/detection/confidence.py
"""

import pytest
from marineguard.detection.confidence import (
    calibrate_confidence,
    calibrate_confidence_float,
    is_monotonic,
    CONFIDENCE_METHOD,
    CONFIDENCE_METHOD_DESCRIPTION,
)


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------

def test_calibrate_zero():
    """Confidence 0.0 must map to 0."""
    assert calibrate_confidence(0.0) == 0


def test_calibrate_one():
    """Confidence 1.0 must map to 100."""
    assert calibrate_confidence(1.0) == 100


def test_calibrate_typical_midrange():
    """Confidence 0.60 should map into the 40–65 band."""
    result = calibrate_confidence(0.60)
    assert 40 <= result <= 65


def test_calibrate_high_confidence():
    """Confidence 0.90 should map into the 82–100 band."""
    result = calibrate_confidence(0.90)
    assert 82 <= result <= 100


def test_calibrate_low_confidence():
    """Confidence 0.15 should map into the 0–20 band."""
    result = calibrate_confidence(0.15)
    assert 0 <= result <= 20


def test_calibrate_boundary_values():
    """Boundary values at segment transitions must be in expected range."""
    assert 20 - 1 <= calibrate_confidence(0.30) <= 20 + 1
    assert 40 - 1 <= calibrate_confidence(0.50) <= 40 + 1
    assert 65 - 1 <= calibrate_confidence(0.70) <= 65 + 1
    assert 82 - 1 <= calibrate_confidence(0.85) <= 82 + 1


def test_calibrate_returns_int():
    """calibrate_confidence must return an integer."""
    result = calibrate_confidence(0.73)
    assert isinstance(result, int)


def test_calibrate_float_returns_float():
    """calibrate_confidence_float must return a float."""
    result = calibrate_confidence_float(0.73)
    assert isinstance(result, float)


def test_calibrate_float_zero():
    assert calibrate_confidence_float(0.0) == 0.0


def test_calibrate_float_one():
    assert calibrate_confidence_float(1.0) == 100.0


# ---------------------------------------------------------------------------
# Invalid confidence
# ---------------------------------------------------------------------------

def test_calibrate_below_zero_raises():
    with pytest.raises(ValueError):
        calibrate_confidence(-0.01)


def test_calibrate_above_one_raises():
    with pytest.raises(ValueError):
        calibrate_confidence(1.001)


def test_calibrate_float_below_zero_raises():
    with pytest.raises(ValueError):
        calibrate_confidence_float(-0.1)


def test_calibrate_float_above_one_raises():
    with pytest.raises(ValueError):
        calibrate_confidence_float(1.1)


# ---------------------------------------------------------------------------
# Monotonicity
# ---------------------------------------------------------------------------

def test_calibrate_monotone_increasing():
    """calibrated_confidence must be non-decreasing as raw increases."""
    values = [i / 100.0 for i in range(0, 101)]
    calibrated = [calibrate_confidence(v) for v in values]
    for i in range(1, len(calibrated)):
        assert calibrated[i] >= calibrated[i - 1], (
            f"Monotonicity violated at raw={values[i]:.2f}: "
            f"calibrated={calibrated[i]} < prev={calibrated[i - 1]}"
        )


def test_is_monotonic_utility():
    """The is_monotonic() utility must return True for the default curve."""
    assert is_monotonic() is True


# ---------------------------------------------------------------------------
# Deterministic output
# ---------------------------------------------------------------------------

def test_calibrate_deterministic():
    """Same input must always produce the same output."""
    for raw in [0.0, 0.25, 0.50, 0.75, 1.0]:
        first = calibrate_confidence(raw)
        second = calibrate_confidence(raw)
        assert first == second


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def test_confidence_method_string_nonempty():
    assert isinstance(CONFIDENCE_METHOD, str)
    assert len(CONFIDENCE_METHOD) > 0


def test_confidence_method_description_nonempty():
    assert isinstance(CONFIDENCE_METHOD_DESCRIPTION, str)
    assert len(CONFIDENCE_METHOD_DESCRIPTION) > 0


def test_confidence_method_not_claiming_statistical():
    """The method name must not claim statistical probability calibration."""
    desc_lower = CONFIDENCE_METHOD_DESCRIPTION.lower()
    assert "platt" not in desc_lower or "not" in desc_lower
