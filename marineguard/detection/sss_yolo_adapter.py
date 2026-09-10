"""
Role 5 SSS YOLOv8n Production Adapter & Pipeline Integration.
Executes authoritative YOLOv8n SSS model (Experiment #2 Augmented Training)
with real inference, Role 3 post-processing, bounding-box rendering, and
metadata preservation.
"""

import os
import hashlib
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

from marineguard.schemas import ClassifiedTarget, DebrisContact

AUTHORITATIVE_MODEL_PATH = "runs/marineguard_full_512_b16-2/weights/best.pt"
AUTHORITATIVE_MODEL_SHA256 = "18c9e560b9e82bb6efe3a108584497c4979a9e135bed578db179341e0778e0d1"

# Reference / historical single-class SSS sonar weights (preserved as reference artifact)
REFERENCE_ONECLASS_SSS_MODEL_PATH = "runs/detect/runs/detect/marineguard_sss_yolov8n_exp2_augmented/weights/best.pt"
REFERENCE_ONECLASS_SSS_SHA256 = "c9fd27940b9b1a28834002dcbc40d1306c3e56650309b536aecd9862236bd7d2"

# Global model cache to avoid re-instantiation per ping/frame
_CACHED_MODEL = None


def verify_model_integrity(model_path: str = AUTHORITATIVE_MODEL_PATH) -> Tuple[bool, str, str]:
    """Verifies that the model weights file exists and matches the authoritative SHA256."""
    if not os.path.exists(model_path):
        return False, "", f"Model file not found at: {model_path}"

    with open(model_path, "rb") as f:
        file_bytes = f.read()

    calc_sha = hashlib.sha256(file_bytes).hexdigest()
    if calc_sha.lower() == AUTHORITATIVE_MODEL_SHA256.lower():
        return True, calc_sha, "Authoritative SHA256 verified."
    else:
        # Check if it's an LFS pointer
        if len(file_bytes) < 300 and b"version https://git-lfs" in file_bytes:
            return False, calc_sha, "Model file is an unresolved Git LFS pointer. Run lfs smudge to resolve."
        return False, calc_sha, f"SHA256 mismatch (Expected {AUTHORITATIVE_MODEL_SHA256[:12]}..., Got {calc_sha[:12]}...)"


def load_authoritative_sss_model(model_path: str = AUTHORITATIVE_MODEL_PATH):
    """Loads and caches the authoritative 50-class YOLOv8n detector as the unified SSS MODEL."""
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL

    is_valid, sha, msg = verify_model_integrity(model_path)
    if not is_valid:
        raise RuntimeError(f"Cannot load SSS model: {msg}")

    import logging
    logger = logging.getLogger("marineguard.detection")
    from ultralytics import YOLO
    model = YOLO(model_path)
    _CACHED_MODEL = model

    logger.info(f"[SSS MODEL] model_path={model_path}")
    logger.info(f"[SSS MODEL] sha256={sha.upper()}")
    logger.info(f"[SSS MODEL] class_count={len(model.names)}")
    logger.info(f"[SSS MODEL] class_names={list(model.names.values())}")

    return _CACHED_MODEL


def preprocess_sss_image(image_input: Union[str, np.ndarray, Image.Image, bytes]) -> Tuple[np.ndarray, Tuple[int, int]]:
    """Loads and standardizes SSS image input into RGB numpy array (H, W, 3)."""
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"SSS image file not found: {image_input}")
        bgr = cv2.imread(image_input)
        if bgr is None:
            raise ValueError(f"Failed to decode image from path: {image_input}")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    elif isinstance(image_input, Image.Image):
        rgb = np.array(image_input.convert("RGB"))
    elif isinstance(image_input, bytes):
        nparr = np.frombuffer(image_input, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Failed to decode image from byte buffer.")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 2:
            # Grayscale waterfall -> 3-channel RGB
            rgb = cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
        elif image_input.ndim == 3:
            if image_input.shape[2] == 1:
                rgb = cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
            elif image_input.shape[2] == 3:
                rgb = image_input.copy()
            elif image_input.shape[2] == 4:
                rgb = cv2.cvtColor(image_input, cv2.COLOR_RGBA2RGB)
            else:
                raise ValueError(f"Unsupported channel count: {image_input.shape[2]}")
        else:
            raise ValueError(f"Unsupported image array dimensions: {image_input.ndim}")
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    height, width = rgb.shape[:2]
    return rgb, (height, width)


def predict_sss(
    image_input: Union[str, np.ndarray, Image.Image, bytes],
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    model=None,
) -> Dict[str, Any]:
    """Runs real YOLOv8n inference on SSS image and returns raw detections."""
    if model is None:
        model = load_authoritative_sss_model()

    rgb_image, (orig_h, orig_w) = preprocess_sss_image(image_input)

    # Execute real YOLO inference
    results = model.predict(
        source=rgb_image,
        conf=conf_threshold,
        iou=iou_threshold,
        verbose=False,
    )

    raw_detections = []
    r = results[0]
    boxes = r.boxes

    for i in range(len(boxes)):
        box = boxes[i]
        xyxy = box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
        conf = float(box.conf[0].cpu().numpy())
        cls_id = int(box.cls[0].cpu().numpy())
        raw_name = model.names.get(cls_id, f"class_{cls_id}")

        # Standardize species for MarineGuard schema
        if raw_name.lower() in ["net", "ghost_net", "net_plastic"]:
            species = "ghost_net"
        else:
            species = raw_name.lower().replace("-", "_")

        raw_detections.append({
            "detection_index": i,
            "class_id": cls_id,
            "raw_class": raw_name,
            "species": species,
            "confidence": round(conf, 4),
            "bbox": [round(coord, 2) for coord in xyxy],  # [x1, y1, x2, y2]
            "bbox_area": round((xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1]), 2),
        })

    return {
        "image_shape": (orig_h, orig_w, 3),
        "raw_detections": raw_detections,
        "speed_ms": r.speed,
    }


def filter_yolo_detections(
    raw_detections: List[Dict[str, Any]],
    confidence_threshold: float = 0.70,
    image_shape: Tuple[int, int, int] = (640, 640, 3),
    min_box_size: float = 4.0,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Applies Role 3 filtering constraints to raw YOLO detections."""
    accepted = []
    rejected = []
    img_h, img_w = image_shape[:2]

    for det in raw_detections:
        bbox = det["bbox"]
        x1, y1, x2, y2 = bbox
        conf = det["confidence"]
        reasons = []

        # Check confidence threshold
        if conf < confidence_threshold:
            reasons.append(f"LOW_CONFIDENCE: {conf:.2f} < threshold {confidence_threshold:.2f}")

        # Check geometry validity
        w = x2 - x1
        h = y2 - y1
        if w <= 0 or h <= 0:
            reasons.append("INVALID_BBOX: width or height <= 0")
        elif w * h == 0:
            reasons.append("ZERO_AREA_BBOX: area is 0")
        elif w < min_box_size or h < min_box_size:
            reasons.append(f"TINY_BBOX: width ({w:.1f}px) or height ({h:.1f}px) < {min_box_size}px")

        # Check image boundary bounds
        if x1 < -10 or y1 < -10 or x2 > img_w + 10 or y2 > img_h + 10:
            reasons.append("OUT_OF_BOUNDS: coordinates exceed image margins")

        det_copy = dict(det)
        if not reasons:
            det_copy["status"] = "ACCEPTED"
            det_copy["reason"] = f"Confidence {conf:.2f} >= threshold {confidence_threshold:.2f}"
            accepted.append(det_copy)
        else:
            det_copy["status"] = "FILTERED"
            det_copy["reason"] = "; ".join(reasons)
            rejected.append(det_copy)

    return accepted, rejected


def draw_sss_bounding_boxes(
    image_input: Union[str, np.ndarray, Image.Image, bytes],
    detections: List[Dict[str, Any]],
    output_path: Optional[str] = None,
) -> np.ndarray:
    """Draws real YOLO bounding boxes on SSS image with status and confidence annotations."""
    rgb_image, _ = preprocess_sss_image(image_input)
    annotated = rgb_image.copy()

    for det in detections:
        x1, y1, x2, y2 = [int(round(c)) for c in det["bbox"]]
        conf = det["confidence"]
        species = det.get("species", "target")
        status = det.get("status", "ACCEPTED")

        if status == "ACCEPTED":
            color = (16, 185, 129)  # Emerald Green
        else:
            color = (239, 68, 68)   # Coral Red

        # Draw main bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Label tag
        label = f"{species.upper()} {conf*100:.1f}% [{status}]"
        (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)

        # Draw tag background
        tag_y1 = max(0, y1 - text_h - 6)
        tag_y2 = y1
        cv2.rectangle(annotated, (x1, tag_y1), (x1 + text_w + 6, tag_y2), color, -1)
        cv2.putText(annotated, label, (x1 + 3, tag_y2 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        bgr_out = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, bgr_out)

    return annotated


def run_sss_pipeline(
    image_input: Union[str, np.ndarray, Image.Image, bytes],
    recorded_metadata: Optional[Dict[str, Any]] = None,
    confidence_threshold: float = 0.75,
    output_annotated_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Full end-to-end SSS YOLOv8n detection, Role 3 filtering, and schema integration pipeline."""
    pred = predict_sss(image_input, conf_threshold=min(0.20, confidence_threshold))
    raw_dets = pred["raw_detections"]
    img_shape = pred["image_shape"]

    accepted_dets, rejected_dets = filter_yolo_detections(
        raw_dets,
        confidence_threshold=confidence_threshold,
        image_shape=img_shape,
    )

    all_dets = accepted_dets + rejected_dets

    # Draw visual annotations
    annotated_img = draw_sss_bounding_boxes(image_input, all_dets, output_path=output_annotated_path)

    # Process recorded metadata (GPS strictly gated by presence)
    has_gps = False
    coords = None
    if recorded_metadata:
        if "lat_lon" in recorded_metadata and recorded_metadata["lat_lon"] is not None:
            lat, lon = recorded_metadata["lat_lon"]
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                has_gps = True
                coords = (lat, lon)
        elif "latitude" in recorded_metadata and "longitude" in recorded_metadata:
            lat = recorded_metadata["latitude"]
            lon = recorded_metadata["longitude"]
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                has_gps = True
                coords = (lat, lon)

    # Format ClassifiedTarget models for downstream compatibility
    classified_targets = []
    for idx, det in enumerate(accepted_dets):
        target_id = f"SSS_TARGET_{idx+1:02d}"
        box_w_m = round((det["bbox"][2] - det["bbox"][0]) * 0.05, 2)
        box_h_m = round((det["bbox"][3] - det["bbox"][1]) * 0.05, 2)
        geom = (max(0.1, box_w_m), max(0.1, box_h_m), 0.5)

        t = ClassifiedTarget(
            target_id=target_id,
            species=det["species"],
            confidence=det["confidence"],
            sensor_contributions={"side_scan_yolo": det["confidence"]},
            geometry_m=geom,
            lat_lon=coords if coords is not None else (13.0827, 80.2707) if has_gps else (0.0, 0.0),
            depth_m=float(recorded_metadata.get("depth_m", 24.3)) if recorded_metadata else 24.3,
            removal_priority="HIGH" if det["species"] == "ghost_net" else "MEDIUM",
            entanglement_risk="CRITICAL" if det["species"] == "ghost_net" else "LOW",
            evidence_id=f"EVIDENCE_{target_id}",
        )
        classified_targets.append(t)

    return {
        "status": "COMPLETED",
        "model_used": AUTHORITATIVE_MODEL_PATH,
        "model_sha256": AUTHORITATIVE_MODEL_SHA256,
        "image_shape": img_shape,
        "raw_detections_count": len(raw_dets),
        "accepted_count": len(accepted_dets),
        "filtered_count": len(rejected_dets),
        "confidence_threshold": confidence_threshold,
        "accepted_detections": accepted_dets,
        "rejected_detections": rejected_dets,
        "all_detections": all_dets,
        "classified_targets": [t.model_dump() for t in classified_targets],
        "annotated_image": annotated_img,
        "annotated_path": output_annotated_path,
        "has_gps_metadata": has_gps,
        "gps_coordinates": coords,
        "inference_speed_ms": pred["speed_ms"],
    }
