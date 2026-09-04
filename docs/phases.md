# Project Execution Roadmap & Phases

**Project:** MarineGuard — Automated Underwater Marine Debris Detection  
**Context:** Sprint & Hackathon Milestone Breakdown (SIH26057)  

---

## Multi-Day SIH Mapping

| Phase | Hackathon Timeline | Multi-Day SIH Schedule | Focus Milestone |
|:---|:---|:---|:---|
| **Phase 0** | Hours 0 – 1 | Day 1, Morning | Schema & Data Freeze |
| **Phase 1** | Hours 1 – 12 | Day 1, Afternoon/Night | Foundations & Preprocessing Pipeline |
| **Phase 2** | Hours 12 – 16 | Day 2, Morning | Detection Quality, ONNX Export & Filtering |
| **Phase 3** | Hours 16 – 20 | Day 3 | Reporting, Dashboard Integration & Clean-up |
| **Phase 4** | Hours 20 – 24 | Day 4 | Rehearsal, Documentation & Polish |

---

## Phase Breakdown & Exit Criteria

### Phase 0 — Schema & Data Freeze (Hours 0–1 / Day 1 AM)
* **Tasks:**
  1. Freeze standard output JSON and CSV schemas (`json_csv_report.py`) with all required fields (location, bounding dimensions, classification, calibrated confidence).
  2. Freeze train/val/test data splits across the 4 public datasets (Marine Debris FLS, UATD, SeaClear, TrashCan).
  3. Formalize the dropped-scope list (firewall, MCP natural-language server, S-100, telemetry sliders).
* **Exit Criteria:** Every team member can cite the report schema fields from memory; data split definitions are committed to version control.

### Phase 1 — Foundations (Hours 1–12 / Day 1)
* **Tasks:**
  1. Ingest and normalize public sonar datasets into standard annotation formats.
  2. Build the image preprocessing pipeline: speckle denoising (Lee/Median), resolution normalization, synthetic shadow augmentation, and dropout simulation.
  3. Execute baseline model training pass (YOLOv8-seg / U-Net).
* **Exit Criteria:** A functional trained model checkpoint exists and executes inference on a held-out test sample.

### Phase 2 — Detection Quality & Filtering (Hours 12–16 / Day 2)
* **Tasks:**
  1. Fine-tune model weights against validation set; export model to ONNX runtime format for edge execution.
  2. Implement Platt / isotonic confidence calibration logic.
  3. Construct and evaluate the false-positive filter using acoustic shadow-ratio and silhouette aspect-ratio heuristics.
* **Exit Criteria:** Measured F1-score ($\ge 0.85$) and false positive rate ($< 5.0\%$) benchmarked on real model outputs before and after filtering.

### Phase 3 — Reporting & Integration (Hours 16–20 / Day 3)
* **Tasks:**
  1. Implement navigation ping-header parser for automatic coordinate geotagging.
  2. Complete the dedicated JSON/CSV report exporter conforming strictly to the Phase 0 frozen schema.
  3. Wire the Streamlit dashboard upload flow to the real pipeline; remove telemetry sliders and firewall controls.
  4. Add the Performance & Metrics tab to the dashboard.
  5. Execute codebase hygiene discards: deprecate firewall references and remove obsolete manifest files.
* **Exit Criteria:** End-to-end user flow operates seamlessly: an operator uploads a raw sonar image/log, views detection overlays and GIS map, and downloads verified JSON/CSV reports.

### Phase 4 — Rehearsal & Polish (Hours 20–24 / Day 4)
* **Tasks:**
  1. Conduct full end-to-end dry-run rehearsals (minimum 2 runs).
  2. Record a high-resolution backup video demonstration of the complete upload $\to$ report workflow.
  3. Finalize README, architectural diagrams, and documentation to reflect only verified, implemented functionality.
  4. Validate all checklist items in the Definition of Done.
* **Exit Criteria:** All items in the Definition of Done are verified; test suite passes 100%; clean commit and push to remote repository.
