# Project Requirement Document (PRD)

**Project:** MarineGuard — Automated Underwater Marine Debris Detection  
**Problem Statement ID:** SIH26057  
**Ministry:** Ministry of Earth Sciences (MoES)  
**Category:** Software  

---

## 1. Problem Statement

Anthropogenic debris — especially abandoned, lost, or discarded fishing gear ("ghost nets") — poses severe threats to marine ecosystems, trapping marine wildlife, destroying coral reefs, and endangering vessel navigation. Side-Scan Sonar (SSS), deployed via towfish or Autonomous Underwater Vehicles (AUVs), produces wide-swath acoustic seafloor imagery. However, manual inspection of thousands of kilometers of sonar logs is exceptionally slow, labor-intensive, and prone to human error. Debris signatures frequently blend into natural seafloor topographies such as rock outcrops, sand ripples, and bathymetric ridges. The mission is to automate marine debris detection and characterization using advanced computer vision and acoustic signal processing.

---

## 2. Objective

Design, train, and deploy an end-to-end computer vision and signal processing pipeline that:
1. Ingests raw side-scan sonar (SSS) imagery and survey logs.
2. Accurately identifies and segments man-made debris against noisy natural seafloor backgrounds.
3. Suppresses false positives from acoustic shadows and natural formations using geometric and acoustic heuristics.
4. Outputs actionable, geotagged, structured anomaly reports (JSON/CSV) for downstream retrieval operations.
5. Operates on edge/embedded compute hardware without mandatory cloud connectivity.

---

## 3. In Scope

* **Detection & Segmentation:** Computer vision model trained to identify man-made marine debris (ghost nets, plastic containers/drums, metal debris/cables, pipes, munitions, shipwrecks) in sonar waterfall imagery.
* **Signal Robustness:** Preprocessing techniques addressing acoustic speckle noise, resolution variance, dynamic acoustic shadows, and vehicle motion dropout (heave, pitch, roll).
* **Confidence Scoring & Calibration:** Calibrated confidence scoring (0–100%) and false-positive suppression against natural geological features (rocks, sand bars, acoustic shadow dropouts).
* **Structured Anomaly Reporting:** Automated export of standardized JSON and CSV survey reports containing coordinates (lat/lon), bounding dimensions, classification, and confidence per contact.
* **User Dashboard:** Interactive web-based dashboard allowing operators to upload sonar logs/images, view visual detection overlays, inspect GIS spatial distribution, and download survey reports.
* **Edge Optimization:** Model export to open runtime standards (ONNX) for embedded edge deployment on survey platforms.

---

## 4. Out of Scope (Explicitly Dropped Scope)

Per architectural review and `rules.md §1 & §5`, the following components from earlier prototype concepts are outside the scored SIH26057 requirements and are excluded from the core pipeline:

* **Vehicle Control & Actuation:** Autonomous vehicle maneuvering, thruster override, station keeping, or emergency ascent logic (the problem statement defines an analytics and reporting pipeline, not an AUV flight controller).
* **Mission Safety Firewall:** Real-time battery/communications gating and operator approval workflows for physical vehicle actions.
* **Natural-Language MCP Agent Interface:** Natural-language agent routing layer (focus remains on deterministic CV inference and structured exports).
* **Dynamic Multi-Platform Compiler:** Real-time platform hot-swapping beyond static YAML configuration ingestion.
* **Hydrographic S-100 Export:** Full IHO S-100/S-102 electronic navigational chart production (standard GIS GeoJSON/CSV suffices for MoES debris clearance).
* **Live Telemetry Simulation:** UI battery percentage and acoustic modem throughput sliders.

---

## 5. Functional Requirements

| ID | Requirement Statement | Status in Repository |
|:---|:---|:---|
| **FR1** | System shall accept uploaded raw sonar images and survey logs as primary input. | Planned (Streamlit upload flow refactor) |
| **FR2** | System shall run a detection/segmentation model on the input to generate bounding boxes or masks. | Partially Implemented (CA-CFAR heuristic & synthetic metadata; YOLOv8-seg ONNX planned) |
| **FR3** | System shall assign a calibrated confidence score (0–100%) to each detected contact. | Partially Implemented (Late-fusion heuristic; Platt calibration planned) |
| **FR4** | System shall filter false positives arising from rocks and acoustic shadows using geometric heuristics. | Partially Implemented (Aspect-ratio & shadow heuristic planned in Phase 2) |
| **FR5** | System shall parse sonar metadata / navigation ping headers to geotag each contact with latitude and longitude. | Partially Implemented (Mock coordinates in harness; ping header parser planned) |
| **FR6** | System shall export structured survey reports in JSON and CSV formats according to the frozen Phase 0 schema. | Partially Implemented (GeoJSON/PDF implemented; JSON/CSV report conforming to Phase 0 schema in development) |
| **FR7** | System shall visually overlay detected bounding boxes, masks, and classification tags on sonar imagery in the UI. | Implemented (Evidence overlay generator & Streamlit view) |
| **FR8** | System shall allow survey report and dataset download directly from the dashboard. | Implemented (Download buttons in Streamlit) |

---

## 6. Non-Functional Requirements

| ID | Requirement Statement | Target | Repository Reality |
|:---|:---|:---|:---|
| **NFR1** | **Edge Optimization:** Model exported to lightweight runtime (ONNX) without mandatory cloud dependencies. | ONNX / TensorRT on NVIDIA Jetson | Target specified; ONNX export planned in Phase 2. |
| **NFR2** | **Inference Latency:** Processing latency per sonar ping/waterfall frame. | $\le 200\text{ ms}$ per ping | Synthetic pipeline runs in $<15\text{ ms}$; real ONNX target is $\le 200\text{ ms}$. |
| **NFR3** | **Detection Performance (Ghost Nets):** F1-score on held-out test benchmarks. | $\text{F1} \ge 0.85$ | Target benchmark; to be evaluated against real sonar datasets. |
| **NFR4** | **False Positive Rate:** Maximum false alarm rate on natural seafloor features. | $\text{FPR} < 5.0\%$ | Target benchmark; enforced via shadow/aspect-ratio filters. |
| **NFR5** | **Offline Operation:** System functions autonomously on public/replayed sonar datasets without live ocean access. | 100% Offline Capability | Fully verified via synthetic replay harness and local file ingestion. |

---

## 7. Deliverables

1. **Detection & Segmentation Pipeline:** Trained model weights and exported ONNX model with documented validation metrics.
2. **Preprocessing Pipeline:** Standalone image processing routines for speckle filtering (Lee/Median), resolution normalization, and shadow augmentation.
3. **Confidence Scoring & False-Positive Filter:** Calibration logic and heuristic filter suppressing geological artifacts.
4. **Geotagging & Report Exporter:** Navigation log parser and JSON/CSV exporter conforming to the frozen Phase 0 schema.
5. **Operator Web Dashboard:** Streamlit web application supporting upload $\to$ inference $\to$ inspection $\to$ report download.
6. **Documentation & Verification Suite:** Comprehensive architectural specifications, decision logs, test suite, and recorded demo.

---

## 8. Success Metrics

| Metric | Target Threshold | Validation Strategy |
|:---|:---|:---|
| **Ghost Net Detection F1** | $\ge 0.85$ | Evaluated on held-out test split of annotated sonar datasets. |
| **False Positive Rate (FPR)** | $< 5.0\%$ | Measured on negative samples containing rocky seafloor and sand dunes. |
| **Report Completeness** | 100% | Verification that all detections contain valid ID, class, confidence, dimensions, and coordinates. |
| **Dashboard Usability** | Single-flow operation | Verification of zero-configuration upload $\to$ visualization $\to$ download. |

---

## 9. Constraints & Assumptions

### Constraints
* **No Direct Ocean Access:** Testing and demonstration rely entirely on public sonar datasets (Marine Debris FLS, UATD, SeaClear, TrashCan) and synthetic replay harnesses.
* **Sprint Timeline:** Development structured around a rapid hackathon/sprint schedule (Phases 0 through 4).
* **Licensing Compliance:** Dataset usage must strictly comply with original academic/research licenses.

### Assumptions
* Public sonar datasets provide adequate acoustic proxy characteristics for MoES operational survey conditions.
* Standard navigation ping headers (vehicle lat/lon, heading, altitude, across-track range) are available or can be simulated for geotagging.
