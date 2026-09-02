"""
Pipeline Generator for MarineGuard MCP Compiler
"""

from typing import List, Dict, Any
from marineguard.schemas import PlatformSpec, SensorSpec


class PipelineGenerator:
    """Auto-configures AI detection pipelines based on platform sensor suite."""

    def generate_pipelines(self, platform: PlatformSpec) -> Dict[str, Dict[str, Any]]:
        pipelines = {}

        for sensor in platform.sensors:
            if sensor.status != "active":
                continue

            if sensor.sub_type == "side_scan":
                pipelines[sensor.id] = {
                    "sensor_name": sensor.name,
                    "pipeline_type": "side_scan_waterfall",
                    "models": ["CFAR_Anomaly_Detector", "YOLOv8_Seg_Sonar"],
                    "input_format": sensor.format,
                    "target_resolution_cm": sensor.resolution_cm or 5.0,
                    "fusion_weight": 0.40,
                }
            elif sensor.sub_type == "sas":
                pipelines[sensor.id] = {
                    "sensor_name": sensor.name,
                    "pipeline_type": "interferometric_sas",
                    "models": ["Phase_Amplitude_Interferometry", "SAS_MicroDebris_Detector"],
                    "input_format": sensor.format,
                    "target_resolution_cm": sensor.resolution_cm or 3.0,
                    "fusion_weight": 0.50,
                }
            elif sensor.type == "optical":
                pipelines[sensor.id] = {
                    "sensor_name": sensor.name,
                    "pipeline_type": "underwater_optical",
                    "models": ["RT_DETR_Optical", "SAM2_Tiny_Segmenter"],
                    "input_format": sensor.format,
                    "fov_deg": sensor.fov_deg or 120.0,
                    "fusion_weight": 0.35,
                }
            elif sensor.type == "bathymetry":
                pipelines[sensor.id] = {
                    "sensor_name": sensor.name,
                    "pipeline_type": "multibeam_bathymetry",
                    "models": ["MBES_Surface_Anomaly_Extractor", "Voxel_Grid_CrossRef"],
                    "input_format": sensor.format,
                    "fusion_weight": 0.25,
                }

        return pipelines
