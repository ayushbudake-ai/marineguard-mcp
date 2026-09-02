"""
Sensor Spec Sheet Parser for MarineGuard MCP Compiler
"""

import os
import yaml
from typing import Union
from marineguard.schemas import PlatformSpec, SensorSpec, PlatformComms


class SensorParser:
    """Parses platform spec sheets (YAML/JSON) into PlatformSpec models."""

    def parse(self, source: Union[str, dict]) -> PlatformSpec:
        if isinstance(source, str):
            if not os.path.exists(source):
                raise FileNotFoundError(f"Platform spec file not found: {source}")
            with open(source, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif isinstance(source, dict):
            data = source
        else:
            raise ValueError("Source must be a file path string or a dictionary.")

        platform_data = data.get("platform", {})
        sensors_raw = data.get("sensors", [])

        sensors = []
        for s in sensors_raw:
            sensors.append(
                SensorSpec(
                    id=s["id"],
                    name=s["name"],
                    type=s["type"],
                    sub_type=s.get("sub_type", "generic"),
                    frequency_khz=s.get("frequency_khz"),
                    swath_m=s.get("swath_m"),
                    resolution_cm=s.get("resolution_cm"),
                    fov_deg=s.get("fov_deg"),
                    fps=s.get("fps"),
                    format=s.get("format", "RAW"),
                    lever_arm=s.get("lever_arm", [0.0, 0.0, 0.0]),
                    status=s.get("status", "active"),
                )
            )

        comms_data = platform_data.get("comms", {})
        comms = PlatformComms(
            acoustic_modem=comms_data.get("acoustic_modem", "10 kbps"),
            surface_link=comms_data.get("surface_link", "WiFi"),
        )

        return PlatformSpec(
            id=platform_data.get("id", "unknown_platform"),
            name=platform_data.get("name", "Unknown Platform"),
            type=platform_data.get("type", "AUV"),
            organization=platform_data.get("organization", "MoES"),
            compute=platform_data.get("compute", "Standard Compute"),
            storage=platform_data.get("storage", "1 TB NVMe"),
            comms=comms,
            sensors=sensors,
        )
