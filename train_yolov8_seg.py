import os
import sys
import json
import time
from pathlib import Path
import torch
from ultralytics import YOLO
from ultralytics.data.utils import check_det_dataset

REPO_ROOT = Path(__file__).resolve().parent
DATA_YAML = REPO_ROOT / "data" / "processed" / "seaclear_segmentation" / "data.yaml"
RUNS_DIR = REPO_ROOT / "runs" / "seaclear_yolov8n_seg"
PRETRAINED_MODEL = "yolov8n-seg.pt"

# Configuration
IMGSZ = 512
EPOCHS = 50
BATCH = 16
WORKERS = 0
AMP = True
SEED = 42

def run_sanity_checks():
    print("=" * 60)
    print("SEACLEAR YOLOV8N-SEG PRE-TRAINING SANITY CHECK")
    print("=" * 60)
    
    # 1. Check data yaml
    if not DATA_YAML.exists():
        raise FileNotFoundError(f"data.yaml not found at {DATA_YAML}")
    print(f"[PASS] data.yaml exists at: {DATA_YAML}")
    
    ds = check_det_dataset(str(DATA_YAML))
    print(f"[PASS] Dataset configuration parsed: nc={ds.get('nc')}")
    
    # 2. Check image & label paths
    train_imgs = list(Path(ds['train']).glob("*.jpg"))
    val_imgs = list(Path(ds['val']).glob("*.jpg"))
    test_imgs = list(Path(ds['test']).glob("*.jpg"))
    
    train_lbls = list((Path(ds['train']).parent.parent / "labels" / "train").glob("*.txt"))
    val_lbls = list((Path(ds['val']).parent.parent / "labels" / "val").glob("*.txt"))
    test_lbls = list((Path(ds['test']).parent.parent / "labels" / "test").glob("*.txt"))
    
    print(f"[INFO] Train images: {len(train_imgs)}, Train labels: {len(train_lbls)}")
    print(f"[INFO] Val images:   {len(val_imgs)}, Val labels:   {len(val_lbls)}")
    print(f"[INFO] Test images:  {len(test_imgs)}, Test labels:  {len(test_lbls)}")
    
    if len(train_imgs) != 6027 or len(val_imgs) != 1722 or len(test_imgs) != 861:
        raise ValueError(f"Unexpected image counts: train={len(train_imgs)}, val={len(val_imgs)}, test={len(test_imgs)}")
    if len(train_lbls) != 6027 or len(val_lbls) != 1722 or len(test_lbls) != 861:
        raise ValueError(f"Unexpected label counts: train={len(train_lbls)}, val={len(val_lbls)}, test={len(test_lbls)}")
    print("[PASS] Dataset counts match expected 8,610 images and 8,610 segmentation labels.")
    
    # 3. Check sample polygon label
    sample_lbl = train_lbls[0]
    with open(sample_lbl) as f:
        first_line = f.readline().strip().split()
    if len(first_line) < 6:
        raise ValueError(f"Label {sample_lbl.name} does not appear to contain polygon coordinates ({len(first_line)} tokens)")
    print(f"[PASS] Sample label verified as polygon annotation ({len(first_line)} tokens in first instance).")
    
    # 4. Check model architecture
    model = YOLO(PRETRAINED_MODEL)
    if model.task != "segment":
        raise ValueError(f"Model task is {model.task}, expected 'segment'")
    print(f"[PASS] Loaded pretrained model {PRETRAINED_MODEL} with task='segment'.")
    
    # 5. Device check
    device = 0 if torch.cuda.is_available() else "cpu"
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"[INFO] Compute device: {device} ({device_name})")
    print("=" * 60)
    print("SANITY CHECK COMPLETE: ALL CHECKS PASSED")
    print("=" * 60)
    return device, ds

def main():
    device, ds = run_sanity_checks()
    
    print("\nStarting YOLOv8n-seg training on SeaClear dataset...")
    model = YOLO(PRETRAINED_MODEL)
    
    start_time = time.time()
    batch_size = BATCH
    
    try:
        results = model.train(
            data=str(DATA_YAML),
            epochs=EPOCHS,
            imgsz=IMGSZ,
            batch=batch_size,
            workers=WORKERS,
            amp=AMP,
            device=device,
            project=str(RUNS_DIR),
            name="train",
            seed=SEED,
            deterministic=True,
            exist_ok=True,
            save=True,
            plots=True,
            verbose=True,
        )
    except RuntimeError as e:
        if "CUDA out of memory" in str(e) or "out of memory" in str(e):
            print("\n[WARNING] CUDA OOM encountered with batch=16. Retrying with batch=8...")
            batch_size = 8
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            model = YOLO(PRETRAINED_MODEL)
            results = model.train(
                data=str(DATA_YAML),
                epochs=EPOCHS,
                imgsz=IMGSZ,
                batch=batch_size,
                workers=WORKERS,
                amp=AMP,
                device=device,
                project=str(RUNS_DIR),
                name="train",
                seed=SEED,
                deterministic=True,
                exist_ok=True,
                save=True,
                plots=True,
                verbose=True,
            )
        else:
            raise e
            
    training_duration = time.time() - start_time
    print(f"\nTraining completed in {training_duration / 60:.2f} minutes ({training_duration:.1f} seconds).")
    
    best_weights = RUNS_DIR / "train" / "weights" / "best.pt"
    if not best_weights.exists():
        best_weights = RUNS_DIR / "train" / "weights" / "last.pt"
    print(f"Best checkpoint path: {best_weights}")
    
    # Load best trained model for rigorous evaluation
    trained_model = YOLO(str(best_weights))
    
    # 1. Validation Set Evaluation
    print("\n" + "=" * 60)
    print("EVALUATION ON VALIDATION SPLIT")
    print("=" * 60)
    val_results = trained_model.val(
        data=str(DATA_YAML),
        split="val",
        imgsz=IMGSZ,
        batch=batch_size,
        workers=WORKERS,
        device=device,
        project=str(RUNS_DIR),
        name="val_evaluation",
        plots=True,
        exist_ok=True,
    )
    
    # 2. Held-Out Test Set Evaluation
    print("\n" + "=" * 60)
    print("EVALUATION ON HELD-OUT TEST SPLIT")
    print("=" * 60)
    test_results = trained_model.val(
        data=str(DATA_YAML),
        split="test",
        imgsz=IMGSZ,
        batch=batch_size,
        workers=WORKERS,
        device=device,
        project=str(RUNS_DIR),
        name="test_evaluation",
        plots=True,
        exist_ok=True,
    )
    
    def extract_metrics(res):
        box_p = float(res.box.mp) if hasattr(res, 'box') and hasattr(res.box, 'mp') else 0.0
        box_r = float(res.box.mr) if hasattr(res, 'box') and hasattr(res.box, 'mr') else 0.0
        box_map50 = float(res.box.map50) if hasattr(res, 'box') and hasattr(res.box, 'map50') else 0.0
        box_map = float(res.box.map) if hasattr(res, 'box') and hasattr(res.box, 'map') else 0.0
        box_f1 = (2 * box_p * box_r / (box_p + box_r)) if (box_p + box_r) > 0 else 0.0
        
        seg_p = float(res.seg.mp) if hasattr(res, 'seg') and hasattr(res.seg, 'mp') else 0.0
        seg_r = float(res.seg.mr) if hasattr(res, 'seg') and hasattr(res.seg, 'mr') else 0.0
        seg_map50 = float(res.seg.map50) if hasattr(res, 'seg') and hasattr(res.seg, 'map50') else 0.0
        seg_map = float(res.seg.map) if hasattr(res, 'seg') and hasattr(res.seg, 'map') else 0.0
        seg_f1 = (2 * seg_p * seg_r / (seg_p + seg_r)) if (seg_p + seg_r) > 0 else 0.0
        
        per_class = {}
        if hasattr(res, 'names') and hasattr(res, 'seg') and hasattr(res.seg, 'maps') and res.seg.maps is not None:
            for i, name in res.names.items():
                if i < len(res.seg.maps):
                    per_class[name] = {
                        "class_id": i,
                        "mask_mAP50-95": float(res.seg.maps[i]) if res.seg.maps[i] is not None else 0.0
                    }
        
        return {
            "box": {
                "precision": box_p,
                "recall": box_r,
                "map50": box_map50,
                "map50_95": box_map,
                "f1": box_f1,
            },
            "mask": {
                "precision": seg_p,
                "recall": seg_r,
                "map50": seg_map50,
                "map50_95": seg_map,
                "f1": seg_f1,
            },
            "per_class": per_class
        }
    
    val_metrics = extract_metrics(val_results)
    test_metrics = extract_metrics(test_results)
    
    summary = {
        "model": PRETRAINED_MODEL,
        "epochs_requested": EPOCHS,
        "batch_size": batch_size,
        "imgsz": IMGSZ,
        "device": str(device),
        "training_duration_seconds": training_duration,
        "best_checkpoint": str(best_weights),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
    }
    
    summary_path = RUNS_DIR / "training_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved full metrics summary to: {summary_path}")
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY REPORT")
    print("=" * 60)
    print(f"Validation Box  -> P: {val_metrics['box']['precision']:.4f}, R: {val_metrics['box']['recall']:.4f}, mAP50: {val_metrics['box']['map50']:.4f}, mAP50-95: {val_metrics['box']['map50_95']:.4f}, F1: {val_metrics['box']['f1']:.4f}")
    print(f"Validation Mask -> P: {val_metrics['mask']['precision']:.4f}, R: {val_metrics['mask']['recall']:.4f}, mAP50: {val_metrics['mask']['map50']:.4f}, mAP50-95: {val_metrics['mask']['map50_95']:.4f}, F1: {val_metrics['mask']['f1']:.4f}")
    print(f"Test Box        -> P: {test_metrics['box']['precision']:.4f}, R: {test_metrics['box']['recall']:.4f}, mAP50: {test_metrics['box']['map50']:.4f}, mAP50-95: {test_metrics['box']['map50_95']:.4f}, F1: {test_metrics['box']['f1']:.4f}")
    print(f"Test Mask       -> P: {test_metrics['mask']['precision']:.4f}, R: {test_metrics['mask']['recall']:.4f}, mAP50: {test_metrics['mask']['map50']:.4f}, mAP50-95: {test_metrics['mask']['map50_95']:.4f}, F1: {test_metrics['mask']['f1']:.4f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
