# Role 1 → Role 2 Handoff

## Model
YOLOv8n object detector

## Trained checkpoint
`runs/marineguard_full_512_b16-2/weights/best.pt`

## Dataset
18,073 images
50 unified classes
46,209 validated bounding boxes
Train: 12,652
Val: 3,613
Test: 1,808

## Held-out test results
Precision: 89.70%
Recall: 71.90%
Calculated F1: 79.94%
mAP50: 80.69%
mAP50-95: 55.74%

## Role 2 next work
- ONNX export
- real detector integration
- real per-detection confidence outputs
- fusion retuning
- downstream integrated evaluation

## Important
This checkpoint is an object detector, not a segmentation model.
