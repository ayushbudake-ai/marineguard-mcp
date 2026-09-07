# MarineGuard — Role 1 Handoff Checklist

## GitHub-controlled handoff

- [x] V1 dataset available through Git LFS
- [x] SeaClear YOLO dataset available through Git LFS
- [x] V1 best.pt available through Git LFS
- [x] Portable dataset YAML
- [x] Portable evaluation script
- [x] V1 dataset manifest
- [x] V1 test-set manifest
- [x] V1 model registry
- [x] 50-class taxonomy
- [x] Detection JSON schema
- [x] Role 1 → Role 2 handoff
- [x] Role 2 → Role 3 contract
- [x] Role 3 → Role 4 contract
- [x] Role 4 → Role 5 contract
- [x] Role dependency matrix
- [x] No downstream dependency on local Windows paths

## V1 baseline

V1 is the current official downstream baseline.

## V2

V2 is experimental and remains separate until controlled comparison is completed.

## Handoff principle

A teammate working on another computer must be able to clone the repository, obtain Git LFS artifacts, read the handoff documents and continue their assigned role without requesting Role-1 files manually.
