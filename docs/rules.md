# Project Engineering Rules

**Project:** MarineGuard — Automated Underwater Marine Debris Detection  
**Context:** Development Discipline & Operational Protocols  

---

## 1. Scope Discipline

* **Requirement Traceability:** Every feature, module, and task must trace directly to a defined requirement in `project_requirement_document.md`. If it does not directly advance the detection, filtering, geotagging, or reporting pipeline for SIH26057, it must not be built.
* **No Feature Creep:** Do not reintroduce dropped features (Mission Firewall, vehicle-action logic, natural-language MCP agent interfaces, S-100 exports, live telemetry sliders) without a formal team decision recorded in `memory.md`.

---

## 2. File Ownership (No-Overlap Rule)

* **Single Ownership:** Each file has exactly one owner for a given work session according to the team ownership map.
* **Cross-File Coordination:** If a task requires modifications to a file outside your assigned module, communicate directly with the owner — do not edit their file unilaterally.
* **Shared Files:** Shared files (`marineguard/schemas.py`, `config.yaml`) may only be modified during the Phase 0 synchronization or with explicit sign-off from all module owners.

---

## 3. Metrics Honesty

* **Empirical Measurements Only:** Never publish, present, or commit a performance metric (F1, precision, recall, false-positive rate, latency) that was not empirically evaluated against actual model outputs on documented datasets.
* **Target Labeling:** No placeholder or target benchmarks may appear in the final report, README, or pitch as if they were achieved results. All projected figures must be clearly labeled as **"Target Benchmarks"**.
* **No Completeness Manifests:** Delete or exclude any file whose sole function is to assert completion without providing verifiable test execution (e.g. self-reported "100% verified" static manifests).

---

## 4. Schema-First Development

* **Early Schema Freeze:** The report output schema (`survey_id`, `source_log`, `detections`, `bounding_box`, `location`, `depth_m`, `summary`) must be frozen in Phase 0 before writing exporter logic.
* **Change Governance:** Any change to frozen schemas after Phase 0 requires immediate re-synchronization with all downstream consumers (Report Exporter, Dashboard, GIS visualizer).

---

## 5. Things Not To Do

* **Do not add vehicle-action logic:** Do not build autonomous vehicle navigation, thruster overrides, or emergency ascent controllers — physical vehicle control is outside the scope of SIH26057.
* **Do not spend build time extending the compiler:** The multi-platform sensor compiler is frozen in its current state as a demonstration asset.
* **Do not add hydrographic S-100 exports:** Do not create complex S-100 or shapefile pipelines beyond the existing GeoJSON exporter.
* **Do not fabricate coordinates or test counts:** Never invent latitude/longitude coordinates or synthetic detection counts without explicitly labeling them as replayed/synthetic data.

---

## 6. Data & Licensing

* **License Verification:** Verify academic and commercial redistribution licenses for all public datasets (Marine Debris FLS, UATD, SeaClear, TrashCan) prior to public release.
* **Git Repository Cleanliness:** Do not commit massive raw acoustic log files or binary datasets to Git version control. Commit only preprocessing, loading, and ingestion scripts.

---

## 7. Code Conventions

* **Single Responsibility Principle:** One module = one responsibility (refer to the `architecture.md` module inventory). Do not embed filtering heuristics into raw detection files, or geotagging logic into report formatters.
* **Mandatory Testing:** Every new module must have a corresponding unit test suite under `tests/` validating edge cases and failure modes.
* **Centralized Configuration:** All operational parameters (model weights paths, confidence thresholds, filter coefficients) must reside in `config.yaml`, never hardcoded into module source files.

---

## 8. Synchronization Checkpoints

* **Phase 0:** Schema Freeze — All team members confirm data structures and drop lists.
* **Phase End Checkpoints:** End of each phase cross-check verifying that module outputs match the frozen data contracts.
* **Pre-Rehearsal:** Group review and validation of the Definition of Done checklist before demo recording.

---

## 9. Pitch & Documentation Honesty

* **Truthful Reporting:** README files, pitch slide decks, and project documentation must describe only what was actually built, verified, and measured.
* **Secondary Feature Boundaries:** Kept non-core features (sensor compiler, multi-sensor late fusion) should receive concise one-line mentions without implying they represent the primary deliverable.
* **Transparent Scoping:** If evaluators inquire about earlier prototype references to AUV control, firewalls, or MCP agents, explain transparently that the project underwent a disciplined scope correction to align directly with the Ministry of Earth Sciences problem statement.
