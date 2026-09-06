# MarineGuard — Role Dependency Matrix

## Source of Truth

GitHub repository:
`https://github.com/ayushbudake-ai/marineguard-mcp`

GitHub is the authoritative handoff source. No downstream role should depend on another developer's local filesystem.

## Role Dependency Matrix

| From | To | Required artifact/interface | GitHub location | Status |
|---|---|---|---|---|
| Role 1 | Role 2 | V1 YOLO detector checkpoint | `runs/marineguard_full_512_b16-2/weights/best.pt` | READY |
| Role 1 | Role 2 | V1 dataset | `data/processed/marineguard/` | READY |
| Role 1 | Role 2 | Dataset YAML | `data/processed/marineguard/data.yaml` | READY |
| Role 1 | Role 2 | 50-class taxonomy | `marineguard_classes.yaml` | READY |
| Role 1 | Role 2 | V1 metrics | `ROLE1_FINAL_RESULTS.md` | READY |
| Role 1 | Role 2 | Handoff instructions | `ROLE1_TO_ROLE2_HANDOFF.md` | READY |
| Role 1 | Role 2 | Artifact registry | `docs/MODEL_REGISTRY.md` | READY |
| Role 2 | Role 3 | Detection JSON contract | `docs/DETECTION_SCHEMA.json` | READY |
| Role 2 | Role 3 | class_id / class_name | `marineguard_classes.yaml` | READY |
| Role 2 | Role 3 | confidence | `docs/DETECTION_SCHEMA.json` | READY |
| Role 2 | Role 3 | bbox | `docs/DETECTION_SCHEMA.json` | READY |
| Role 2 | Role 3 | frame_id | `docs/DETECTION_SCHEMA.json` | READY |
| Role 2 | Role 3 | model_version | `docs/DETECTION_SCHEMA.json` | READY |
| Role 3 | Role 4 | filter_status | `docs/HANDOFF_CONTRACT.md` | READY |
| Role 3 | Role 4 | preserved detection identity | `docs/HANDOFF_CONTRACT.md` | READY |
| Role 4 | Role 5 | geolocation | `docs/HANDOFF_CONTRACT.md` | READY |
| Role 4 | Role 5 | timestamp | `docs/HANDOFF_CONTRACT.md` | READY |
| Role 4 | Role 5 | detection identity | `docs/HANDOFF_CONTRACT.md` | READY |

## Role 1 → downstream dependency rule

Roles 2–5 must be able to obtain their required Role-1 interfaces from GitHub without requesting files from Role 1's local computer.

## V1 baseline

V1 remains the official baseline until a controlled V2 comparison replaces it.

## V2

V2 is experimental and must not replace V1 until its evaluation, checksum, manifest and handoff are complete.
