"""
IHO S-100 Universal Hydrographic Feature Catalogue Exporter
"""

import json
from typing import List, Dict, Any
from marineguard.schemas import ClassifiedTarget


class S100Exporter:
    """Exports hydrographic survey data compliant with IHO S-100 standards."""

    def export(self, targets: List[ClassifiedTarget], output_file: str = None) -> Dict[str, Any]:
        hydrographic_features = []
        for t in targets:
            feature_code = "Obstruction" if t.removal_priority == "HIGH" else "UnderwaterWreckOrDebris"
            hydrographic_features.append({
                "featureIdentifier": t.target_id,
                "s100FeatureCode": feature_code,
                "categoryOfObstruction": t.species,
                "depthValuation": t.depth_m,
                "qualityOfSoundingMeasurement": "EvaluatedByMultiSensorFusion",
                "horizontalAccuracyMeters": 0.1,
                "position": {
                    "latitude": t.lat_lon[0],
                    "longitude": t.lat_lon[1],
                },
                "hazardSeverity": t.entanglement_risk,
                "evidenceTraceId": t.evidence_id,
            })

        catalog = {
            "s100Header": {
                "specification": "IHO S-100 Universal Hydrographic Data Model",
                "edition": "5.0.0",
                "datasetTitle": "MoES MarineGuard Autonomous Underwater Debris Survey",
                "producer": "Ministry of Earth Sciences (MoES) MarineGuard MCP Agent",
                "compliance": "S-102 Bathymetry & S-124 Navigational Warnings",
            },
            "features": hydrographic_features,
        }

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(catalog, f, indent=2)

        return catalog
