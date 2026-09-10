# MarineGuard MCP — AGENTS.md
# ROLE 5 — UI DASHBOARD & SYSTEM INTEGRATION

## 0. ROLE 5 STATUS

Role 1: COMPLETE / FROZEN
Role 2: COMPLETE / FROZEN
Role 3: COMPLETE / FROZEN
Role 4: COMPLETE / FROZEN
Role 5: CURRENT IMPLEMENTATION ROLE

Role 5 is responsible for:

- UI dashboard
- received-data upload workflow
- integration of existing detection pipeline
- displaying real detection results
- confidence filtering UI
- metrics presentation
- reporting integration
- MCP detection/report integration
- final end-to-end demonstration
- repository cleanup related only to Role 5

Do NOT implement Role 6 or any additional role.

---

# 1. MOST IMPORTANT SYSTEM SCOPE

MarineGuard is NOT a live underwater vehicle-control system.

The system receives previously recorded / collected underwater data.

The data is then processed by the MarineGuard software pipeline.

The correct conceptual workflow is:

RECEIVED UNDERWATER DATA
        ↓
DATA VALIDATION
        ↓
DETECTION
        ↓
CONFIDENCE FILTERING
        ↓
RESULTS
        ↓
METRICS
        ↓
REPORTING

The system must NOT pretend that it is receiving live sensor telemetry.

---

# 2. INPUT MODEL

Role 5 must treat the input as:

> Received / recorded underwater or sonar data.

Examples may include:

- underwater images
- optical camera images
- side-scan sonar images
- supported image/data files already compatible with the existing pipeline

The exact input format MUST be determined from the existing repository implementation.

Do not invent a new input format without checking the existing code.

---

# 3. STRICTLY FORBIDDEN TELEMETRY

The final MarineGuard UI MUST NOT contain or simulate:

- temperature
- water temperature
- pressure sensor
- depth sensor
- depth gauge
- battery percentage
- battery voltage
- battery current
- communications signal
- communications strength
- telemetry
- IMU
- accelerometer
- gyroscope
- compass
- heading
- vehicle speed
- motor state
- motor RPM
- propulsion state
- AUV state
- AUV controls
- vehicle controls
- autonomous navigation
- live GPS hardware
- live location tracking
- live vehicle position
- live sensor streams

Do not create placeholder cards for these values.

Do not display these values as simulated/demo data.

Do not generate fake values such as:

temperature = 24°C
depth = 18m
battery = 87%
heading = 142°
speed = 1.4 m/s

These values are NOT part of the MarineGuard Role 5 scope.

---

# 4. NO FABRICATED DATA

This rule is mandatory.

Never fabricate:

- detections
- confidence values
- coordinates
- timestamps
- metrics
- sensor readings
- model performance
- latency
- geographic positions
- environmental measurements

If information is unavailable, display:

- "Unavailable"
- "Not provided"
- "Not available"

as appropriate.

Never substitute a fake value.

---

# 5. LOCATION / GEOLOCATION RULE

MarineGuard does NOT generate location information.

The system may only display geographic information if valid geographic information is already present in the received input/result metadata.

Never:

- generate coordinates
- estimate coordinates without an approved algorithm
- create fake GPS locations
- assign default coordinates
- use the user's computer location
- use browser geolocation
- use IP geolocation
- infer location from unrelated information

If the received data contains valid latitude/longitude metadata:

    display it as provided by the data pipeline.

If the received data does not contain coordinates:

    display:
    "Location unavailable"

Do not create a map marker for an object with no valid coordinates.

---

# 6. MAP / GEOGRAPHIC UI RULE

A geographic map is NOT mandatory for every input.

The UI must handle both cases.

CASE A — valid geographic metadata exists:

    Show geographic results.

CASE B — no geographic metadata exists:

    Show detection results without geographic positioning.

Never fabricate map markers.

Never use a random/default location.

Never center the map on the user's current location.

Never use browser GPS.

If geographic information is unavailable, clearly state:

    "Geographic coordinates were not provided with this dataset."

---

# 7. ROLE 4 INTEGRATION

Role 4 is COMPLETE and FROZEN.

Do not rewrite Role 4.

Use the existing Role 4 exporters and geotagging functionality.

Expected existing capabilities include:

- GeoJSON
- S-100/S-124 partial export
- PDF
- CSV
- JSON
- coordinate validation
- rejected detection preservation

Role 5 should CONSUME these capabilities.

Do not redesign or replace them.

If a Role 4 defect is discovered, first verify whether it is genuinely required for Role 5 integration.

Do not modify frozen Role 4 code casually.

---

# 8. ROLE 3 INTEGRATION

Role 3 is COMPLETE and FROZEN.

Use the existing:

- confidence filtering
- accepted/rejected detection information
- filtering reasons
- calibrated confidence where available
- evidence information

Do not reimplement the filtering algorithm in the UI.

The UI must call the existing filtering/pipeline layer.

The UI must NOT duplicate detection filtering logic.

---

# 9. ROLE 2 INTEGRATION

Role 2 is COMPLETE and FROZEN.

Use the existing:

- optical detection
- side-scan sonar detection
- model loading
- DetectionResult contract
- SSS class mapping

Do not rewrite Role 2 detection logic.

Do not create another detector inside Streamlit.

---

# 10. ROLE 1 INTEGRATION

Role 1 is COMPLETE and FROZEN.

Do not modify:

- V1 dataset
- V1 split
- V1 taxonomy
- V1 class IDs
- V1 test set
- frozen V1 model
- dataset conversion logic

The UI must consume the existing model/pipeline.

---

# 11. PRIMARY UI WORKFLOW

The main dashboard should follow:

UPLOAD
    ↓
VALIDATE
    ↓
READY
    ↓
RUN DETECTION
    ↓
PROCESSING
    ↓
RESULTS
    ↓
FILTERED RESULTS
    ↓
METRICS
    ↓
REPORT

The user should not need manual backend intervention during the demo.

---

# 12. DASHBOARD STRUCTURE

Recommended sections:

1. Analyze
2. Results
3. Metrics
4. Reports
5. About

A Map section may exist ONLY when valid geographic data is available.

Do not make geographic visualization mandatory when coordinates are absent.

---

# 13. ANALYZE PAGE

The Analyze page must provide:

- file upload
- supported input indication
- file validation
- ready state
- Run Detection button
- processing/loading state
- real detection execution
- result summary

Do not add:

- telemetry sliders
- sensor controls
- vehicle controls
- fake environmental controls
- simulated battery
- simulated depth
- simulated temperature

---

# 14. FILE UPLOAD

The uploader must use the project's ACTUAL supported input format.

Before implementing:

1. Inspect the repository.
2. Identify the existing input format.
3. Identify the existing inference entry point.
4. Confirm the expected data structure.
5. Connect the UI to that implementation.

Do not guess.

---

# 15. DETECTION

The Run Detection button MUST execute the real existing MarineGuard pipeline.

It must NOT:

- generate fake detections
- return hardcoded objects
- return demonstration values
- bypass the trained model
- create random confidence scores

The displayed detections must originate from the actual pipeline.

---

# 16. DETECTION RESULTS

The results page should display, where available:

- detection ID
- class/object name
- class ID
- raw confidence
- calibrated confidence
- filtering status
- filtering reason
- bounding box
- sensor/source
- coordinates ONLY if supplied
- evidence information

Unavailable fields must be shown as unavailable.

---

# 17. CONFIDENCE FILTER

Use the existing Role 3 filtering implementation.

The UI may expose a confidence threshold control if compatible with the existing architecture.

Important:

Changing the UI threshold must affect actual filtering.

Do not simply change a displayed number.

The UI must clearly distinguish:

TOTAL DETECTIONS

ACCEPTED DETECTIONS

FILTERED / REJECTED DETECTIONS

---

# 18. METRICS

The Metrics page must use real benchmark results.

Possible metrics:

- precision
- recall
- F1
- false-positive rate
- false-negative rate
- inference latency
- benchmark/test sample count

Only show metrics that are actually available and verified.

If a metric has not been measured:

    display "Unavailable"

Do NOT display fabricated percentages.

Do NOT use:

- firewall compliance %
- battery %
- telemetry %
- sensor health %
- vehicle health %

as model-performance metrics.

---

# 19. EVALUATION

If eval.py already exists:

1. Inspect it.
2. Determine whether it uses real model predictions.
3. Determine whether it uses held-out data.
4. Preserve correct existing behavior.
5. Fix only Role 5-required integration issues.

Evaluation must not use fabricated predictions.

The test set must remain untouched.

Do not train on the test set.

Do not alter Role 1 V1 test data.

---

# 20. LATENCY

Latency may be displayed only if it is actually measured.

Use a documented and repeatable measurement method.

Do not create a fake latency value.

Do not hardcode:

    120 ms
    150 ms
    200 ms

etc.

---

# 21. REPORTING

Role 5 must integrate existing reporting functionality.

Supported outputs may include:

- PDF
- CSV
- JSON
- GeoJSON
- S-100/S-124 partial export

Use the existing Role 4 exporters.

Do not create duplicate exporters unless absolutely necessary.

Reports should reflect the same detection results shown in the UI.

---

# 22. PDF REPORT

The PDF report should use actual results.

It may contain:

- mission/input identifier
- processing timestamp if genuinely available
- detection summary
- accepted detections
- rejected detections
- confidence information
- filtering reasons
- coordinates if provided
- model metrics if available
- scope notes

It must NOT contain fake:

- depth
- temperature
- battery
- communications
- vehicle state
- sensor telemetry

---

# 23. MCP SERVER

The existing MCP server is primarily for detection/report functionality.

Role 5 must NOT introduce:

- vehicle control
- motor control
- autonomous navigation
- telemetry commands
- battery commands
- depth commands
- temperature commands
- live GPS commands

Keep the MCP interface focused on:

- detection
- results
- filtering
- reporting/export

Do not break existing MCP functionality.

---

# 24. CONFIGURATION

Inspect config.yaml before changing it.

Keep only configuration actually required by:

- model
- detection
- fusion
- filtering
- reporting
- UI integration

Remove obsolete vehicle/telemetry configuration only if it is clearly unused and within Role 5 scope.

Do not modify frozen-role configuration unnecessarily.

---

# 25. UI DESIGN PRINCIPLE

MarineGuard should look like a professional marine-debris analysis system.

The UI should emphasize:

UNDERWATER DATA
        ↓
AI DETECTION
        ↓
CONFIDENCE FILTERING
        ↓
RESULTS
        ↓
METRICS
        ↓
REPORTING

The UI should NOT look like:

- an AUV control console
- a submarine cockpit
- a vehicle telemetry dashboard
- a robotics remote-control panel

---

# 26. SIMULATION RULE

No fake runtime values.

If demonstration data is required:

Use an actual repository test/sample file.

Clearly identify it as:

    Sample / Test Dataset

Do not create simulated sensor telemetry.

---

# 27. ERROR HANDLING

The UI must gracefully handle:

- unsupported file
- corrupted file
- empty file
- invalid input
- model loading failure
- inference failure
- filtering failure
- exporter failure
- missing coordinates
- missing metrics
- missing optional metadata

Errors must be understandable to the operator.

Do not silently return fake results after an error.

---

# 28. NO LOCATION FABRICATION

This deserves explicit enforcement.

NEVER use:

    0,0

as a default location.

NEVER use:

    user's current location

as a default.

NEVER use:

    browser geolocation

as a default.

NEVER use:

    random coordinates

for visualization.

If coordinates are absent:

    geometry = null

or equivalent existing project representation.

---

# 29. SECURITY / PRIVACY

Do not collect:

- browser GPS
- computer location
- personal location
- unnecessary device telemetry

Do not send uploaded data to an external service unless explicitly required by the existing project architecture.

Keep processing within the existing MarineGuard architecture.

---

# 30. REPOSITORY SAFETY

Before modifying anything:

    git status
    git branch
    git log --oneline -10

Create a dedicated Role 5 branch.

Example:

    feature/ui-system-integration

Do not work directly on main unless explicitly instructed.

---

# 31. FROZEN ROLE PROTECTION

The following are frozen:

ROLE 1
ROLE 2
ROLE 3
ROLE 4

Do not modify their implementation merely for cleanup.

If Role 5 requires integration:

Prefer:

    additive integration

over:

    modifying frozen implementation.

Any unavoidable modification to frozen code must be:

1. justified
2. minimal
3. tested
4. documented
5. explicitly reviewed

---

# 32. TESTING

After each meaningful change:

    python -m pytest -q

If the complete environment cannot execute all tests:

- record the exact failure
- identify whether it is dependency/environment related
- do not hide the failure
- do not replace tests with fake success

Also test the Streamlit application.

---

# 33. REQUIRED END-TO-END TEST

At minimum demonstrate:

1. Start dashboard.
2. Upload an actual supported underwater/sonar file.
3. Validate the file.
4. Click Run Detection.
5. Real model executes.
6. Real detections appear.
7. Confidence filtering works.
8. Accepted/rejected counts are correct.
9. Results table is correct.
10. Geographic information is shown ONLY if provided.
11. Missing coordinates are handled correctly.
12. Metrics are real or explicitly unavailable.
13. Report generation works.
14. Exported report matches displayed results.
15. No telemetry/fake sensor values appear.

---

# 34. UI CLEANUP CHECKLIST

The final UI MUST NOT contain:

[ ] Mission Firewall UI
[ ] Battery gauge
[ ] Communications gauge
[ ] Depth gauge
[ ] Temperature gauge
[ ] Telemetry sliders
[ ] Simulated sensor controls
[ ] Vehicle controls
[ ] Motor controls
[ ] Autonomous navigation controls
[ ] Fake GPS
[ ] Browser geolocation
[ ] Fake coordinates
[ ] Fake sensor readings

---

# 35. REQUIRED UI CHECKLIST

The final UI SHOULD contain:

[ ] Dashboard
[ ] File upload
[ ] Input validation
[ ] Run Detection
[ ] Processing state
[ ] Detection summary
[ ] Detection table
[ ] Confidence information
[ ] Accepted count
[ ] Filtered count
[ ] Filtering reasons
[ ] Evidence inspection
[ ] Metrics
[ ] Reports
[ ] PDF export
[ ] CSV/JSON export where supported
[ ] GeoJSON only when geographic information is available/required
[ ] Clear unavailable-state handling
[ ] About/project information

---

# 36. GEOGRAPHIC RESULTS RULE

If valid coordinates are present in the received dataset:

    display them.

If valid coordinates are absent:

    do not invent them.

The UI must be fully functional without geographic data.

This means:

Detection workflow:

    Upload
    ↓
    Detect
    ↓
    Filter
    ↓
    Results
    ↓
    Metrics
    ↓
    Reports

must work even when:

    coordinates = unavailable

---

# 37. PRESENTATION NARRATIVE

The final demonstration should communicate:

"MarineGuard receives recorded underwater data and processes it through an AI-based marine debris detection pipeline."

Then demonstrate:

1. Upload data.
2. Run detection.
3. Identify detected objects.
4. Apply confidence filtering.
5. Inspect results.
6. View available geographic information if provided.
7. View real model metrics.
8. Generate the report.

Do NOT claim:

- live underwater sensing
- live AUV control
- live GPS
- live telemetry
- real-time battery monitoring
- real-time depth sensing
- temperature sensing

unless those capabilities are genuinely implemented and part of the approved project scope.

---

# 38. DOCUMENTATION

Update documentation where necessary.

Documentation must accurately describe:

- received-data workflow
- supported input
- detection pipeline
- confidence filtering
- metrics
- reporting
- optional geographic metadata

Documentation must NOT claim unsupported live telemetry.

---

# 39. CODE QUALITY

Prefer:

- reusable functions
- clear interfaces
- existing project abstractions
- minimal duplication
- type-safe data flow where existing project style supports it
- meaningful error handling
- testable components

Avoid:

- giant Streamlit functions
- duplicated model-loading code
- duplicated filtering logic
- hardcoded detections
- hardcoded metrics
- fake telemetry
- unnecessary dependencies

---

# 40. DEPENDENCY RULE

Before adding a dependency:

1. Check whether an existing dependency already provides the functionality.
2. Check requirements.txt.
3. Avoid unnecessary packages.
4. Do not introduce large UI frameworks unless required.

Keep the project lightweight.

---

# 41. OBSOLETE FILE CLEANUP

If COMPLETE_MARINEGUARD_CODEBASE.py exists:

1. Search the repository for imports/references.
2. Confirm it is not required.
3. Remove it only after dependency verification.
4. Run tests.
5. Run the application.

Do not delete files blindly.

---

# 42. GIT COMMIT RULE

Use small focused commits.

Suggested sequence:

    refactor(member5): redesign dashboard for received data
    feat(member5): connect real detection pipeline
    feat(member5): integrate confidence-filtered results
    feat(member5): add evidence-based metrics
    feat(member5): integrate reporting
    chore(member5): remove obsolete telemetry UI
    chore(member5): clean obsolete integration files
    test(member5): verify end-to-end dashboard workflow
    docs(member5): finalize system integration documentation

Use the actual changes as the source of truth.

Do not create meaningless commits.

---

# 43. FINAL FORENSIC AUDIT

Before Role 5 is declared complete, verify:

### Input

[ ] Real received data can be uploaded.
[ ] Input validation works.
[ ] Unsupported files fail safely.

### Detection

[ ] Real trained model is used.
[ ] Real detections are returned.
[ ] Correct class names are shown.
[ ] Real confidence values are shown.

### Filtering

[ ] Existing Role 3 filtering is used.
[ ] Accepted detections are correct.
[ ] Rejected detections are preserved.
[ ] Rejection reasons are visible.

### Geography

[ ] Existing coordinates are preserved.
[ ] Missing coordinates remain missing.
[ ] No coordinates are fabricated.
[ ] No browser GPS is used.
[ ] No user location is used.

### Metrics

[ ] Metrics come from real evaluation.
[ ] Unavailable metrics are clearly marked.
[ ] No fake percentages exist.
[ ] Latency is measured if displayed.

### Reporting

[ ] PDF works.
[ ] CSV/JSON work where supported.
[ ] GeoJSON works when applicable.
[ ] Reports match displayed results.

### UI

[ ] Dashboard loads.
[ ] Upload works.
[ ] Run Detection works.
[ ] Results work.
[ ] Metrics work.
[ ] Reports work.
[ ] No telemetry UI remains.
[ ] No vehicle-control UI remains.
[ ] No fake sensor cards remain.

### MCP

[ ] Detection tools work.
[ ] Reporting/export tools work.
[ ] No vehicle-action tools remain in final scope.

### Repository

[ ] Frozen Roles 1–4 remain protected.
[ ] No accidental dataset/model changes.
[ ] Tests run.
[ ] Streamlit runs.
[ ] Git status is understood.
[ ] Documentation is updated.

---

# 44. ROLE 5 DEFINITION OF DONE

Role 5 is COMPLETE only when:

1. A real received underwater/sonar file can be uploaded.
2. The file reaches the actual MarineGuard detection pipeline.
3. Real detections are displayed.
4. Confidence filtering works.
5. Accepted and rejected detections are distinguishable.
6. Evidence information is available where supported.
7. Geographic information is displayed only when actually provided.
8. Missing geographic information is handled honestly.
9. Metrics are real or explicitly unavailable.
10. Reports are generated from the same results.
11. MCP detection/report functionality remains operational.
12. All fake telemetry is removed.
13. Battery/depth/temperature/communications/vehicle controls are absent.
14. No location is fabricated.
15. No browser/user geolocation is used.
16. Frozen Roles 1–4 remain intact.
17. Tests pass or documented environment limitations are recorded.
18. Complete upload → detection → filtering → results → metrics → report workflow is demonstrated successfully.

---

# 45. FINAL SYSTEM MODEL

The final MarineGuard system should be understood as:

        RECEIVED DATA
              ↓
        DATA VALIDATION
              ↓
        AI DETECTION
              ↓
        CONFIDENCE FILTERING
              ↓
        DETECTION RESULTS
           ↙       ↘
      METRICS     REPORTS
           \
       OPTIONAL GEO
       IF PROVIDED

NOT:

        LIVE AUV
           ↓
      LIVE TELEMETRY
           ↓
       GPS / DEPTH
           ↓
       BATTERY
           ↓
      VEHICLE CONTROL

The second architecture is OUT OF SCOPE.

MarineGuard Role 5 is a received-data analysis and reporting dashboard.

END OF ROLE 5 AGENTS.md