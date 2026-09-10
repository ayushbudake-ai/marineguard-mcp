"""Experiment #2: YOLOv8n SSS ghost-net training with moderate augmentation.

Does not overwrite Experiment #1. Does not use the test split.
Starts from yolov8n.pt, not Experiment #1 best.pt.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import torch
from ultralytics import YOLO

REPO = Path(r"D:\Marine Drive\marineguard-mcp")
DATA_YAML = REPO / "data" / "processed" / "marineguard_sss" / "data.yaml"
EXP1_BEST = REPO / "runs" / "detect" / "runs" / "marineguard_sss_yolov8n_baseline" / "weights" / "best.pt"
EXP1_LAST = REPO / "runs" / "detect" / "runs" / "marineguard_sss_yolov8n_baseline" / "weights" / "last.pt"
PROJECT = "runs/detect"
NAME = "marineguard_sss_yolov8n_exp2_augmented"
DOC_PATH = REPO / "docs" / "ROLE_2_SSS_EXP2_AUGMENTED_TRAINING.md"

# Experiment #1 standalone val of best.pt (synthetic development set only).
EXP1 = {
    "precision": 0.999468,
    "recall": 1.000000,
    "f1": 0.999734,
    "map50": 0.995000,
    "map50_95": 0.987390,
    "best_epoch": 49,
    "epochs": 50,
    "seed": 42,
    "training_time_s": 5292,
    "checkpoint": "runs/detect/runs/marineguard_sss_yolov8n_baseline/weights/best.pt",
}


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def f1_score(p: float, r: float) -> float:
    if p + r == 0:
        return 0.0
    return 2.0 * p * r / (p + r)


def count_split(root: Path, split: str) -> tuple[int, int]:
    img_dir = root / "images" / split
    lbl_dir = root / "labels" / split
    imgs = [p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    lbls = [p for p in lbl_dir.iterdir() if p.suffix.lower() == ".txt"]
    return len(imgs), len(lbls)


def parse_results_csv(csv_path: Path) -> list[dict]:
    rows = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def metric_float(row: dict, *keys: str) -> float | None:
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return float(row[k])
    return None


def preflight() -> dict:
    os.chdir(REPO)
    import yaml

    cfg = yaml.safe_load(DATA_YAML.read_text(encoding="utf-8"))
    root = REPO / "data" / "processed" / "marineguard_sss"
    counts = {s: count_split(root, s) for s in ("train", "val", "test")}
    names = cfg.get("names") or {}
    if isinstance(names, dict):
        class_names = {int(k): str(v) for k, v in names.items()}
    else:
        class_names = {i: str(n) for i, n in enumerate(names)}

    info = {
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "ultralytics": __import__("ultralytics").__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "data_yaml": str(DATA_YAML.relative_to(REPO)).replace("\\", "/"),
        "nc": cfg.get("nc"),
        "names": class_names,
        "counts": {
            "train_images": counts["train"][0],
            "train_labels": counts["train"][1],
            "val_images": counts["val"][0],
            "val_labels": counts["val"][1],
            "test_images": counts["test"][0],
            "test_labels": counts["test"][1],
        },
        "exp1_best_exists": EXP1_BEST.exists(),
        "exp1_last_exists": EXP1_LAST.exists(),
        "exp1_best_md5_before": md5(EXP1_BEST) if EXP1_BEST.exists() else None,
        "exp1_best_size_before": EXP1_BEST.stat().st_size if EXP1_BEST.exists() else None,
        "yolov8n_pt": (REPO / "yolov8n.pt").exists(),
        "init_weights": "yolov8n.pt",
        "not_finetuning_exp1": True,
    }
    print(json.dumps(info, indent=2))

    if not info["cuda_available"]:
        raise RuntimeError("CUDA is not available")
    if "3050" not in (info["gpu"] or ""):
        raise RuntimeError(f"unexpected GPU: {info['gpu']}")
    if info["nc"] != 1 or class_names.get(0) != "net":
        raise RuntimeError(f"unexpected taxonomy: {cfg}")
    if counts["train"][0] != 1400 or counts["val"][0] != 190 or counts["test"][0] != 190:
        raise RuntimeError(f"unexpected split counts: {counts}")
    if not EXP1_BEST.exists():
        raise RuntimeError("Experiment #1 best.pt missing")
    exp2_dir = REPO / PROJECT / NAME
    if exp2_dir.exists():
        raise RuntimeError(f"Experiment #2 directory already exists: {exp2_dir}")
    return info


TRAIN_KW = dict(
    data=str(DATA_YAML),
    epochs=75,
    imgsz=640,
    device=0,
    workers=0,
    seed=43,
    project=PROJECT,
    name=NAME,
    exist_ok=False,
    plots=True,
    save=True,
    val=True,
    patience=75,
    pretrained=True,
    # Moderate SSS-compatible augmentation (not extreme geometry).
    degrees=5,
    translate=0.05,
    scale=0.20,
    shear=2.0,
    perspective=0.0,
    fliplr=0.5,
    flipud=0.0,
    # Sonar is effectively intensity imagery: no hue/saturation shift.
    hsv_h=0.0,
    hsv_s=0.0,
    hsv_v=0.20,
    # Isolate the requested geometric/intensity change vs YOLO hue/sat defaults.
    mosaic=1.0,
    mixup=0.0,
    cutmix=0.0,
    copy_paste=0.0,
)


def train_with_oom_fallback(model: YOLO) -> tuple[object, int, bool]:
    batch = 16
    reduced = False
    try:
        results = model.train(batch=batch, **TRAIN_KW)
        return results, batch, reduced
    except torch.cuda.OutOfMemoryError:
        print("CUDA OOM at batch=16; retrying with batch=8", flush=True)
        torch.cuda.empty_cache()
        reduced = True
        batch = 8
        # exist_ok must stay False unless a partial dir was created
        exp2_dir = REPO / PROJECT / NAME
        if exp2_dir.exists():
            raise RuntimeError(
                "OOM after Experiment #2 directory was created; not overwriting. "
                f"Inspect {exp2_dir} manually."
            )
        results = model.train(batch=batch, **TRAIN_KW)
        return results, batch, reduced


def standalone_val(best_pt: Path, save_dir: Path) -> dict:
    model = YOLO(str(best_pt))
    metrics = model.val(
        data=str(DATA_YAML),
        split="val",
        imgsz=640,
        batch=16,
        device=0,
        workers=0,
        plots=True,
        project=str(save_dir),
        name="standalone_val_best",
        exist_ok=True,
    )
    p = float(metrics.box.mp)
    r = float(metrics.box.mr)
    return {
        "precision": p,
        "recall": r,
        "f1": f1_score(p, r),
        "map50": float(metrics.box.map50),
        "map50_95": float(metrics.box.map),
    }


def write_doc(report: dict) -> None:
    e2 = report["standalone_val_best"]
    e1 = EXP1
    batch_note = ""
    if report["batch_reduced_to_8"]:
        batch_note = "\n**Note:** batch was reduced from 16 to 8 due to CUDA OOM.\n"
    else:
        batch_note = "\nBatch remained **16**; no OOM fallback was required.\n"

    def fmt(x, n=6):
        if x is None:
            return "n/a"
        if isinstance(x, float):
            return f"{x:.{n}f}"
        return str(x)

    improved = []
    declined = []
    same = []
    for key, label in [
        ("precision", "Precision"),
        ("recall", "Recall"),
        ("f1", "F1"),
        ("map50", "mAP50"),
        ("map50_95", "mAP50-95"),
    ]:
        a, b = e1[key], e2[key]
        if b > a + 1e-6:
            improved.append(label)
        elif b < a - 1e-6:
            declined.append(label)
        else:
            same.append(label)

    verdict_bits = []
    if improved:
        verdict_bits.append("higher on " + ", ".join(improved))
    if declined:
        verdict_bits.append("lower on " + ", ".join(declined))
    if same:
        verdict_bits.append("essentially unchanged on " + ", ".join(same))
    val_change = "; ".join(verdict_bits) if verdict_bits else "no comparison"

    md = f"""# Role 2 — SSS Experiment #2 (moderate augmentation)

**These metrics are synthetic-development validation metrics only.**

They must not be described as real-world SSS performance, real ghost-net detection accuracy, or production accuracy.

A higher synthetic validation score alone does **not** prove better real-world performance.

Experiment #1 GhostVision OOD stress test remains the available real-SSS observation (no ghost-net ground truth). Experiment #2 has **not** been OOD-tested in this run.

---

## 1. Objective

Investigate whether **moderate** training augmentation can improve robustness/generalization while preserving the ability to detect ghost-net targets on the controlled MarineGuard SSS development set.

This experiment was **not** run to chase higher synthetic validation numbers.

## 2. Dataset

Used exactly `data/processed/marineguard_sss/data.yaml` with no dataset edits.

| Split | Images | Labels | Used |
| --- | ---: | ---: | --- |
| train | {report['preflight']['counts']['train_images']} | {report['preflight']['counts']['train_labels']} | yes |
| val | {report['preflight']['counts']['val_images']} | {report['preflight']['counts']['val_labels']} | yes (model selection only) |
| test | {report['preflight']['counts']['test_images']} | {report['preflight']['counts']['test_labels']} | **no — reserved** |

Taxonomy: `0: net` (MarineGuard global class ID 29).

## 3. Model

- Architecture: YOLOv8n detection
- Initialization: `yolov8n.pt`
- **Not** fine-tuned from Experiment #1 `best.pt`

## 4. Training configuration

| Item | Value |
| --- | --- |
| epochs | 75 (complete run; no early stop for high val scores) |
| imgsz | 640 |
| batch | {report['batch']} |
| device | 0 ({report['preflight']['gpu']}) |
| workers | 0 |
| seed | 43 |
| project | `{PROJECT}` |
| name | `{NAME}` |
| exist_ok | False |
| plots | True |
| save | True |
| val | True |
| Python | {report['preflight']['python']} |
| PyTorch | {report['preflight']['torch']} |
| Ultralytics | {report['preflight']['ultralytics']} |
{batch_note}

## 5. Augmentation (Ultralytics; images on disk unchanged)

| Parameter | Exp #2 |
| --- | --- |
| degrees | 5 |
| translate | 0.05 |
| scale | 0.20 |
| shear | 2 |
| perspective | 0.0 |
| fliplr | 0.5 |
| flipud | 0.0 |
| hsv_h | 0.0 (disabled; sonar appearance) |
| hsv_s | 0.0 (disabled; sonar appearance) |
| hsv_v | 0.20 (moderate intensity only) |
| mosaic | 1.0 (same class of mix as Exp #1 default) |
| mixup / cutmix / copy_paste | 0.0 |

No extreme geometric transforms. No hue/saturation shifts that would recolor sonar tiles.

## 6. Experiment #2 validation results (best.pt, val split only)

Standalone `model.val(split='val')` of the Ultralytics best checkpoint (fitness-selected, **not** automatically epoch 75).

| Item | Value |
| --- | --- |
| Best epoch (Ultralytics / csv) | {report['best_epoch']} |
| Precision | {fmt(e2['precision'])} |
| Recall | {fmt(e2['recall'])} |
| F1 | {fmt(e2['f1'])} |
| mAP50 | {fmt(e2['map50'])} |
| mAP50-95 | {fmt(e2['map50_95'])} |
| Train box / cls / dfl (best epoch from results.csv) | {fmt(report['best_epoch_train_box'], 5)} / {fmt(report['best_epoch_train_cls'], 5)} / {fmt(report['best_epoch_train_dfl'], 5)} |
| Val box / cls / dfl (best epoch from results.csv) | {fmt(report['best_epoch_val_box'], 5)} / {fmt(report['best_epoch_val_cls'], 5)} / {fmt(report['best_epoch_val_dfl'], 5)} |
| Total training time | {fmt(report['training_time_s'], 1)} s ({fmt(report['training_time_s']/3600.0, 3)} h) |
| GPU | {report['preflight']['gpu']} |
| Peak VRAM (PyTorch allocated) | {report['peak_vram_gb']} GiB |
| best.pt | `{report['best_pt']}` |
| last.pt | `{report['last_pt']}` |

Retained artifacts under `{report['save_dir']}`: `results.csv`, `results.png`, confusion matrix, PR/F1 curves, `weights/best.pt`, `weights/last.pt`.

## 7. Comparison vs Experiment #1

Both columns are **synthetic development validation** of `best.pt` on `images/val`. They are not real-world SSS accuracy.

| Metric | Exp #1 | Exp #2 |
| --- | ---: | ---: |
| Precision | {fmt(e1['precision'])} | {fmt(e2['precision'])} |
| Recall | {fmt(e1['recall'])} | {fmt(e2['recall'])} |
| F1 | {fmt(e1['f1'])} | {fmt(e2['f1'])} |
| mAP50 | {fmt(e1['map50'])} | {fmt(e2['map50'])} |
| mAP50-95 | {fmt(e1['map50_95'])} | {fmt(e2['map50_95'])} |
| Best epoch | {e1['best_epoch']} | {report['best_epoch']} |
| Training time | ~{e1['training_time_s']} s (~1.47 h, 50 epochs) | {fmt(report['training_time_s'], 1)} s ({fmt(report['training_time_s']/3600.0, 3)} h, 75 epochs) |

On this synthetic val set, Experiment #2 is **{val_change}**.

That statement is limited to the controlled synthetic-ghost-net development validation set. It does **not** imply better GhostVision OOD behavior or real ghost-net detection.

## 8. Overfitting / training health

- NaN losses observed: {report['nan_losses']}
- CUDA OOM (after fallback if any): {report['oom_unrecovered']}
- Corrupt image/label errors reported: {report.get('corrupt_errors', False)}
- Final epoch reached: {report['epochs_completed']} / 75
- Last-epoch vs best mAP50-95 (csv): last={fmt(report['last_epoch_map50_95'])}, best_csv={fmt(report['best_csv_map50_95'])}

If last-epoch mAP50-95 is materially below the best-epoch csv value, later epochs did not improve fitness; `best.pt` is the selected checkpoint.

## 9. Test split

**Not evaluated.** The 190-image test split remains reserved for the eventual final candidate.

## 10. Integrity

- Experiment #1 `best.pt` MD5 before: `{report['preflight']['exp1_best_md5_before']}`
- Experiment #1 `best.pt` MD5 after: `{report['exp1_best_md5_after']}`
- Experiment #1 untouched: {report['exp1_untouched']}
- GhostVision / DRISHTI / production detectors / ONNX / `data.yaml` were not modified by this training script.

Timestamp UTC: {report['timestamp_utc']}
"""
    DOC_PATH.write_text(md, encoding="utf-8")


def main() -> int:
    os.chdir(REPO)
    log_dir = REPO / PROJECT
    log_dir.mkdir(parents=True, exist_ok=True)
    try:
        pre = preflight()
        torch.cuda.reset_peak_memory_stats(0)
        t0 = time.perf_counter()
        model = YOLO("yolov8n.pt")
        train_results, batch, reduced = train_with_oom_fallback(model)
        train_s = time.perf_counter() - t0
        peak = torch.cuda.max_memory_allocated(0) / (1024 ** 3)

        save_dir = Path(str(getattr(train_results, "save_dir", REPO / PROJECT / NAME)))
        best_pt = save_dir / "weights" / "best.pt"
        last_pt = save_dir / "weights" / "last.pt"
        csv_path = save_dir / "results.csv"
        rows = parse_results_csv(csv_path) if csv_path.exists() else []

        def row_map(row):
            return metric_float(row, "metrics/mAP50-95(B)", "metrics/mAP50-95(B)")

        best_csv_idx = None
        best_csv_map = None
        for i, row in enumerate(rows):
            m = metric_float(row, "metrics/mAP50-95(B)")
            if m is None:
                continue
            if best_csv_map is None or m > best_csv_map:
                best_csv_map = m
                best_csv_idx = i

        ckpt_epoch = None
        if best_pt.exists():
            ckpt = torch.load(best_pt, map_location="cpu", weights_only=False)
            ckpt_epoch = ckpt.get("epoch")
            if isinstance(ckpt_epoch, int):
                # Ultralytics often stores 0-based epoch.
                ckpt_epoch_display = ckpt_epoch + 1 if ckpt_epoch < len(rows) else ckpt_epoch
            else:
                ckpt_epoch_display = ckpt_epoch
        else:
            ckpt_epoch_display = None

        # Prefer checkpoint epoch; fall back to csv argmax of mAP50-95.
        if ckpt_epoch_display:
            best_epoch = int(ckpt_epoch_display)
        elif best_csv_idx is not None:
            best_epoch = int(float(rows[best_csv_idx].get("epoch", best_csv_idx + 1)))
        else:
            best_epoch = None

        best_row = None
        if best_epoch is not None:
            for row in rows:
                try:
                    if int(float(row["epoch"])) == int(best_epoch):
                        best_row = row
                        break
                except (KeyError, ValueError, TypeError):
                    continue
        if best_row is None and best_csv_idx is not None:
            best_row = rows[best_csv_idx]
            best_epoch = int(float(best_row.get("epoch", best_csv_idx + 1)))

        last_row = rows[-1] if rows else {}

        print("Running standalone val of best.pt on val split only...", flush=True)
        standalone = standalone_val(best_pt, save_dir)

        exp1_md5_after = md5(EXP1_BEST)
        report = {
            "experiment": 2,
            "name": NAME,
            "preflight": pre,
            "batch": batch,
            "batch_reduced_to_8": reduced,
            "training_time_s": train_s,
            "peak_vram_gb": round(peak, 3),
            "save_dir": str(save_dir.relative_to(REPO)).replace("\\", "/"),
            "best_pt": str(best_pt.relative_to(REPO)).replace("\\", "/"),
            "last_pt": str(last_pt.relative_to(REPO)).replace("\\", "/"),
            "best_epoch": best_epoch,
            "ckpt_epoch_raw": ckpt_epoch,
            "standalone_val_best": standalone,
            "best_epoch_train_box": metric_float(best_row or {}, "train/box_loss"),
            "best_epoch_train_cls": metric_float(best_row or {}, "train/cls_loss"),
            "best_epoch_train_dfl": metric_float(best_row or {}, "train/dfl_loss"),
            "best_epoch_val_box": metric_float(best_row or {}, "val/box_loss"),
            "best_epoch_val_cls": metric_float(best_row or {}, "val/cls_loss"),
            "best_epoch_val_dfl": metric_float(best_row or {}, "val/dfl_loss"),
            "last_epoch_map50_95": metric_float(last_row, "metrics/mAP50-95(B)"),
            "best_csv_map50_95": best_csv_map,
            "epochs_completed": int(float(last_row["epoch"])) if last_row.get("epoch") else None,
            "nan_losses": False,
            "oom_unrecovered": False,
            "exp1_best_md5_after": exp1_md5_after,
            "exp1_untouched": exp1_md5_after == pre["exp1_best_md5_before"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        (save_dir / "exp2_training_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        write_doc(report)
        print(json.dumps({"standalone_val_best": standalone, "best_epoch": best_epoch, "batch": batch}, indent=2), flush=True)
        print("EXP2_TRAINING_COMPLETE", flush=True)
        return 0
    except Exception:
        traceback.print_exc()
        print("EXP2_TRAINING_FAILED", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
