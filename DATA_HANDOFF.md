# Data Handoff — Member 1 → Member 2

Member 1's 150GB labeled dataset lives locally and needs to land in this
exact structure. Once it does, **no code changes are needed** — everything
below already points at these paths.

```
data/processed/marineguard/
├── data.yaml                  # already exists, already points here
├── images/
│   ├── train/                 # .jpg / .png sonar + optical frames
│   ├── val/
│   └── test/
└── labels/
    ├── train/                 # YOLO-format .txt labels, one per image
    ├── val/
    └── test/
```

- Class list is already frozen in `data.yaml` / `marineguard_classes.yaml` (50 classes) — don't regenerate it, just make sure label files use these exact class indices.
- `images/{split}/foo.jpg` must have a matching `labels/{split}/foo.txt`.

## Because the dataset is 150GB, don't push it to GitHub

Copy it directly onto whatever machine will actually run training (needs a
GPU — this repo's training script will run painfully slowly or not at all
on CPU-only hardware). Git is the wrong tool for 150GB; committing it would
break the repo for everyone else. If you need it in version control, use
Git LFS or a dataset artifact store instead of a plain commit.

## What happens automatically once the data is in place

1. `python run_full_training.py` — trains YOLOv8-seg, auto-detects GPU/CPU, and copies the best checkpoint to `models/best.pt`.
2. `python export_onnx.py` — exports `models/best.pt` → `models/best.onnx`.
3. `marineguard/detection/{side_scan,optical,bathymetry}.py` — automatically switch from stub/fallback mode to real-model mode the moment `models/best.pt` exists. No flag to flip, no import to uncomment.
4. `python eval_detection.py` — computes real precision/recall/F1/mAP on the held-out `test` split and writes `data/reports/detection_metrics.json`.
5. `python retune_fusion_weights.py` — once you also have a `fusion_validation.json` export (see the script's docstring for the expected format), grid-searches better per-sensor fusion weights than the current hand-guessed defaults.

## What's still a manual step even after data arrives

- Updating `MultiSensorFusionEngine.DEFAULT_WEIGHTS` in `fusion.py` with whatever `retune_fusion_weights.py` finds — this is a one-line edit, not automated on purpose so a human reviews the number before it ships.
- Deciding whether `bathymetry.py`'s model-based path is actually usable — see the caveat in that file's docstring; it depends on whether Member 1's dataset includes depth-grid-style training examples at all, or only side-scan/optical imagery.
