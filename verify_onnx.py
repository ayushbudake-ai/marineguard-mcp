# Role 2: YOLOv8n-seg ONNX Verification Tool
import json
from pathlib import Path
import numpy as np
import torch
import onnx
import onnxruntime as ort
from ultralytics import YOLO

def verify():
    repo_root = Path(__file__).resolve().parent
    best_pt = repo_root / 'runs' / 'seaclear_yolov8n_seg' / 'train' / 'weights' / 'best.pt'
    onnx_path = repo_root / 'runs' / 'seaclear_yolov8n_seg' / 'onnx' / 'best.onnx'
    val_img_dir = repo_root / 'data' / 'processed' / 'seaclear_segmentation' / 'images' / 'val'

    assert best_pt.exists(), f'Missing {best_pt}'
    assert onnx_path.exists(), f'Missing {onnx_path}'

    onnx_model = onnx.load(str(onnx_path))
    onnx.checker.check_model(onnx_model)
    session = ort.InferenceSession(str(onnx_path), providers=['CPUExecutionProvider'])

    pt_model = YOLO(str(best_pt))
    onnx_runner = YOLO(str(onnx_path), task='segment')

    samples = [val_img_dir / '1009.jpg', val_img_dir / '1017.jpg', val_img_dir / '1019.jpg', val_img_dir / '1037.jpg', val_img_dir / '1043.jpg']

    print('=== PYTORCH VS ONNX VERIFICATION ===')
    for idx, img_p in enumerate(samples):
        pt_res = pt_model(str(img_p), imgsz=512, rect=False, conf=0.25, verbose=False)[0]
        onnx_res = onnx_runner(str(img_p), imgsz=512, conf=0.25, verbose=False)[0]

        pt_count = len(pt_res.boxes)
        onnx_count = len(onnx_res.boxes)

        pt_cls = [int(c) for c in pt_res.boxes.cls.cpu().numpy()] if pt_count > 0 else []
        onnx_cls = [int(c) for c in onnx_res.boxes.cls.cpu().numpy()] if onnx_count > 0 else []

        pt_conf = [float(c) for c in pt_res.boxes.conf.cpu().numpy()] if pt_count > 0 else []
        onnx_conf = [float(c) for c in onnx_res.boxes.conf.cpu().numpy()] if onnx_count > 0 else []

        max_conf_d = float(np.max(np.abs(np.array(pt_conf) - np.array(onnx_conf)))) if pt_count == onnx_count and pt_count > 0 else 0.0

        print(f'Sample {idx+1} ({img_p.name}): Detections={pt_count}/{onnx_count} | Classes Match={pt_cls == onnx_cls} | Max Conf Diff={max_conf_d:.6e}')

if __name__ == '__main__':
    verify()
