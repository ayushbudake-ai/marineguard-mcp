"""
Sensor Geometry & Spatial Solver for MarineGuard MCP Compiler
"""

import math
from typing import Tuple, List, Dict, Any
from marineguard.schemas import SensorSpec


class GeometrySolver:
    """Solves sensor lever arms, beam swath footprints, time sync, and acoustic-to-latlon transformations."""

    DEFAULT_SOUND_SPEED_MPS = 1500.0  # m/s in seawater

    def calculate_sensor_position(
        self, auv_pose: Dict[str, float], sensor: SensorSpec
    ) -> Dict[str, float]:
        """Calculates absolute sensor coordinate considering vehicle pose and lever arm offsets."""
        lat = auv_pose.get("lat", 13.0827)
        lon = auv_pose.get("lon", 80.2707)
        depth = auv_pose.get("depth_m", 20.0)
        heading_deg = auv_pose.get("heading_deg", 90.0)

        dx, dy, dz = sensor.lever_arm

        # Convert local NED lever arm offsets based on heading
        rad = math.radians(heading_deg)
        north_offset = dx * math.cos(rad) - dy * math.sin(rad)
        east_offset = dx * math.sin(rad) + dy * math.cos(rad)

        # 1 deg latitude ~ 111,000 m; 1 deg longitude ~ 111,000 * cos(lat) m
        lat_per_m = 1.0 / 111000.0
        lon_per_m = 1.0 / (111000.0 * math.cos(math.radians(lat)))

        sensor_lat = lat + (north_offset * lat_per_m)
        sensor_lon = lon + (east_offset * lon_per_m)
        sensor_depth = max(0.0, depth + dz)

        return {
            "sensor_id": sensor.id,
            "lat": round(sensor_lat, 7),
            "lon": round(sensor_lon, 7),
            "depth_m": round(sensor_depth, 2),
        }

    def compute_swath_coverage(
        self, sensor: SensorSpec, altitude_m: float
    ) -> Tuple[float, float]:
        """Computes effective swath width (meters) and spatial resolution (cm) at given altitude."""
        if sensor.type == "sonar":
            swath = sensor.swath_m if sensor.swath_m else 2.0 * altitude_m * math.tan(math.radians(60.0))
            res = sensor.resolution_cm if sensor.resolution_cm else 5.0
        elif sensor.type == "optical":
            fov = sensor.fov_deg if sensor.fov_deg else 90.0
            swath = 2.0 * altitude_m * math.tan(math.radians(fov / 2.0))
            res = (swath / 3840.0) * 100.0  # 4K horizontal pixels
        elif sensor.type == "bathymetry":
            swath = sensor.swath_m if sensor.swath_m else 3.5 * altitude_m
            res = sensor.resolution_cm if sensor.resolution_cm else 10.0
        else:
            swath = 10.0
            res = 10.0

        return round(swath, 2), round(res, 2)

    def Correct_sound_speed(self, ctd_temp_c: float, ctd_salinity_ppt: float, depth_m: float) -> float:
        """Mackenzie formula for sound speed in seawater (m/s)."""
        T = ctd_temp_c
        S = ctd_salinity_ppt
        D = depth_m
        c = (
            1448.96
            + 4.591 * T
            - 0.05304 * (T**2)
            + 2.374e-4 * (T**3)
            + 1.340 * (S - 35)
            + 0.0163 * D
            + 1.675e-7 * (D**2)
            - 0.01025 * T * (S - 35)
            - 7.139e-13 * T * (D**3)
        )
        return round(c, 2)
