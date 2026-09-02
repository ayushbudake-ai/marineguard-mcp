"""
Operator Approval Interface for MarineGuard MCP Mission Firewall
"""

from typing import Dict, Any
from marineguard.schemas import Action, MissionContext, FirewallDecision


class OperatorUIHandler:
    """Renders Mission Firewall Intercept Modal and handles decision responses."""

    def format_intercept_card(
        self, action: Action, context: MissionContext, decision: FirewallDecision
    ) -> str:
        lines = []
        lines.append("[FIREWALL INTERCEPT]")
        lines.append("=" * 55)
        lines.append(f"ACTION REQUESTED: {action.type.upper()}")
        lines.append(f"Description: {action.description}")
        lines.append(f"Target: {action.target_id or 'Survey Grid'}")
        lines.append("-" * 55)
        lines.append("CURRENT VEHICLE STATUS:")
        lines.append(f"  * Battery Reserve: {context.battery_reserve * 100:.0f}% (Threshold: 25%)")
        lines.append(f"  * Acoustic Link:   {context.acoustic_link_kbps:.1f} kbps (Threshold: 5.0 kbps)")
        lines.append(f"  * Speed & Altitude: {context.speed_knots} knots @ {context.current_depth_m}m depth")
        lines.append("-" * 55)
        lines.append(f"EVALUATED RISK TIER: [{decision.risk_level.value}]")
        lines.append(f"Reasoning: {decision.reason}")
        if decision.suggested_modifications:
            lines.append("Suggested Safer Parameters:")
            for k, v in decision.suggested_modifications.items():
                lines.append(f"  -> {k}: {v}")
        lines.append("-" * 55)
        lines.append("OPERATOR DECISION REQUIRED:")
        lines.append("  [1] ALLOW    - Grant explicit single-operator approval")
        lines.append("  [2] MODIFY   - Enforce suggested safer parameters")
        lines.append("  [3] DEFER    - Postpone action until surface link restored")
        lines.append("  [4] DENY     - Block action execution permanently (Default: Auto-deny in 60s)")
        lines.append("=" * 55)
        return "\n".join(lines)
