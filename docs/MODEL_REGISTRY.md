# MarineGuard — V1 Model Registry

## Production Baseline

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

## Checksum

The SHA-256 checksum below is generated from the actual checkpoint in the current Role-1 working tree.

- SHA-256: `18C9E560B9E82BB6EFE3A108584497C4979A9E135BED578DB179341E0778E0D1`
- File size: `6226410` bytes

## Retrieval

1. Clone the repository.
2. Install Git LFS.
3. Run `git lfs pull` if required.
4. Verify the checkpoint exists at:
   `runs/marineguard_full_512_b16-2/weights/best.pt`
5. Compare its SHA-256 against this registry.

## Immutability

This V1 checkpoint must not be silently replaced by V2.
