"""
Action Risk Taxonomy for MarineGuard MCP Mission Firewall
"""

from marineguard.schemas import RiskLevel, Action


class RiskTaxonomy:
    """Formal Risk Taxonomy mapping platform actions to risk tiers."""

    ACTION_MAP = {
        "read_telemetry": RiskLevel.LOW,
        "run_inference": RiskLevel.LOW,
        "generate_report": RiskLevel.LOW,
        "start_survey": RiskLevel.LOW,
        "request_course_change": RiskLevel.MEDIUM,
        "request_altitude_change": RiskLevel.MEDIUM,
        "station_keep": RiskLevel.MEDIUM,
        "deploy_marker": RiskLevel.HIGH,
        "close_inspection": RiskLevel.HIGH,
        "abort_mission": RiskLevel.CRITICAL,
        "override_thrusters": RiskLevel.CRITICAL,
    }

    def evaluate_base_risk(self, action: Action) -> RiskLevel:
        return self.ACTION_MAP.get(action.type, RiskLevel.CRITICAL)
