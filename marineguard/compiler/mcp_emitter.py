"""
MCP Tool Emitter for MarineGuard MCP Compiler
"""

from typing import List, Dict, Any
from marineguard.schemas import PlatformSpec, CapabilityRegistry
from marineguard.compiler.sensor_parser import SensorParser
from marineguard.compiler.pipeline_generator import PipelineGenerator


class MCPEmitter:
    """Emits MCP tool definitions and compiles platform CapabilityRegistry."""

    BASE_TOOLS = [
        {
            "name": "marine_debris_survey",
            "description": "Execute autonomous marine debris detection survey on any equipped platform.",
            "parameters": {
                "platform": "Platform identifier or YAML spec file path",
                "survey_area": "GeoJSON Polygon of survey bounds",
                "objectives": "List of targets e.g. ['ghost_nets', 'plastics', 'metal', 'munitions']",
            },
        },
        {
            "name": "generate_debris_map",
            "description": "Generate spatial debris density map and removal priority grid.",
            "parameters": {"format": "GeoJSON, PDF, Shapefile, S-100"},
        },
        {
            "name": "trigger_close_inspection",
            "description": "Request AUV to alter course/altitude for close-range optical verification.",
            "parameters": {"target_id": "Target contact identifier", "altitude_m": "Target altitude"},
        },
        {
            "name": "export_report",
            "description": "Export survey results to MoES PDF, GeoJSON, or IHO S-100 format.",
            "parameters": {"export_format": "PDF / GeoJSON / S-100"},
        },
    ]

    def compile(self, platform: PlatformSpec) -> CapabilityRegistry:
        generator = PipelineGenerator()
        pipelines = generator.generate_pipelines(platform)

        tools = list(self.BASE_TOOLS)
        parsers_loaded = []
        active_sensors = []
        fusion_weights = {}

        for sensor in platform.sensors:
            if sensor.status != "active":
                continue

            active_sensors.append(f"{sensor.name} ({sensor.type})")
            if sensor.format not in parsers_loaded:
                parsers_loaded.append(sensor.format)

            if sensor.sub_type == "side_scan":
                tools.append({
                    "name": "start_side_scan_survey",
                    "description": f"Run side-scan sonar waterfall detection using {sensor.name}",
                    "parameters": {"frequency_khz": sensor.frequency_khz, "swath_m": sensor.swath_m},
                })
                tools.append({
                    "name": "detect_debris_sonar",
                    "description": f"Execute CFAR + YOLOv8-seg detection on {sensor.name} waterfall data",
                    "parameters": {"confidence_threshold": 0.5},
                })
                fusion_weights["sonar"] = 0.40

            elif sensor.sub_type == "sas":
                tools.append({
                    "name": "start_sas_survey",
                    "description": f"Run synthetic aperture sonar survey using {sensor.name}",
                    "parameters": {"swath_m": sensor.swath_m, "resolution_cm": sensor.resolution_cm},
                })
                tools.append({
                    "name": "detect_debris_sas",
                    "description": f"Execute high-res SAS interferometric detection using {sensor.name}",
                    "parameters": {"resolution_cm": sensor.resolution_cm},
                })
                fusion_weights["sas"] = 0.50

            elif sensor.type == "optical":
                tools.append({
                    "name": "detect_debris_optical",
                    "description": f"Run RT-DETR + SAM2 optical debris detection using {sensor.name}",
                    "parameters": {"fov_deg": sensor.fov_deg, "fps": sensor.fps},
                })
                fusion_weights["optical"] = 0.35

            elif sensor.type == "bathymetry":
                tools.append({
                    "name": "start_bathymetry_mapping",
                    "description": f"Execute 3D bathymetric anomaly mapping using {sensor.name}",
                    "parameters": {"swath_m": sensor.swath_m},
                })
                fusion_weights["bathymetry"] = 0.25

        tools.append({
            "name": "classify_target",
            "description": "Fuse multi-sensor detections into classified debris targets with confidence scores",
            "parameters": {"fusion_strategy": "confidence_weighted_late"},
        })

        return CapabilityRegistry(
            platform_name=platform.name,
            sensors_active=active_sensors,
            parsers_loaded=parsers_loaded,
            pipelines_configured=list(pipelines.keys()),
            tools_emitted=tools,
            fusion_weights=fusion_weights,
        )

    def print_compile_summary(self, registry: CapabilityRegistry) -> str:
        """Returns clean formatted terminal summary of platform compilation."""
        lines = []
        lines.append("PLATFORM DISCOVERED")
        lines.append("-" * 40)
        lines.append(f"Platform: {registry.platform_name}")
        lines.append(f"Sensors Active: {len(registry.sensors_active)}")
        lines.append(f"Parsers Loaded: {', '.join(registry.parsers_loaded)}")
        lines.append("-" * 40)
        lines.append("COMPILED TOOLS:")
        for t in registry.tools_emitted:
            lines.append(f"[OK] {t['name']}()")
        return "\n".join(lines)
