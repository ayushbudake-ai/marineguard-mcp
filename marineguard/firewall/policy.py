"""
Dynamic Policy Engine for MarineGuard MCP Mission Firewall
"""

from marineguard.schemas import Action, MissionContext, FirewallDecision, RiskLevel
from marineguard.firewall.risk_taxonomy import RiskTaxonomy


class MissionFirewallPolicy:
    """Dynamic Risk Policy Engine enforcing safety boundaries on AUV actions."""

    RISK_ORDER = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]

    def __init__(self, battery_min: float = 0.25, comms_min_kbps: float = 5.0):
        self.battery_min = battery_min
        self.comms_min_kbps = comms_min_kbps
        self.taxonomy = RiskTaxonomy()

    def check_action(self, action: Action, context: MissionContext) -> FirewallDecision:
        base_risk = self.taxonomy.evaluate_base_risk(action)

        # Calculate dynamic risk escalations
        risk_index = self.RISK_ORDER.index(base_risk)
        reasons = [f"Base Action Risk: {base_risk.value}"]

        if context.battery_reserve < 0.30:
            risk_index = min(len(self.RISK_ORDER) - 1, risk_index + 1)
            reasons.append(f"Low Battery Reserve ({context.battery_reserve*100:.0f}% < 30%)")

        if context.acoustic_link_kbps < self.comms_min_kbps:
            risk_index = min(len(self.RISK_ORDER) - 1, risk_index + 1)
            reasons.append(f"Degraded Acoustic Comms Link ({context.acoustic_link_kbps:.1f} kbps < {self.comms_min_kbps} kbps)")

        if action.consumes_reserve > 0.10:
            risk_index = min(len(self.RISK_ORDER) - 1, risk_index + 1)
            reasons.append(f"High Reserve Consumption ({action.consumes_reserve*100:.0f}% > 10%)")

        final_risk = self.RISK_ORDER[risk_index]

        allowed = (final_risk == RiskLevel.LOW)
        requires_approval = (final_risk in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL])
        requires_dual_approval = (final_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL])

        suggested_mods = {}
        if final_risk >= RiskLevel.MEDIUM:
            suggested_mods = {
                "max_station_keep_min": 5,
                "min_altitude_m": 8.0,
                "require_surface_reconnect": context.battery_reserve < 0.30,
            }

        return FirewallDecision(
            allowed=allowed,
            requires_approval=requires_approval,
            requires_dual_approval=requires_dual_approval,
            risk_level=final_risk,
            reason=" | ".join(reasons),
            suggested_modifications=suggested_mods,
        )
