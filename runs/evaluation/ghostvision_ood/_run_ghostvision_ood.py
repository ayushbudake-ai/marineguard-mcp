"""Read-only GhostVision OOD inference for the SSS YOLOv8n baseline.

Does not train, does not modify GhostVision, DRISHTI, or production models.
"""
from __future__ import annotations

import json
import shutil
import statistics
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO

REPO = Path(r"D:\Marine Drive\marineguard-mcp")
GV = Path(r"C:\MarineGuard-SSS\GhostVision")
CKPT = REPO / "runs" / "detect" / "runs" / "marineguard_sss_yolov8n_baseline" / "weights" / "best.pt"
OUT = REPO / "runs" / "evaluation" / "ghostvision_ood"
SPLITS = ("train", "valid", "test")
CONF = 0.25
IMGSZ = 640
DEVICE = 0
BATCH = 8
CHUNK = 64
IOU_OVERLAP = 0.30
NEAR_PX = 50.0
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def xywh_to_xyxy(box: list[float]) -> list[float]:
    x, y, w, h = box
    return [x, y, x + w, y + h]


def iou_xyxy(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def center(box: list[float]) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def load_crabpot_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    for split in SPLITS:
        jsonl = GV / split / "metadata.jsonl"
        with jsonl.open("r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                boxes = [xywh_to_xyxy(b) for b in rec["objects"]["bbox"]]
                cats = rec["objects"]["category"]
                key = f"{split}/{rec['file_name']}"
                index[key] = {"boxes": boxes, "categories": cats, "split": split, "file_name": rec["file_name"]}
    return index


def classify_pred_vs_crabpot(pred: list[float], pots: list[list[float]]) -> str:
    if not pots:
        return "elsewhere_no_crabpot_annotation"
    best_iou = max(iou_xyxy(pred, p) for p in pots)
    if best_iou >= IOU_OVERLAP:
        return "overlaps_crabpot_annotation"
    pc = center(pred)
    best_d = min(dist(pc, center(p)) for p in pots)
    if best_d <= NEAR_PX:
        return "near_crabpot_annotation"
    return "elsewhere"


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    f = int(np.floor(k))
    c = int(np.ceil(k))
    if f == c:
        return xs[f]
    return xs[f] * (c - k) + xs[c] * (k - f)


def save_annotated(img_path: Path, preds: list[dict], dest: Path, pots: list[list[float]] | None = None) -> None:
    img = cv2.imread(str(img_path))
    if img is None:
        return
    if pots:
        for p in pots:
            x1, y1, x2, y2 = [int(round(v)) for v in p]
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 0), 1)
    for det in preds:
        x1, y1, x2, y2 = [int(round(v)) for v in det["xyxy"]]
        conf = det["confidence"]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        label = f"net {conf:.3f}"
        cv2.putText(img, label, (x1, max(12, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dest), img)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "annotated").mkdir(exist_ok=True)
    (OUT / "examples" / "highest_confidence").mkdir(parents=True, exist_ok=True)
    (OUT / "examples" / "medium_confidence").mkdir(parents=True, exist_ok=True)
    (OUT / "examples" / "zero_detections").mkdir(parents=True, exist_ok=True)

    verify = {
        "checkpoint": str(CKPT),
        "checkpoint_exists": CKPT.exists(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "device0_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    if not CKPT.exists():
        raise FileNotFoundError(CKPT)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")

    model = YOLO(str(CKPT))
    names = model.names
    if isinstance(names, dict):
        class_names = {int(k): str(v) for k, v in names.items()}
    else:
        class_names = {i: str(n) for i, n in enumerate(names)}
    verify.update(
        {
            "task": getattr(model, "task", None),
            "class_count": len(class_names),
            "class_names": class_names,
            "class0": class_names.get(0),
        }
    )
    print(json.dumps(verify, indent=2))
    if verify["task"] != "detect":
        raise RuntimeError(f"unexpected task: {verify['task']}")
    if verify["class_count"] != 1 or verify["class0"] != "net":
        raise RuntimeError(f"unexpected classes: {class_names}")

    crabpot = load_crabpot_index()
    image_records: list[dict] = []
    detections: list[dict] = []
    confs: list[float] = []
    split_stats: dict[str, dict] = {}
    relation_counts = Counter()

    # Warmup
    first_img = next((GV / "valid").glob("*.jpg"))
    _ = model.predict(source=str(first_img), conf=CONF, imgsz=IMGSZ, device=DEVICE, verbose=False)

    t0 = time.perf_counter()
    for split in SPLITS:
        split_dir = GV / split
        images = sorted(p for p in split_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        split_start = time.perf_counter()
        split_det = 0
        split_img_with = 0
        split_confs: list[float] = []
        for chunk_start in range(0, len(images), CHUNK):
            chunk = images[chunk_start : chunk_start + CHUNK]
            results = model.predict(
                source=[str(p) for p in chunk],
                conf=CONF,
                imgsz=IMGSZ,
                device=DEVICE,
                batch=BATCH,
                verbose=False,
                stream=True,
                save=False,
            )
            for img_path, result in zip(chunk, results, strict=True):
                key = f"{split}/{img_path.name}"
                pots = crabpot[key]["boxes"]
                preds: list[dict] = []
                if result.boxes is not None and len(result.boxes) > 0:
                    xyxy = result.boxes.xyxy.cpu().numpy()
                    scores = result.boxes.conf.cpu().numpy()
                    clss = result.boxes.cls.cpu().numpy()
                    for box, score, cls_id in zip(xyxy, scores, clss):
                        pred_box = [float(box[0]), float(box[1]), float(box[2]), float(box[3])]
                        relation = classify_pred_vs_crabpot(pred_box, pots)
                        relation_counts[relation] += 1
                        det = {
                            "image": key,
                            "split": split,
                            "class_id": int(cls_id),
                            "class_name": class_names[int(cls_id)],
                            "confidence": float(score),
                            "xyxy": pred_box,
                            "relation_to_crabpot_annotation": relation,
                            "n_crabpot_annotations": len(pots),
                        }
                        preds.append(det)
                        detections.append(det)
                        confs.append(float(score))
                        split_confs.append(float(score))
                rec = {
                    "image": key,
                    "split": split,
                    "n_predicted_net": len(preds),
                    "max_confidence": max((d["confidence"] for d in preds), default=None),
                    "n_crabpot_annotations": len(pots),
                    "predictions": preds,
                }
                image_records.append(rec)
                split_det += len(preds)
                if preds:
                    split_img_with += 1
                    save_annotated(img_path, preds, OUT / "annotated" / split / img_path.name, pots=pots)
            torch.cuda.empty_cache()
        split_elapsed = time.perf_counter() - split_start
        split_stats[split] = {
            "images": len(images),
            "images_with_predicted_net": split_img_with,
            "images_without_predicted_net": len(images) - split_img_with,
            "total_predicted_net": split_det,
            "elapsed_s": split_elapsed,
            "latency_ms_per_image": (split_elapsed / len(images) * 1000.0) if images else None,
            "confidence": {
                "n": len(split_confs),
                "min": min(split_confs) if split_confs else None,
                "mean": float(statistics.fmean(split_confs)) if split_confs else None,
                "median": float(statistics.median(split_confs)) if split_confs else None,
                "max": max(split_confs) if split_confs else None,
            },
        }
        print(f"split {split}: images={len(images)} with_net={split_img_with} dets={split_det}")

    elapsed = time.perf_counter() - t0
    n_images = len(image_records)
    n_with = sum(1 for r in image_records if r["n_predicted_net"] > 0)
    n_without = n_images - n_with
    bins = {"0.25-0.40": 0, "0.40-0.60": 0, "0.60-0.80": 0, "0.80-1.00": 0}
    for c in confs:
        if c < 0.40:
            bins["0.25-0.40"] += 1
        elif c < 0.60:
            bins["0.40-0.60"] += 1
        elif c < 0.80:
            bins["0.60-0.80"] += 1
        else:
            bins["0.80-1.00"] += 1

    # Representative examples
    with_det = [r for r in image_records if r["n_predicted_net"] > 0]
    with_det_sorted = sorted(with_det, key=lambda r: r["max_confidence"] or 0.0, reverse=True)
    highest = with_det_sorted[:10]
    if with_det_sorted:
        conf_list = [r["max_confidence"] for r in with_det_sorted]
        med = statistics.median(conf_list)
        remaining = [r for r in with_det_sorted if r not in highest]
        remaining.sort(key=lambda r: abs((r["max_confidence"] or 0.0) - med))
        medium = remaining[:10]
        if len(medium) < 10:
            # fewer than 20 detection images; take next unused after highest
            used = {r["image"] for r in highest}
            medium = [r for r in with_det_sorted if r["image"] not in used][:10]
    else:
        medium = []
    zeros = [r for r in image_records if r["n_predicted_net"] == 0]
    rng = np.random.default_rng(42)
    if zeros:
        idx = rng.choice(len(zeros), size=min(10, len(zeros)), replace=False)
        zero_examples = [zeros[int(i)] for i in idx]
    else:
        zero_examples = []

    def copy_example(records: list[dict], dest_dir: Path, draw_pots: bool) -> list[str]:
        names = []
        dest_dir.mkdir(parents=True, exist_ok=True)
        for rec in records:
            split, fn = rec["image"].split("/", 1)
            src = GV / split / fn
            pots = crabpot[rec["image"]]["boxes"] if draw_pots else []
            save_annotated(src, rec["predictions"], dest_dir / f"{split}__{fn}", pots=pots if rec["predictions"] else None)
            names.append(rec["image"])
        return names

    example_index = {
        "highest_confidence": copy_example(highest, OUT / "examples" / "highest_confidence", True),
        "medium_confidence": copy_example(medium, OUT / "examples" / "medium_confidence", True),
        "zero_detections": copy_example(zero_examples, OUT / "examples" / "zero_detections", False),
        "note": "Cyan boxes (when present) are GhostVision crab-pot annotations for qualitative comparison only. Red boxes are predicted net. Crab pots are not ghost-net labels.",
    }

    summary = {
        "task": "real_sss_ood_false_positive_stress_test",
        "scientific_notice": (
            "This is an OOD/false-positive stress test, not a ground-truth ghost-net accuracy evaluation. "
            "GhostVision contains real SSS imagery but does not provide ghost-net ground truth for this evaluation."
        ),
        "model": {
            "architecture": "YOLOv8n detection",
            "initialization": "yolov8n.pt",
            "checkpoint": str(CKPT.relative_to(REPO)).replace("\\", "/"),
            "task": verify["task"],
            "class_count": verify["class_count"],
            "classes": class_names,
            "local_class_0": "net",
            "marineguard_global_class_id": 29,
        },
        "environment": {
            "python": "3.14.5",
            "torch": torch.__version__,
            "ultralytics": getattr(__import__("ultralytics"), "__version__", None),
            "device": f"cuda:{DEVICE}",
            "device_name": verify["device0_name"],
        },
        "inference": {
            "conf": CONF,
            "imgsz": IMGSZ,
            "device": DEVICE,
            "batch": BATCH,
            "source": str(GV),
            "training": False,
        },
        "dataset": {
            "name": "GhostVision / PINGEcosystem sss-crab-pot-detection-ds",
            "path": str(GV),
            "images_evaluated": n_images,
            "splits": {k: v["images"] for k, v in split_stats.items()},
            "annotation_classes_present": ["Crab-Pot"],
            "ghost_net_ground_truth": False,
        },
        "results": {
            "images_evaluated": n_images,
            "images_with_predicted_net": n_with,
            "images_without_predicted_net": n_without,
            "pct_images_with_predicted_net": (n_with / n_images * 100.0) if n_images else None,
            "pct_images_without_predicted_net": (n_without / n_images * 100.0) if n_images else None,
            "total_predicted_net_detections": len(detections),
            "detections_per_image_mean": (len(detections) / n_images) if n_images else None,
            "confidence": {
                "n": len(confs),
                "min": min(confs) if confs else None,
                "mean": float(statistics.fmean(confs)) if confs else None,
                "median": float(statistics.median(confs)) if confs else None,
                "max": max(confs) if confs else None,
                "p25": percentile(confs, 0.25),
                "p75": percentile(confs, 0.75),
                "p90": percentile(confs, 0.90),
            },
            "confidence_bins_count": bins,
            "relation_to_crabpot_annotation": dict(relation_counts),
            "relation_definitions": {
                "overlaps_crabpot_annotation": f"IoU >= {IOU_OVERLAP} with a Crab-Pot box",
                "near_crabpot_annotation": f"IoU < {IOU_OVERLAP} and center distance <= {NEAR_PX} px",
                "elsewhere": "a crab-pot annotation exists on the image but the predicted net is neither overlapping nor near",
                "elsewhere_no_crabpot_annotation": "image has no crab-pot annotation",
            },
            "qualitative_note": (
                "Crab-pot overlap is qualitative only. It is not ghost-net precision, recall, F1, or mAP. "
                "Predicted net detections on this dataset are predicted net detections on a real SSS OOD "
                "dataset without ghost-net ground truth."
            ),
        },
        "latency": {
            "includes_warmup": False,
            "warmup_note": "One valid-split image was predicted before timed evaluation.",
            "total_eval_s": elapsed,
            "ms_per_image": (elapsed / n_images * 1000.0) if n_images else None,
            "per_split": {k: {"elapsed_s": v["elapsed_s"], "ms_per_image": v["latency_ms_per_image"]} for k, v in split_stats.items()},
        },
        "per_split": split_stats,
        "examples": example_index,
        "outputs": {
            "directory": str(OUT.relative_to(REPO)).replace("\\", "/"),
            "predictions_json": "predictions.json",
            "summary_json": "ghostvision_ood_report.json",
            "annotated_images_with_detections": "annotated/",
            "examples": "examples/",
        },
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "verify": verify,
    }

    (OUT / "ghostvision_ood_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "predictions.json").write_text(
        json.dumps({"images": image_records, "detections": detections}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({k: summary[k] for k in ("results", "latency")}, indent=2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
