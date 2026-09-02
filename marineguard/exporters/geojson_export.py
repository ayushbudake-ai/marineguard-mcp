"""
GeoJSON FeatureCollection Exporter for MarineGuard MCP
"""

import json
from typing import List, Dict, Any
from marineguard.schemas import ClassifiedTarget


class GeoJSONExporter:
    """Exports debris targets to standard GeoJSON GIS FeatureCollections."""

    def export(self, targets: List[ClassifiedTarget], output_file: str = None) -> Dict[str, Any]:
        features = []
        for t in targets:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [t.lat_lon[1], t.lat_lon[0]],  # lon, lat
                },
                "properties": {
                    "target_id": t.target_id,
                    "species": t.species,
                    "confidence": t.confidence,
                    "depth_m": t.depth_m,
                    "dimensions_m": f"{t.geometry_m[0]}x{t.geometry_m[1]}x{t.geometry_m[2]}",
                    "removal_priority": t.removal_priority,
                    "entanglement_risk": t.entanglement_risk,
                    "sensor_contributions": t.sensor_contributions,
                },
            }
            features.append(feature)

        collection = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(collection, f, indent=2)

        return collection
