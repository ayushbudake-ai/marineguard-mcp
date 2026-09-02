"""
Shared Pydantic V2 Schemas for MarineGuard MCP
Covers both AUV debris detection and surface vessel fleet management domains.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    def __ge__(self, other: "RiskLevel") -> bool:
        order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
        return order[self] >= order[other]

    def __gt__(self, other: "RiskLevel") -> bool:
        order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
        return order[self] > order[other]

    def __le__(self, other: "RiskLevel") -> bool:
        order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
        return order[self] <= order[other]

    def __lt__(self, other: "RiskLevel") -> bool:
        order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
        return order[self] < order[other]


class SensorSpec(BaseModel):
    id: str
    name: str
    type: str  # sonar, bathymetry, optical, navigation, oceanographic
    sub_type: str
    frequency_khz: Optional[List[float]] = None
    swath_m: Optional[float] = None
    resolution_cm: Optional[float] = None
    fov_deg: Optional[float] = None
    fps: Optional[int] = None
    format: str
    lever_arm: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    status: str = "active"


class PlatformComms(BaseModel):
    acoustic_modem: str = "10 kbps"
    surface_link: str = "WiFi"


class PlatformSpec(BaseModel):
    id: str
    name: str
    type: str = "AUV"
    organization: str = "MoES"
    compute: str = "NVIDIA Jetson AGX Xavier"
    storage: str = "2 TB NVMe"
    comms: PlatformComms = Field(default_factory=PlatformComms)
    sensors: List[SensorSpec] = Field(default_factory=list)


class CapabilityRegistry(BaseModel):
    platform_name: str
    sensors_active: List[str]
    parsers_loaded: List[str]
    pipelines_configured: List[str]
    tools_emitted: List[Dict[str, Any]]
    fusion_weights: Dict[str, float]


class DebrisContact(BaseModel):
    contact_id: str
    sensor_id: str
    sensor_type: str
    raw_confidence: float
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    label_candidate: str
    acoustic_shadow_ratio: Optional[float] = None
    estimated_dimensions_m: Tuple[float, float, float] = (1.0, 1.0, 0.5)
    lat_lon: Tuple[float, float] = (13.0827, 80.2707)
    depth_m: float = 24.3


class DebrisField(BaseModel):
    field_id: str
    timestamp: float
    platform_id: str
    contacts: List[DebrisContact] = Field(default_factory=list)


class ClassifiedTarget(BaseModel):
    target_id: str
    species: str  # ghost_net, plastic_container, metal_debris, munition, unknown
    confidence: float
    sensor_contributions: Dict[str, float]
    geometry_m: Tuple[float, float, float]  # length, width, height
    lat_lon: Tuple[float, float]
    depth_m: float
    removal_priority: str  # HIGH, MEDIUM, LOW
    entanglement_risk: str  # HIGH, MEDIUM, LOW
    evidence_id: str


class Action(BaseModel):
    type: str
    description: str
    target_id: Optional[str] = None
    proposed_params: Dict[str, Any] = Field(default_factory=dict)
    consumes_reserve: float = 0.0  # percentage of battery/fuel consumed


class MissionContext(BaseModel):
    battery_reserve: float = 0.85  # 0.0 to 1.0
    acoustic_link_kbps: float = 10.0
    current_depth_m: float = 20.0
    speed_knots: float = 2.5
    usbl_lock: bool = True
    mission_time_remaining_min: int = 120


class FirewallDecision(BaseModel):
    allowed: bool
    requires_approval: bool
    requires_dual_approval: bool
    risk_level: RiskLevel
    reason: str
    suggested_modifications: Dict[str, Any] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    event_id: str
    timestamp: float
    stage: str
    input_summary: str
    output_summary: str
    model: str
    confidence: float
    reasoning: str
    evidence_overlay_path: Optional[str] = None


class SurveyJob(BaseModel):
    job_id: str
    platform_id: str
    survey_area_geojson: Dict[str, Any]
    status: str = "IN_PROGRESS"
    contacts_detected: int = 0
    targets_classified: int = 0
    classified_targets: List[ClassifiedTarget] = Field(default_factory=list)
    start_time: float
    end_time: Optional[float] = None


# =============================================================================
# VESSEL FLEET MANAGEMENT SCHEMAS
# =============================================================================

class OperatingMode(str, Enum):
    NORMAL = "NORMAL"
    STANDBY = "STANDBY"
    PATROL = "PATROL"
    EMERGENCY = "EMERGENCY"
    MAINTENANCE = "MAINTENANCE"
    DOCKED = "DOCKED"


class VesselEngineStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"


class VesselStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"
    DOCKED = "DOCKED"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class UserRole(str, Enum):
    VIEWER = "VIEWER"
    OPERATOR = "OPERATOR"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class PolicyDecision(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    CANCELLED = "CANCELLED"


class Vessel(BaseModel):
    vessel_id: str
    vessel_name: str
    status: VesselStatus
    latitude: float
    longitude: float
    speed: float                   # knots
    heading: float                 # degrees 0-360
    fuel_level: float              # percentage 0-100
    engine_temperature: float      # Celsius
    engine_status: VesselEngineStatus
    current_mode: OperatingMode
    crew_count: int = 0
    cargo_description: str = ""
    last_updated: str              # ISO timestamp string


class Alert(BaseModel):
    alert_id: str
    vessel_id: str
    vessel_name: str
    severity: AlertSeverity
    alert_type: str
    reason: str
    recommended_action: str
    timestamp: str
    status: AlertStatus = AlertStatus.ACTIVE


class WeatherData(BaseModel):
    location_lat: float
    location_lon: float
    condition: str
    wind_speed_knots: float
    wind_direction: str
    wave_height_m: float
    visibility_km: float
    severity: AlertSeverity
    forecast: str
    timestamp: str


class FleetSummary(BaseModel):
    total_vessels: int
    operational: int
    warning: int
    critical: int
    offline: int
    active_alerts: int
    vessels_requiring_attention: List[str]
    timestamp: str


class AuditRecord(BaseModel):
    record_id: str
    timestamp: str
    session_id: str
    user_role: str
    user_request: str
    tool_name: str
    tool_input: Dict[str, Any]
    risk_level: str
    permission_required: str
    policy_decision: str
    confirmation_required: bool
    confirmation_status: str        # PENDING / APPROVED / DENIED / N/A
    execution_status: str
    result_summary: str
    reasoning: str


class ConfirmationRequest(BaseModel):
    confirmation_id: str
    tool_name: str
    tool_input: Dict[str, Any]
    risk_level: str
    reason: str
    permission_required: str
    potential_impact: str
    requested_by: str
    timestamp: str
    status: str = "PENDING"         # PENDING / APPROVED / DENIED


class ToolCapability(BaseModel):
    tool_name: str
    description: str
    input_params: Dict[str, str]
    output_description: str
    tool_type: str                  # READ / WRITE
    risk_level: str
    required_permission: str
    requires_confirmation: bool
    example_request: str
