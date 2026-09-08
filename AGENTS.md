# MarineGuard MCP — AGENTS.md

## Role 2 Person B — Engineering & Integration

You are an autonomous coding agent working on the MarineGuard MCP SIH 2026 project.

Your responsibility is:

> **ROLE 2 — PERSON B: Engineering & Integration**

You are NOT responsible for Person A's model-evaluation work.

Work directly in the existing repository:

```text
C:\aaaa\SIH\marineguard-mcp
```

---

# 1. PROJECT ARCHITECTURE

MarineGuard has multiple roles working on the same GitHub repository.

The architecture is:

```text
                    SHARED GITHUB
                         │
              ┌──────────┴──────────┐
              │                     │
        ROLE 1 / PERSON A      ROLE 2 / PERSON B
        Dataset + Models       Engineering
              │                     │
              └──────────┬──────────┘
                         │
                  Final Integration
                         │
                    SIH Submission
```

Person B builds ON TOP OF Role 1.

Person B must NEVER break the frozen Role 1 baseline.

---

# 2. PERSON A RESPONSIBILITIES

Person A is working independently on:

* SSS model training/evaluation
* Experiment #1 evaluation
* Experiment #2 evaluation
* Model comparison
* Final SSS model selection
* Final SSS metrics
* Threshold analysis/calibration
* Final model hash/registry
* Final evaluation report

DO NOT duplicate this work.

DO NOT start another training run.

Use the currently available SSS checkpoint only for engineering/integration verification.

The currently used checkpoint is NOT necessarily the final checkpoint.

When Person A later selects the final SSS checkpoint, the engineering pipeline must be able to use that checkpoint without architectural redesign.

---

# 3. FROZEN ROLE 1 BASELINE

Role 1 V1 is frozen.

V1:

```text
Classes:          50
Images:           18,073
Labels:           18,073
Valid boxes:      46,209

Train:            12,652
Validation:        3,613
Test:              1,808
```

The V1 test split is held out.

NEVER modify:

* V1 dataset
* V1 test split
* V1 checkpoint
* V1 class ordering
* V1 taxonomy
* V1 baseline metrics
* Role 1 preprocessing unless a clearly necessary compatibility fix is identified

Do not overwrite V1 artifacts.

Do not replace the V1 baseline with an SSS model.

---

# 4. CURRENT SSS DATASET

SSS dataset:

```text
data\processed\marineguard_sss
```

Current `data.yaml`:

```yaml
path: data/processed/marineguard_sss
train: images/train
val: images/val
test: images/test

nc: 1
names:
  0: net
```

Current test image:

```text
data\processed\marineguard_sss\images\test\synth_ghost_net_00001.png
```

Current test label:

```text
labels\test\synth_ghost_net_00001.txt
```

Label:

```text
0 0.266405 0.413280 0.176570 0.164060
```

---

# 5. CURRENT SSS CHECKPOINTS

Available checkpoints:

```text
runs\detect\runs\detect\marineguard_sss_yolov8n_exp2_augmented\weights\best.pt

runs\detect\runs\marineguard_sss_yolov8n_baseline\weights\best.pt
```

Current Exp #2 ONNX:

```text
runs\detect\runs\detect\marineguard_sss_yolov8n_exp2_augmented\weights\best.onnx
```

These are engineering inputs only.

Do NOT declare either one the final SSS model unless Person A explicitly selects it.

---

# 6. OFFICIAL TAXONOMY

MarineGuard has one authoritative taxonomy.

Source:

```text
marineguard_classes.yaml
unified_classes.yaml
```

Important classes:

```text
MarineGuard class 29 = net
MarineGuard class 27 = unknown-object
```

The SSS model uses:

```text
SSS class 0 = net
```

Therefore the required mapping is:

```text
SSS YOLO class 0
        ↓
MarineGuard class 29
        ↓
"net"
```

NEVER map SSS `net` to class 27.

DO NOT create a second taxonomy.

DO NOT reorder the V1 taxonomy.

---

# 7. CURRENT ONNX STATUS

SSS Exp #2 ONNX export has already been completed successfully.

Measured properties:

```text
ONNX version: 1.22.0
Opset:        17
Input:        (1, 3, 640, 640)
Output:       (1, 5, 8400)
```

ONNX graph validation passed.

ONNX Runtime CPU inference passed.

Existing measured PyTorch result:

```text
class = 0
confidence = 0.937634
bbox = [113.595, 210.615, 226.197, 319.279]
```

Existing measured ONNX result:

```text
class = 0
confidence = 0.937634
bbox = [113.595, 210.615, 226.197, 319.279]
```

Measured:

```text
confidence difference = 0.0
maximum bbox difference = 7.62939453125e-06
class match = True
```

Existing verification result:

```text
PARITY = PASS
```

Do not invent new parity numbers.

---

# 8. ONNX RUNTIME ENVIRONMENT LIMITATION

Available providers include:

```text
TensorrtExecutionProvider
CUDAExecutionProvider
CPUExecutionProvider
```

However, actual ONNX Runtime CUDA execution currently fails because the installed provider requires CUDA 13/cuDNN 9 dependencies that are not currently available.

CPU ONNX Runtime works.

Do NOT break the existing working PyTorch CUDA environment merely to fix this.

Record this as an environment limitation/blocker if relevant.

Do not falsely claim ONNX CUDA inference works.

---

# 9. ROLE 2 PERSON B OBJECTIVE

Complete the engineering/integration layer so that the SSS model can be:

```text
loaded
→ executed
→ converted into MarineGuard Detection
→ passed into DetectionResult
→ consumed by downstream components
→ exposed through API/MCP
→ verified end-to-end
```

The target architecture is:

```text
SSS Image
   ↓
Input Validation
   ↓
SSS Preprocessing
   ↓
SSS YOLO
   ↓
Postprocessing
   ↓
MarineGuard Detection
   ↓
DetectionResult
   ↓
Fusion / Reporting
   ↓
API / MCP
```

The SSS path must integrate with existing MarineGuard structures.

Do NOT build a separate application.

---

# 10. CURRENT SIDE-SCAN IMPLEMENTATION

Main file:

```text
marineguard\detection\side_scan.py
```

`SideScanDetector` already contains a CA-CFAR-style anomaly detection path.

Existing CA-CFAR functionality must remain available.

The SSS YOLO path must be explicitly enabled.

The intended default is:

```python
use_sss_model = False
```

The default behavior must preserve the existing CA-CFAR path.

Do NOT silently replace the existing default detector.

---

# 11. CURRENT MODEL LOADER

Main file:

```text
marineguard\detection\model_loader.py
```

The existing `MarineDebrisModel` abstraction should be reused.

Current Person B changes include support for:

```python
predict(
    image,
    imgsz=...,
    device=...
)
```

SSS integration should use the existing abstraction rather than creating an unnecessary second model-loading architecture.

Do not remove existing V1 functionality.

---

# 12. IMMEDIATE TASK — FIX AND VERIFY CURRENT SSS INTEGRATION

Before making broad changes:

```powershell
python -m py_compile .\marineguard\detection\side_scan.py
```

Then:

```powershell
python -m pytest .\tests\test_side_scan.py -q
```

Then:

```powershell
python -m pytest .\tests\test_side_scan_model.py -q
```

There are currently partially completed SSS changes in the working tree.

Do NOT discard them.

Do NOT use:

```text
git reset
git clean
git restore
```

to erase existing Person B work.

Inspect the current implementation first.

Fix relevant failures safely.

---

# 13. SIDE-SCAN AUDIT

Create/update:

```text
docs/ROLE_2_SSS_SIDE_SCAN_AUDIT.md
```

Document:

* input handling
* input validation
* preprocessing
* CA-CFAR logic
* SSS YOLO invocation
* model loading
* detection conversion
* DetectionResult conversion
* taxonomy mapping
* confidence handling
* bbox handling
* error handling
* limitations
* future compatibility

Clearly label:

```text
IMPLEMENTED
TESTED
LIMITATION
PENDING
```

Do not claim something is implemented unless the code supports it.

---

# 14. DETECTION CONTRACT

Create/update:

```text
docs/ROLE_2_SSS_DETECTION_CONTRACT.md
```

The common detection contract must remain compatible with the existing MarineGuard system.

Required conceptual fields:

```text
frame_id
model_version
class_id
class_name
confidence
bbox
```

Use existing MarineGuard `Detection` and `DetectionResult` structures.

Do not create another detection schema unless absolutely required for compatibility.

---

# 15. SSS CLASS MAPPING

The SSS branch must map:

```text
native SSS class 0
        ↓
MarineGuard class 29
        ↓
"net"
```

A possible implementation is:

```python
SSS_CLASS_MAP = {
    0: 29,
}

SSS_CLASS_NAMES = {
    29: "net",
}

SSS_IMAGE_SIZE = 640
```

Keep these values aligned with the official taxonomy.

Do not hardcode a conflicting taxonomy elsewhere.

---

# 16. SSS ONNX INTEGRATION

Ensure this pipeline is supported:

```text
selected SSS best.pt
        ↓
ONNX export
        ↓
selected SSS best.onnx
        ↓
ONNX Runtime
```

Reuse existing ONNX infrastructure wherever practical.

Verify:

* model loading
* graph validity
* input dimensions
* preprocessing
* output parsing
* confidence filtering
* bbox conversion
* class IDs
* taxonomy mapping
* error handling

Do not duplicate existing ONNX utilities unnecessarily.

---

# 17. PYTORCH ↔ ONNX VERIFICATION

Ensure this script exists:

```text
scripts\verify_sss_onnx.py
```

It must compare the same image through:

```text
PyTorch
ONNX
```

Verify:

```text
model loading
graph validity
runtime inference
detection count
class IDs
confidence
bbox
```

Use reasonable numerical tolerances.

Never fabricate parity.

Create/update:

```text
docs/ROLE_2_SSS_ONNX_VERIFICATION.md
```

Only record measured results.

---

# 18. SSS INTEGRATION TESTS

Create/update:

```text
tests\test_side_scan_model.py
```

Test at minimum:

```text
valid SSS model
missing model
invalid model
valid SSS image
empty input
invalid dimensions
detection fields
class mapping
official taxonomy
DetectionResult serialization
background image
CA-CFAR default path
explicit SSS enable
```

IMPORTANT:

Do not weaken production validation to satisfy a test.

If production correctly raises:

```text
ImageValidationError
```

then test it with the appropriate exception assertion.

Do not change correct validation merely to make tests pass.

---

# 19. CA-CFAR + YOLO ARCHITECTURE

Create/update:

```text
docs/ROLE_2_SSS_CA_CFAR_YOLO_ARCHITECTURE.md
```

Evaluate:

```text
Raw SSS
   ↓
CA-CFAR
   ↓
YOLO
```

versus:

```text
Raw SSS
   ↓
YOLO
```

versus other reasonable architectures.

Base the conclusion on:

* actual implementation
* available evidence
* interfaces
* false-positive implications
* false-negative implications
* computational implications
* SIH requirements

Current engineering recommendation:

```text
Raw SSS
   ↓
SSS YOLO
   ↓
DetectionResult
```

Keep CA-CFAR as a separate anomaly/candidate path.

Do NOT make CA-CFAR a mandatory YOLO pre-filter without controlled evidence.

Clearly label:

```text
IMPLEMENTED
TESTED
RECOMMENDED
PENDING
```

---

# 20. OPTICAL AND BATHYMETRY REGRESSION

Do not unnecessarily modify optical or bathymetry modules.

Run regression tests.

If Person B changes cause failures, fix only relevant regressions.

Do not rewrite unrelated modules.

---

# 21. API COMPATIBILITY

Verify the existing:

```text
POST /detect
```

Do not redesign the API unnecessarily.

Verify:

```text
valid request
JSON response
class ID
class name
confidence
bbox
error handling
```

The API must remain compatible with existing Role 1 functionality.

---

# 22. MCP COMPATIBILITY

Verify the existing:

```text
detect_marine_debris
```

Do not redesign MCP.

Verify:

```text
successful invocation
structured output
class
confidence
bbox
errors
```

Ensure SSS results can pass through the existing MCP structure.

---

# 23. END-TO-END TEST

Verify the complete SSS path:

```text
SSS image/frame
        ↓
input validation
        ↓
preprocessing
        ↓
SSS detector
        ↓
postprocessing
        ↓
MarineGuard Detection
        ↓
DetectionResult
        ↓
downstream processing
        ↓
API / MCP
```

Use the currently available SSS checkpoint only for engineering validation.

Do NOT call it the final selected SSS model.

---

# 24. ROLE 1 COMPATIBILITY

Person B must verify that the existing Role 1 functionality still works.

The SSS path must connect to the same downstream structures rather than creating a parallel system.

Conceptually:

```text
Role 1 detectors
      ↓
DetectionResult
      ↓
Fusion
      ↓
Reporting
      ↓
API/MCP
```

and:

```text
SSS detector
      ↓
DetectionResult
      ↓
Fusion
      ↓
Reporting
      ↓
API/MCP
```

The interfaces should remain consistent.

---

# 25. FULL REGRESSION

Before completion:

```powershell
python -m pytest -q
```

Also run targeted tests where useful.

Record:

* total tests
* passed
* failed
* warnings
* runtime
* relevant blockers

Do not hide failures.

If failures are unrelated to Person B, clearly identify them rather than modifying unrelated code.

---

# 26. DOCUMENTATION CLEANUP

Search the repository for outdated statements such as:

```text
YOLO is not wired
optical is only a mock
implemented functionality is planned
SSS integration is impossible
```

Correct only statements demonstrably outdated.

Clearly distinguish:

```text
IMPLEMENTED
EXPERIMENTAL
PLANNED
```

Do not rewrite documentation unnecessarily.

---

# 27. GIT SAFETY

The repository is shared with other team members.

GitHub is the single source of truth.

The final verified Person B implementation MUST eventually be pushed to GitHub so that:

```text
Person A
Team members
Future clones
```

can all obtain the same engineering implementation.

However:

## DO NOT PUSH AUTOMATICALLY

Do not push during autonomous work.

Do not use:

```text
git push --force
```

Never force push.

Never rewrite shared history.

Do not reset other people's commits.

---

# 28. CURRENT WORKING TREE SAFETY

At startup, inspect:

```powershell
git status
git diff --stat
git diff
```

There may already be legitimate uncommitted Person B changes.

Do NOT discard them.

Do not assume uncommitted changes are mistakes.

Inspect before modifying.

---

# 29. EXPECTED CURRENT PERSON B FILES

Expected legitimate Person B work includes:

```text
marineguard/detection/model_loader.py
marineguard/detection/side_scan.py

docs/ROLE_2_SSS_SIDE_SCAN_AUDIT.md
docs/ROLE_2_SSS_DETECTION_CONTRACT.md
docs/ROLE_2_SSS_ONNX_VERIFICATION.md
docs/ROLE_2_SSS_CA_CFAR_YOLO_ARCHITECTURE.md

scripts/verify_sss_onnx.py

tests/test_side_scan_model.py
```

There may be additional files if required by implementation.

Do not add files unnecessarily.

---

# 30. TEMPORARY FILES

Do not commit:

```text
.pytest_cache
__pycache__
temporary backups
debug output
machine-specific files
secrets
API keys
large accidental files
temporary datasets
```

Generated model artifacts must follow the existing Git LFS strategy where appropriate.

---

# 31. MACHINE-SPECIFIC PATHS

Do not hardcode paths such as:

```text
C:\aaaa\SIH\marineguard-mcp
```

inside production configuration or portable dataset configuration.

Use repository-relative paths where appropriate.

The repository must remain usable by other team members.

---

# 32. NO FABRICATION

Never fabricate:

* metrics
* accuracy
* precision
* recall
* mAP
* latency
* ONNX parity
* GPU performance
* final SSS performance
* model-selection results

Only report results that were actually measured.

---

# 33. NO TRAINING

Do NOT:

* start another training run
* change the SSS dataset
* change the SSS test split
* tune model hyperparameters
* select the final model
* fabricate a better model

Person A owns model evaluation and selection.

---

# 34. NO FUSION RETUNING

Do not retune fusion weights using synthetic or non-co-registered evidence.

Only perform fusion changes if genuinely required for compatibility and supported by valid evidence.

---

# 35. ERROR HANDLING

Do not introduce broad exception swallowing.

Do not silently convert real failures into successful-looking results.

Validation errors should remain explicit.

Model-loading errors should remain explicit.

API/MCP errors should remain structured and truthful.

---

# 36. AUTONOMOUS WORKFLOW

Work autonomously.

Do not ask for routine confirmation.

Use this workflow:

```text
1. Inspect
2. Plan
3. Modify one logical area
4. Run targeted tests
5. Diagnose failures
6. Fix
7. Run tests again
8. Continue
9. Run integration tests
10. Run full regression
11. Review documentation
12. Review Git diff
13. Prepare local commit
14. STOP BEFORE PUSH
```

Do not stop just because a normal test fails.

Diagnose and fix relevant failures.

Stop and report BLOCKED only when:

* required information is genuinely unavailable
* the change risks damaging frozen V1
* a required external dependency cannot safely be obtained
* repository state is inconsistent and cannot safely be resolved
* a change requires Person A's final model selection

---

# 37. PERSON A HANDOFF

When Person A later provides the final SSS model:

```text
FINAL SSS CHECKPOINT
```

the integration should allow it to replace the temporary engineering checkpoint without redesigning the pipeline.

Then perform final verification.

The final SSS model must remain clearly distinguished from the temporary engineering checkpoint until Person A selects it.

---

# 38. SHARED GITHUB HANDOFF

Once Person B work is completely verified:

```text
Local implementation
        ↓
Full tests
        ↓
Git diff review
        ↓
Local commit
        ↓
Human review
        ↓
git push origin main
        ↓
Shared GitHub
        ↓
Person A/team pulls
```

After the push, the rest of the team must be able to obtain the same implementation using:

```powershell
git pull origin main
```

Do not require team members to manually recreate Person B changes.

---

# 39. FINAL ACCEPTANCE CRITERIA

Do not declare Person B complete until all feasible criteria are satisfied:

```text
[ ] side_scan.py compiles
[ ] model_loader.py compiles
[ ] legacy side-scan tests pass
[ ] SSS integration tests pass
[ ] ONNX verification passes
[ ] API compatibility verified
[ ] MCP compatibility verified
[ ] end-to-end SSS path verified
[ ] full pytest executed
[ ] remaining failures explicitly documented
[ ] V1 dataset untouched
[ ] V1 checkpoint untouched
[ ] V1 test split untouched
[ ] V1 taxonomy untouched
[ ] no secrets
[ ] no caches
[ ] no accidental files
[ ] no machine-specific production paths
[ ] documentation complete
[ ] Git diff reviewed
[ ] final model clearly identified as temporary unless Person A selected it
```

---

# 40. FINAL REPORT

At completion provide exactly these sections:

```text
1. Files created
2. Files modified
3. Tests added
4. Targeted test results
5. Full pytest result
6. ONNX status
7. Side-scan integration status
8. API status
9. MCP status
10. Architecture decision
11. Blockers
```

Also provide:

```text
Exact verification commands
```

Include actual measured results.

Do not claim completion if a required verification was not performed.

---

# 41. FINAL GIT CHECK

Before stopping:

```powershell
git status
git diff --stat
git diff
```

Confirm:

```text
V1 untouched
datasets untouched
test split untouched
taxonomy untouched
no secrets
no caches
no accidental files
```

Do NOT automatically push.

Leave the repository ready for human review and shared GitHub integration.

---

# 42. CORE PRINCIPLE

The most important rule is:

> **Build Person B on top of Role 1, do not replace Role 1.**

MarineGuard should become:

```text
                 MARINEGUARD MCP
                       │
          ┌────────────┴────────────┐
          │                         │
     ROLE 1 BASELINE           SSS ENGINEERING
     Frozen V1                 Person B
          │                         │
          └────────────┬────────────┘
                       │
                 COMMON DETECTION
                    INTERFACE
                       │
             ┌─────────┴─────────┐
             │                   │
           FUSION             REPORTING
             │                   │
             └─────────┬─────────┘
                       │
                    API / MCP
                       │
                  SIH FINAL SYSTEM
```

Do not turn SSS into a separate unrelated system.

Do not break the frozen baseline.

Do not fabricate results.

Do not train another model.

Complete the engineering work safely and make the final verified implementation shareable through GitHub.
