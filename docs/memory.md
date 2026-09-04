# Project Memory / Decision Log

**Project:** MarineGuard — Automated Underwater Marine Debris Detection  
**Purpose:** Preserve engineering context, architectural pivots, and rationale across sprint transitions.

---

## 1. Key Decision: Scope Correction

The initial prototype implementation ("MarineGuard MCP") was architected around an expansive autonomous vehicle agent concept comprising:
* An MCP agent tool server with real-time natural language reasoning.
* A multi-platform sensor-suite compiler supporting hot-swappable AUV specifications.
* A Mission Safety Firewall with dynamic risk taxonomy and operator approval gating for physical vehicle maneuvers (altitude descent, course alterations, mission abort).
* Specialized IHO S-100 hydrographic catalogue exporters.

### Evaluation against SIH26057
Upon rigorous comparison against the official **SIH26057** problem statement issued by the **Ministry of Earth Sciences (MoES)**:
* The core challenge is strictly focused on **automated side-scan sonar marine debris detection**, **false-positive filtering**, **geotagged reporting**, and an **operator review dashboard**.
* The problem statement contains **no requirement for autonomous AUV flight control**, thruster management, natural language agent interfaces, or maritime hydrographic chart production.

### Final Decision
Re-scope the project to match the true problem statement:
1. **Focus 100% of core development** on the computer vision and acoustic processing pipeline (Preprocessing $\to$ Detection $\to$ Filtering $\to$ Geotagging $\to$ Reporting).
2. **De-scope / Freeze legacy modules:** Retain the sensor compiler and multi-sensor fusion engines as frozen secondary assets (mentioned as pitch asides); remove Mission Firewall, S-100 export, and simulated telemetry sliders from the critical deliverable path (`rules.md §1 & §5`).

---

## 2. Corrections Carried Forward

| Item | Original Claim / Implementation | Corrected Formulation | Reason / Evidence |
|:---|:---|:---|:---|
| **Primary Platform Naming** | "Matsya-6000 AUV" | **"Sagar Netra"** (Fictional AUV-01) | *Matsya 6000* is India's real human-occupied deep-submergence vehicle under the Deep Ocean Mission, not an autonomous unmanned AUV. The platform name was corrected in `data/sensor_specs/sagar_netra.yaml`. |
| **Competition Fit Score** | "28.5 / 30" | **Removed** | No official hackathon rubric publishes this score; speculative claims violate project honesty rules. |
| **Theme Tag Pairing** | "Renewable / Sustainable Energy" | **Flagged for verification** | Needs direct re-verification on the official SIH portal before final submission. |
| **Model Completeness Claim** | Self-reported "100% Complete & Verified" manifest | **Removed / Flagged for Deletion** | See Repo Hygiene Note below. |

---

## 3. What Was Kept from the Original Build (and Why)

* **Explainable Trace & Evidence Overlay (`marineguard/trace/`):** Repurposed as the explainability and false-positive filter auditing layer. Provides visual and reasoning transparency into why an acoustic anomaly was accepted or rejected.
* **Multi-Sensor Fusion Engine (`marineguard/detection/fusion.py`):** Retained as a secondary accuracy booster when optical or bathymetric auxiliary feeds are present alongside primary side-scan sonar.
* **Sensor-Suite Compiler (`marineguard/compiler/`):** Frozen and retained as a one-line architectural asset demonstrating multi-platform adaptability.
* **GeoJSON GIS Exporter (`marineguard/exporters/geojson_export.py`):** Retained as a standard GIS bonus export format alongside primary JSON/CSV outputs.
* **Frame Replay Harness (`data/test_data/sample_frames.py`):** Retained as the testing and demonstration mechanism for offline operation without requiring live maritime vessels.

---

## 4. What Was Dropped from Active Scope (and Why)

* **Mission Firewall (`marineguard/firewall/`):** Excluded because physical vehicle control (course changes, thruster overrides) is not part of SIH26057.
* **MCP Natural-Language Agent Server:** Excluded to eliminate non-deterministic conversational routing in favor of high-throughput signal processing.
* **Live Platform Hot-Swapping:** Static YAML spec configuration is sufficient for demonstration.
* **IHO S-100 Hydrographic Export:** Specialized hydrographic standard; standard GeoJSON and CSV provide superior utility for debris clearance authorities.
* **Simulated Telemetry Sliders:** Removed to eliminate distracting and unneeded UI controls (battery %, comms link).

---

## 5. Repository Hygiene Note

`COMPLETE_MARINEGUARD_CODEBASE.py` in the root repository self-reported a "100% COMPLETE & VERIFIED" status. Inspection revealed that this file is a non-functional static text manifest containing commented-out schemas and claims without attached test evidence. In accordance with `rules.md §3` (Metrics Honesty), this file is flagged as an obsolete manifest and marked for deletion in Phase 3. Real test output (`pytest`) and empirical benchmarks represent the sole acceptable evidence of completeness.

---

## 6. Current Implementation State Snapshot

* **Model Training:** In transition. Legacy code uses 1D CA-CFAR heuristic; real YOLOv8-seg model training on public datasets is scheduled for Phase 1/2.
* **Confidence Filtering:** Partially implemented via late-fusion weighting; Platt calibration and geometric shadow-ratio filters scheduled for Phase 2.
* **Geotagging & Report Exporter:** Partially implemented (GeoJSON/PDF working; dedicated Phase 0 JSON/CSV exporter scheduled for Phase 3).
* **Dashboard Workflow:** Functional prototype (`streamlit_demo.py`) with telemetry sliders; upload-based refactor scheduled for Phase 3.
* **Frozen / Reusable Assets:** Compiler, GeoJSON exporter, replay harness, and trace visualizer are fully verified and passing unit tests.
