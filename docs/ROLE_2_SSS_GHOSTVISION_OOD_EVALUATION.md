# Role 2 — GhostVision real-SSS OOD / false-positive stress test

**This is an OOD/false-positive stress test, not a ground-truth ghost-net accuracy evaluation.**

**GhostVision contains real SSS imagery but does not provide ghost-net ground truth for this evaluation.**

No ghost-net precision, recall, F1, or mAP is reported. Crab-pot labels were not relabeled as `net`, were not mapped into the MarineGuard taxonomy, and were not used for training.

---

## 1. Objective

Measure how the synthetic ghost-net YOLOv8n baseline behaves on genuinely real side-scan-sonar imagery that it was not trained on.

The question is whether the detector produces high-confidence `net` predictions on visually different real SSS tiles (Delaware Bay / Inland Bays crab-pot imagery), not whether it can find ghost nets in GhostVision.

## 2. Model used

- Architecture: YOLOv8n detection
- Initialization (training, not this eval): `yolov8n.pt`
- Task verified at load: `detect`
- Class count verified at load: 1
- Class 0 verified at load: `net`
- Local class `net` corresponds to MarineGuard global class ID 29
- Official MarineGuard 50-class taxonomy was not changed

## 3. Model checkpoint

`runs/detect/runs/marineguard_sss_yolov8n_baseline/weights/best.pt`

The checkpoint was loaded read-only. `last.pt` was not used. No training, fine-tuning, or weight overwrite was performed.

## 4. Dataset used

External path (read-only): `C:\MarineGuard-SSS\GhostVision`

Inspection (`runs/evaluation/ghostvision_ood/ghostvision_inspection.json`):

| Split | JPEG images | JSONL rows | Crab-Pot boxes | Images with ≥1 crab-pot box |
| --- | ---: | ---: | ---: | ---: |
| train | 5721 | 5721 | 7469 | 4291 |
| valid | 555 | 555 | 1275 | 502 |
| test | 398 | 398 | 567 | 334 |
| **Total** | **6674** | **6674** | **9311** | **5127** |

- Image format: JPEG only
- Resolution: 640×640 for all 6674 images
- Annotation format: Hugging Face JSONL (`metadata.jsonl`) with pixel `xywh` boxes and string categories
- Categories present on disk: `Crab-Pot` only (9311 boxes). The dataset README also describes `Maybe-Crab-Pot`; that class did not appear in this local copy
- Duplicate content hashes: 0 groups
- Unopenable / corrupt images: 0
- Existing splits: train / valid / test (GhostVision’s own splits). All three were used for OOD inference because none of them were used to train the MarineGuard SSS baseline
- 1547 images have empty annotation lists (no crab-pot box)

## 5. Dataset provenance

GhostVision / PINGEcosystem `sss-crab-pot-detection-ds`: manually annotated consumer-grade Humminbird side-scan imagery of derelict crab pots from Delaware Inland Bays and Delaware Bay.

Source README (local): `C:\MarineGuard-SSS\GhostVision\README.md`

Publication cited by that README: Bodine et al. (2026), *GhostVision: Democratizing Derelict Gear Detection Using Low-Cost Sonar and Artificial Intelligence*, Journal of Marine Science and Engineering, 14(10), 951.

GhostVision source files were not modified.

## 6. Why this is an OOD test

The baseline was trained only on the controlled MarineGuard SSS development set (`data/processed/marineguard_sss`): synthetic ghost-net positives plus real SubPipeMini2 background / hard-negative tiles. GhostVision is a different sonar system, geography, target type (crab pots, not nets), and visual domain. It was never used for training or model selection.

## 7. Exact inference configuration

| Item | Value |
| --- | --- |
| Python | `.\.venv\Scripts\python.exe` (3.14.5) |
| PyTorch | 2.14.0+cu126 |
| Ultralytics | 8.4.143 |
| Device | CUDA device 0 (`NVIDIA GeForce RTX 3050`) |
| `conf` | 0.25 |
| `imgsz` | 640 |
| `batch` | 8 (chunked to 64 paths per call to avoid GPU OOM) |
| Training | not performed |
| Source images | not altered |

One valid-split image was predicted before the timed loop (warmup). Reported latency excludes that warmup.

## 8. Number of images evaluated

**6674** (all local GhostVision JPEGs: 5721 train + 555 valid + 398 test).

## 9. Detection statistics

Predicted `net` detections on a real SSS OOD dataset **without ghost-net ground truth**. These are **not** conventional false positives in a precision/recall sense.

| Quantity | Value |
| --- | ---: |
| Images evaluated | 6674 |
| Images with ≥1 predicted `net` | 36 (0.539%) |
| Images with zero predicted `net` | 6638 (99.461%) |
| Total predicted `net` boxes | 40 |
| Mean detections per image | 0.005993 |

By GhostVision split (still OOD for this model):

| Split | Images | With predicted `net` | Zero predicted `net` | Predicted `net` boxes |
| --- | ---: | ---: | ---: | ---: |
| train | 5721 | 30 | 5691 | 32 |
| valid | 555 | 0 | 555 | 0 |
| test | 398 | 6 | 392 | 8 |

## 10. Confidence statistics

Among the **40** predicted `net` boxes with `conf ≥ 0.25`:

| Statistic | Confidence |
| --- | ---: |
| Minimum | 0.252033 |
| Mean | 0.404667 |
| Median | 0.331985 |
| Maximum | 0.880790 |
| 25th percentile | 0.284492 |
| 75th percentile | 0.480809 |
| 90th percentile | 0.625500 |

Count by confidence bin:

| Bin | Count |
| --- | ---: |
| 0.25–0.40 | 26 |
| 0.40–0.60 | 9 |
| 0.60–0.80 | 3 |
| 0.80–1.00 | 2 |

Most predicted boxes sit just above the 0.25 threshold. Only two exceed 0.80.

## 11. Latency

Timed evaluation (after one warmup image):

- Total: 66.801 s
- Mean: 10.009 ms / image on `cuda:0`

This is batch-8 Ultralytics predict latency on this GPU, not a production MCP/API benchmark.

## 12. Representative examples

Saved under `runs/evaluation/ghostvision_ood/examples/` (copies only; GhostVision originals unchanged).

Red boxes: predicted `net`. Cyan boxes (when drawn): GhostVision crab-pot annotations for qualitative comparison only.

| Set | n | Directory |
| --- | ---: | --- |
| Highest max-confidence images | 10 | `examples/highest_confidence/` |
| Medium-confidence images (closest to median max-conf among remaining detection images) | 10 | `examples/medium_confidence/` |
| Zero-detection images (seed 42 sample) | 10 | `examples/zero_detections/` |

All 36 images with predicted `net` also have annotated copies in `runs/evaluation/ghostvision_ood/annotated/`.

Highest-confidence image list (from `ghostvision_ood_report.json`):

1. `test/Rec09_Sensor_Depth_wcp_ss_star_00021_png_jpg.rf.2866aa91a79454f1549e3c0bfbe8df7e.jpg`
2. `test/Rec09_Sensor_Depth_wcp_ss_port_00004_jpg.rf.aaaab34b32a88e481efe9f72cf05ac93.jpg`
3. `test/Rec9_wcp_ss_port_00037_png_jpg.rf.3ade22e50cf8b125edaa5c1bca8d6120.jpg`
4. `train/Rec16_wcp_ss_star_00022_png_jpg.rf.b3edd53d06221a3b1d2742d1b65ca08c.jpg`
5. `test/Rec09_Sensor_Depth_wcp_ss_star_00028_png_jpg.rf.64d1ea763ba782aa94a3eec7d1e60685.jpg`

## 13. Qualitative comparison to crab-pot boxes (not ghost-net accuracy)

Heuristic only (not a metric of ghost-net performance):

- Overlap: IoU ≥ 0.30 with a `Crab-Pot` box
- Near: IoU < 0.30 and center distance ≤ 50 px
- Elsewhere: image has crab-pot boxes, but the predicted `net` is neither overlapping nor near
- No crab-pot annotation: image JSONL has zero boxes

Of 40 predicted `net` boxes:

| Relation to crab-pot annotation | Count |
| --- | ---: |
| Overlaps crab-pot (IoU ≥ 0.30) | 0 |
| Near crab-pot (≤ 50 px) | 3 |
| Elsewhere on an image that has crab-pot boxes | 34 |
| On an image with no crab-pot annotation | 3 |

The detector did not systematically place `net` boxes on crab-pot annotations. Most predicted `net` boxes landed elsewhere in the tile. This still does **not** prove crab-pot invariance as a formal metric, and it does **not** give ghost-net precision.

## 14. Limitations

- GhostVision has **no ghost-net labels**. Zero detections cannot be called true negatives for nets.
- Predicted `net` boxes cannot be called conventional false positives without knowing whether a net is actually present.
- High controlled-set validation scores (synthetic ghost nets) do not transfer to this test.
- Imagery is region- and sensor-specific (Delaware, Humminbird SSS).
- Confidence threshold 0.25 is a default operating point, not a calibrated real-SSS threshold.
- Latency includes image decode and Ultralytics overhead; it is not an ONNX/MCP production number.
- Crab-pot overlap uses arbitrary IoU / distance cutoffs.

## 15. Interpretation

On 6674 real SSS tiles the baseline produced 40 `net` predictions on 36 images (0.539% of images). Most of those 40 scores are low-to-mid (median 0.332); a small number reach high confidence (max 0.881).

This is evidence about **domain-shift firing rate** of a synthetic-net detector on real crab-pot SSS, not real-world ghost-net detection accuracy.

No next training run is started from this result. Possible later choices (stronger augmentation, more realistic synthesis, extra real SSS, domain adaptation, hard-negative mining, or another approach) remain a separate decision.

## 16. Integrity

- DRISHTI, GhostVision, and the existing MarineGuard 50-class dataset were not modified
- Production `fusion.py`, `side_scan.py`, `optical.py`, `bathymetry.py`, MCP code, and Role 2 inference modules were not modified
- Baseline `best.pt` / `last.pt` were not overwritten
- MarineGuard SSS test split remains unused for training and model selection
- Official taxonomy was not changed
- Outputs: `runs/evaluation/ghostvision_ood/` (new evaluation directory)

Machine-readable report: `runs/evaluation/ghostvision_ood/ghostvision_ood_report.json`
