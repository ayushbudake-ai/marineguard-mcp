"""
Multi-Sensor Late Fusion Engine for MarineGuard MCP
"""

from typing import List, Dict, Any
from marineguard.schemas import DebrisContact, ClassifiedTarget


class MultiSensorFusionEngine:
    """Confidence-Weighted Late Fusion Engine across Sonar, Optical, and Bathymetry."""

    DEFAULT_WEIGHTS = {
        "side_scan": 0.40,
        "sas": 0.50,
        "optical": 0.35,
        "bathymetry": 0.25,
    }

    LABEL_NAME_MAP = {
        "ghost_net": "Ghost Net Cluster (Entangled Nylon Netting)",
        "plastic_container": "Industrial HDPE Plastic Container Field",
        "metal_debris": "Sunken Steel Cable & Metal Structures",
        "munition": "Submerged Explosive Ordnance / Casing",
        "unknown": "Unclassified Marine Anomaly",
    }

    ENTANGLEMENT_RISKS = {
        "ghost_net": "HIGH",
        "plastic_container": "MEDIUM",
        "metal_debris": "LOW",
        "munition": "CRITICAL",
    }

    REMOVAL_PRIORITIES = {
        "ghost_net": "HIGH",
        "plastic_container": "MEDIUM",
        "metal_debris": "LOW",
        "munition": "HIGH",
    }

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    def fuse(self, contacts: List[DebrisContact]) -> ClassifiedTarget:
        if not contacts:
            raise ValueError("Cannot perform fusion on empty contact list.")

        contributions = {}
        weighted_score_sum = 0.0
        weight_total = 0.0

        ref_contact = contacts[0]
        species_raw = ref_contact.label_candidate

        for c in contacts:
            w = self.weights.get(c.sensor_type, 0.30)
            weighted_score_sum += c.raw_confidence * w
            weight_total += w
            contributions[c.sensor_type] = round(c.raw_confidence, 3)

        fused_confidence = round(weighted_score_sum / weight_total, 3) if weight_total > 0 else 0.80

        # Multi-sensor boost (+0.05 if >= 2 sensors confirm target)
        if len(contributions) >= 2:
            fused_confidence = min(0.99, fused_confidence + 0.05)

        species_clean = self.LABEL_NAME_MAP.get(species_raw, species_raw)
        entanglement = self.ENTANGLEMENT_RISKS.get(species_raw, "MEDIUM")
        priority = self.REMOVAL_PRIORITIES.get(species_raw, "MEDIUM")

        target_id = f"TARGET_{ref_contact.contact_id.split('_')[-1]}"

        return ClassifiedTarget(
            target_id=target_id,
            species=species_clean,
            confidence=round(fused_confidence, 3),
            sensor_contributions=contributions,
            geometry_m=ref_contact.estimated_dimensions_m,
            lat_lon=ref_contact.lat_lon,
            depth_m=ref_contact.depth_m,
            removal_priority=priority,
            entanglement_risk=entanglement,
            evidence_id=f"EVIDENCE_{target_id}",
        )
