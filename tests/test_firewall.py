"""
Unit Tests for Module 3 — Mission Firewall
"""

import pytest
from marineguard.schemas import Action, MissionContext, RiskLevel
from marineguard.firewall.policy import MissionFirewallPolicy


def test_firewall_low_risk_auto_allow():
    policy = MissionFirewallPolicy()
    action = Action(type="generate_report", description="Generate report")
    context = MissionContext(battery_reserve=0.85, acoustic_link_kbps=10.0)

    decision = policy.check_action(action, context)
    assert decision.allowed is True
    assert decision.risk_level == RiskLevel.LOW


def test_firewall_dynamic_risk_escalation():
    policy = MissionFirewallPolicy()
    # Medium risk base action
    action = Action(type="request_course_change", description="Turn left", consumes_reserve=0.15)
    # Low battery + degraded comms
    context = MissionContext(battery_reserve=0.20, acoustic_link_kbps=3.0)

    decision = policy.check_action(action, context)
    assert decision.allowed is False
    assert decision.requires_approval is True
    assert decision.risk_level == RiskLevel.CRITICAL
    assert "Low Battery Reserve" in decision.reason
    assert "Degraded Acoustic Comms Link" in decision.reason
