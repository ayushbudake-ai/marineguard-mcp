# MarineGuard — Model Registry

## Production Baseline — V1

| Field | Value |
|---|---|
| Model version | `v1` |
| Model name | MarineGuard V1 |
| Architecture | YOLOv8n |
| Task | Object Detection |
| Classes | 50 |
| Input size | 512x512 |
| Checkpoint | `runs/marineguard_full_512_b16-2/weights/best.pt` |
| Distribution | Git LFS |
| Status | FROZEN |

## V1 Evaluation

| Metric | Result |
|---|---:|
| Precision | 89.70% |
| Recall | 71.90% |
| F1 | 79.94% |
| mAP50 | 80.69% |
| mAP50-95 | 55.74% |
| Test images | 1,808 |

## V1 Checksum

The SHA-256 checksum below is generated from the actual V1 checkpoint.

- SHA-256: `18C9E560B9E82BB6EFE3A108584497C4979A9E135BED578DB179341E0778E0D1`
- File size: `6226410` bytes

## V1 Retrieval

1. Clone the repository.
2. Install Git LFS.
3. Run `git lfs pull` if required.
4. Verify the checkpoint exists at:
   `runs/marineguard_full_512_b16-2/weights/best.pt`
5. Compare its SHA-256 against this registry.

## Immutability

This V1 checkpoint must not be silently replaced by V2.

---

## Experimental Candidate — V2

| Field | Value |
|---|---|
| Model version | `v2` |
| Model name | MarineGuard V2 |
| Architecture | YOLOv8n |
| Task | Object Detection |
| Classes | 50 |
| Input size | 512x512 |
| Checkpoint | `runs/marineguard_v2_final/weights/best.pt` |
| Distribution | Git LFS |
| Status | EXPERIMENTAL |

## V2 Evaluation

| Metric | Result |
|---|---:|
| Precision | 86.10% |
| Recall | 73.11% |
| mAP50 | 78.77% |
| mAP50-95 | 53.80% |
| Test images | 1,808 |

> Note: F1 is intentionally omitted because the exact independently recorded V2 F1 value has not been established from the available training metadata. Precision and recall are retained exactly as recorded.

## V2 Checksum

The SHA-256 checksum below is generated from the actual V2 checkpoint.

- SHA-256: `330021F1C535F2B8E2BC227BD234E75892BAA273DED0359CCA6F6F41483AB530`
- File size: `6250026` bytes

## V2 Retrieval

1. Clone the repository.
2. Install Git LFS.
3. Run `git lfs pull` if required.
4. Verify the checkpoint exists at:
   `runs/marineguard_v2_final/weights/best.pt`
5. Compare its SHA-256 against this registry.

## V2 Status

V2 is an experimental candidate and does **not** replace the frozen V1 production baseline.

V1 remains the authoritative baseline because V2 does not improve the recorded mAP50 or mAP50-95 results.

Future model selection must be based on evaluation against the frozen V1 test methodology.
