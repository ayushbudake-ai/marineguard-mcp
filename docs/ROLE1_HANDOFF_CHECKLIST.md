# MarineGuard — Role 1 Handoff Checklist

## GitHub-controlled handoff

- [x] SeaClear YOLO dataset available through Git LFS
- [x] V1 best.pt available through Git LFS
- [x] V2 best.pt available through Git LFS
- [x] V1 processed dataset reproduction path documented
- [x] Portable dataset YAML format documented
- [x] Portable evaluation/inference scripts
- [x] V1 dataset manifest
- [x] V1 test-set definition
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

The V1 processed dataset is intentionally not stored directly in GitHub because of its approximately 27.9 GB size. It is reproducible from the documented source datasets, conversion scripts, validation scripts, split definition, and dataset manifest.

The V1 detector checkpoint is directly available through Git LFS.

## V2

V2 is experimental and remains separate from the frozen V1 baseline.

The V2 detector checkpoint is available through Git LFS. V2 does not replace V1 unless a controlled evaluation establishes it as the selected baseline.

## Handoff principle

A teammate working on another computer must be able to clone the repository, obtain Git LFS artifacts, reproduce intentionally untracked generated datasets from the documented pipeline, read the handoff documents, and continue their assigned role without requesting Role-1 files manually.

GitHub is the authoritative handoff source.
