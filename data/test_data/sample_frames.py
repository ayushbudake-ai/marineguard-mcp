"""
Synthetic Dataset Streamer and Frame Replay Harness for MarineGuard MCP
"""

import time
import numpy as np
from typing import Dict, Any, List


class FrameReplayHarness:
    """Generates synthetic sonar waterfall, optical RGB frame, and MBES bathymetry depth grid."""

    SAMPLE_TARGETS = [
        {
            "id": "Contact_01",
            "type": "ghost_net",
            "label": "Ghost Net Cluster (Entangled Nylon)",
            "sonar_db": -18.5,
            "shadow_ratio": 0.35,
            "dimensions_m": (12.0, 8.0, 0.5),
            "lat_lon": (13.0835, 80.2715),
            "depth_m": 24.3,
            "sonar_confidence": 0.91,
            "optical_confidence": 0.86,
            "bathymetry_anomaly_m": 0.45,
        },
        {
            "id": "Contact_02",
            "type": "plastic_container",
            "label": "Industrial HDPE Plastic Drum Field",
            "sonar_db": -12.0,
            "shadow_ratio": 0.20,
            "dimensions_m": (2.5, 1.8, 1.2),
            "lat_lon": (13.0842, 80.2728),
            "depth_m": 25.1,
            "sonar_confidence": 0.84,
            "optical_confidence": 0.89,
            "bathymetry_anomaly_m": 1.15,
        },
        {
            "id": "Contact_03",
            "type": "metal_debris",
            "label": "Sunken Steel Cable Spool & Frames",
            "sonar_db": -8.2,
            "shadow_ratio": 0.42,
            "dimensions_m": (3.8, 3.0, 2.1),
            "lat_lon": (13.0850, 80.2741),
            "depth_m": 23.8,
            "sonar_confidence": 0.94,
            "optical_confidence": 0.78,
            "bathymetry_anomaly_m": 2.05,
        },
        {
            "id": "Contact_04",
            "type": "munition",
            "label": "Submerged Metallic Shell Casing",
            "sonar_db": -6.5,
            "shadow_ratio": 0.50,
            "dimensions_m": (1.2, 0.4, 0.4),
            "lat_lon": (13.0858, 80.2755),
            "depth_m": 26.0,
            "sonar_confidence": 0.88,
            "optical_confidence": 0.72,
            "bathymetry_anomaly_m": 0.38,
        },
    ]

    def __init__(self):
        self.frame_index = 0

    def get_next_ping(self) -> Dict[str, Any]:
        """Returns next frame ping payload across side-scan, optical, and bathymetry."""
        idx = self.frame_index % len(self.SAMPLE_TARGETS)
        target = self.SAMPLE_TARGETS[idx]
        self.frame_index += 1

        # Generate synthetic side-scan waterfall array (256 x 256)
        sonar_img = np.random.normal(loc=40, scale=10, size=(256, 256)).astype(np.uint8)
        # Inject acoustic highlight and shadow
        sonar_img[100:150, 100:150] = np.random.normal(loc=220, scale=15, size=(50, 50)).astype(np.uint8)
        sonar_img[150:200, 100:150] = np.random.normal(loc=5, scale=3, size=(50, 50)).astype(np.uint8)

        # Generate synthetic optical crop (128 x 128 x 3)
        optical_img = np.random.normal(loc=80, scale=20, size=(128, 128, 3)).astype(np.uint8)

        # Generate synthetic MBES bathymetry grid (32 x 32)
        bathy_grid = np.full((32, 32), fill_value=target["depth_m"], dtype=np.float32)
        bathy_grid[12:20, 12:20] -= target["bathymetry_anomaly_m"]

        return {
            "ping_id": f"PING_{int(time.time())}_{self.frame_index}",
            "timestamp": time.time(),
            "target_meta": target,
            "sonar_waterfall": sonar_img,
            "optical_crop": optical_img,
            "bathymetry_grid": bathy_grid,
        }
