
"""
MarineGuard MCP — Production FastAPI Backend Bridge.
Connects the React web frontend directly to the real SSS YOLOv8n pipeline,
Role 3 post-processing, and Role 4 report exporters.
"""

import os
import time
import json
import logging
import shutil
from typing import Dict, Any, List, Optional
import cv2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from marineguard.mcp_server import MarineGuardMCPServer
from marineguard.schemas import ClassifiedTarget
from marineguard.detection.sss_yolo_adapter import (
    AUTHORITATIVE_MODEL_PATH,
    AUTHORITATIVE_MODEL_SHA256,
    verify_model_integrity,
    load_authoritative_sss_model,
    run_sss_pipeline,
)

# Setup detailed development logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("marineguard.api")

# ------------------------------------------------------------------------------
# 1. FastAPI Application Setup & CORS
# ------------------------------------------------------------------------------
app = FastAPI(
    title="MarineGuard MCP API Bridge",
    description="Real SSS YOLOv8n AI Detection & Post-Mission Analysis API",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required storage directories exist
os.makedirs("data/demo_sss", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/evidence", exist_ok=True)
os.makedirs("data/reports", exist_ok=True)

# Mount static file directory for serving images and reports
app.mount("/static/data", StaticFiles(directory="data"), name="static_data")

# Global singleton server instance
mcp_server = MarineGuardMCPServer()

# Pre-load YOLO model at server startup
_is_model_ok, _model_sha, _model_msg = verify_model_integrity()
if _is_model_ok:
    load_authoritative_sss_model()
    logger.info(f"Authoritative YOLOv8n SSS model loaded and verified: {AUTHORITATIVE_MODEL_PATH}")
else:
    logger.warning(f"Authoritative model warning: {_model_msg}")

# Cached runtime state of the latest detection run
LATEST_DETECTION_STATE: Dict[str, Any] = {
    "has_run": False,
    "sample_name": "",
    "result": None,
    "classified_targets": [],
}


# ------------------------------------------------------------------------------
# 2. Helper Functions & Image Validation
# ------------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def validate_sss_image(file_path: str) -> Tuple[np.ndarray, int, int]:
    """Validates that the file exists, is readable, and decodes into a valid SSS image.
    
    Raises HTTPException(404) if missing.
    Raises HTTPException(400) if decoding fails or dimensions are invalid.
    """
    if not os.path.exists(file_path):
        logger.error(f"[VALIDATION] File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"SSS image file not found: {os.path.basename(file_path)}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        logger.error(f"[VALIDATION] Unsupported extension: {ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. SSS images must be PNG, JPG, JPEG, BMP, or TIFF.",
        )

    img = cv2.imread(file_path)
    if img is None or img.size == 0:
        logger.error(f"[VALIDATION] Failed to decode image: {file_path}")
        raise HTTPException(status_code=400, detail="SSS image could not be decoded.")

    h, w = img.shape[:2]
    if h <= 0 or w <= 0:
        logger.error(f"[VALIDATION] Invalid dimensions: {w}x{h}")
        raise HTTPException(status_code=400, detail="Invalid image dimensions.")

    return img, w, h


def load_demo_manifest() -> List[Dict[str, Any]]:
    """Dynamically loads demo samples from data/demo_sss/demo_samples.json in their
    exact authoritatively specified order (positive contacts first, then negative control),
    discovers any additional images in data/demo_sss/, and includes the verified
    authoritative sample from data/processed/marineguard_sss/images/test/synth_ghost_net_00001.png.
    """
    manifest_path = "data/demo_sss/demo_samples.json"
    manifest_entries: Dict[str, Dict[str, Any]] = {}
    manifest_order: List[Dict[str, Any]] = []

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_order = json.load(f)
                for entry in manifest_order:
                    manifest_entries[entry.get("file", "")] = entry
                    manifest_entries[entry.get("id", "")] = entry
        except Exception as e:
            logger.error(f"Error reading demo_samples.json: {e}")

    samples: List[Dict[str, Any]] = []
    seen_files = set()
    demo_dir = "data/demo_sss"

    # 1. Process files in manifest order first (ghost_net_contact_01, ghost_net_contact_02, background_seabed)
    for meta in manifest_order:
        fname = meta.get("file", "")
        fpath = os.path.join(demo_dir, fname)
        if os.path.exists(fpath):
            seen_files.add(fname)
            sample_id = meta.get("id", os.path.splitext(fname)[0])
            sample_name = meta.get("name", fname.replace("_", " ").replace("-", " ").title())
            desc = meta.get("description", "Recorded/repository-controlled SSS demonstration sample.")
            gps = meta.get("gps")
            has_gps = gps is not None and isinstance(gps, (list, tuple)) and len(gps) == 2

            samples.append({
                "id": sample_id,
                "name": sample_name,
                "description": desc,
                "file": fname,
                "path": fpath,
                "sensor": meta.get("sensor", "Side-Scan Sonar"),
                "gps": gps if has_gps else None,
                "has_gps": has_gps,
                "lat_lon": gps if has_gps else None,
                "depth_m": meta.get("depth_m", 24.0),
                "imageUrl": f"/static/data/demo_sss/{fname}",
            })

    # 2. Add any other image files in data/demo_sss/ not listed in manifest
    if os.path.exists(demo_dir):
        for fname in sorted(os.listdir(demo_dir)):
            if fname not in seen_files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    fpath = os.path.join(demo_dir, fname)
                    seen_files.add(fname)
                    sample_id = os.path.splitext(fname)[0]
                    sample_name = fname.replace("_", " ").replace("-", " ").title()
                    samples.append({
                        "id": sample_id,
                        "name": sample_name,
                        "description": "Recorded/repository-controlled SSS demonstration sample.",
                        "file": fname,
                        "path": fpath,
                        "sensor": "Side-Scan Sonar",
                        "gps": None,
                        "has_gps": False,
                        "lat_lon": None,
                        "depth_m": 24.0,
                        "imageUrl": f"/static/data/demo_sss/{fname}",
                    })

    # 3. Include the verified existing sample: synth_ghost_net_00001.png
    synth_path = "data/processed/marineguard_sss/images/test/synth_ghost_net_00001.png"
    if os.path.exists(synth_path):
        samples.append({
            "id": "synth_ghost_net_00001",
            "name": "Verified Benchmark Ghost Net #1",
            "description": "Authoritative reserved test split sample with verified single ghost net contact.",
            "file": "synth_ghost_net_00001.png",
            "path": synth_path,
            "sensor": "Side-Scan Sonar",
            "gps": [13.0835, 80.2715],
            "has_gps": True,
            "lat_lon": [13.0835, 80.2715],
            "depth_m": 24.3,
            "imageUrl": "/static/data/processed/marineguard_sss/images/test/synth_ghost_net_00001.png",
        })

    return samples


def execute_inference_pipeline(
    image_path: str,
    confidence_threshold: float = 0.75,
    sample_name: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    file_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core execution function running real YOLOv8n inference on verified image pixels,
    applying Role 3 filtering, and formatting the detection result.
    """
    # 1. Validate image
    _, img_w, img_h = validate_sss_image(image_path)

    # 2. Execute real YOLO pipeline
    annotated_filename = f"annotated_{int(time.time()*1000)}.png"
    out_annotated_path = os.path.join("data/evidence", annotated_filename)

    t0 = time.perf_counter()
    pipeline_res = run_sss_pipeline(
        image_input=image_path,
        recorded_metadata=metadata,
        confidence_threshold=confidence_threshold,
        output_annotated_path=out_annotated_path,
    )
    t_elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    # 3. Mandatory Development Logging (Requirement 6)
    logger.info(f"[INFERENCE] actual image path: {image_path}")
    logger.info(f"[INFERENCE] width: {img_w}")
    logger.info(f"[INFERENCE] height: {img_h}")
    logger.info(f"[INFERENCE] model path: {AUTHORITATIVE_MODEL_PATH}")
    logger.info(f"[INFERENCE] raw detection count: {pipeline_res['raw_detections_count']}")
    logger.info(f"[INFERENCE] processing time: {t_elapsed_ms} ms")

    # 4. Format detections for React UI
    has_gps = pipeline_res["has_gps_metadata"]
    coords = pipeline_res["gps_coordinates"]
    gps_message = (
        f"Recorded ({coords[0]:.4f}, {coords[1]:.4f})"
        if has_gps and coords
        else "Geolocation unavailable — no recorded coordinates supplied with this SSS data."
    )

    react_detections = []
    for idx, d in enumerate(pipeline_res["all_detections"]):
        x1, y1, x2, y2 = d["bbox"]
        is_accepted = d["status"] == "ACCEPTED"
        conf = d["confidence"]

        det_obj = {
            "id": f"DET-{idx+1:03d}",
            "objectClass": d["species"].replace("_", " ").title(),
            "species": d["species"],
            "rawClass": d["raw_class"],
            "confidence": conf,
            "confidencePct": f"{conf*100:.1f}%",
            "status": "accepted" if is_accepted else "filtered",
            "rejectionReason": d["reason"],
            "bbox": [x1, y1, x2, y2],
            "bboxCoords": f"[{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]",
            "bboxArea": d["bbox_area"],
            "lat": coords[0] if has_gps and coords else None,
            "lng": coords[1] if has_gps and coords else None,
            "location": {
                "latitude": coords[0] if has_gps and coords else None,
                "longitude": coords[1] if has_gps and coords else None,
            } if has_gps and coords else None,
            "depthM": metadata.get("depth_m", 24.3) if metadata else 24.3,
            "priority": "HIGH" if d["species"] == "ghost_net" else "MEDIUM" if any(k in d["species"] for k in ["bottle", "can", "tire", "plastic", "container", "wreckage", "cable"]) else "LOW",
            "risk": "CRITICAL" if d["species"] == "ghost_net" else "ELEVATED" if any(k in d["species"] for k in ["bottle", "can", "tire", "plastic", "container", "wreckage", "cable"]) else "MONITORED",
        }
        react_detections.append(det_obj)

    # Calculate average raw neural confidence across all raw detections
    raw_avg_conf = (
        sum(d["confidence"] for d in pipeline_res["all_detections"]) / len(pipeline_res["all_detections"])
        if pipeline_res["all_detections"] else 0.0
    )

    # Construct public static URL for the original image
    rel_orig_path = image_path.replace("\\", "/")
    if rel_orig_path.startswith("data/"):
        orig_url = f"/static/{rel_orig_path}"
    else:
        orig_url = f"/static/data/{os.path.basename(image_path)}"

    display_name = sample_name or os.path.basename(image_path)
    eff_file_id = file_id or os.path.basename(image_path)

    raw_speed = pipeline_res.get("inference_speed_ms")
    if isinstance(raw_speed, dict):
        inference_speed_ms = round(float(raw_speed.get("inference", 0.0)), 2)
    elif isinstance(raw_speed, (int, float)):
        inference_speed_ms = round(float(raw_speed), 2)
    else:
        inference_speed_ms = t_elapsed_ms

    response_data = {
        "fileId": eff_file_id,
        "sampleName": display_name,
        "confidenceThreshold": confidence_threshold,
        "totalDetections": pipeline_res["raw_detections_count"],
        "acceptedCount": pipeline_res["accepted_count"],
        "filteredCount": pipeline_res["filtered_count"],
        "averageConfidence": round(raw_avg_conf, 3),
        "rawAverageConfidence": round(raw_avg_conf, 3),
        "processingTimeMs": t_elapsed_ms,
        "inferenceSpeedMs": inference_speed_ms,
        "imageShape": pipeline_res["image_shape"],
        "annotatedImageUrl": f"/static/data/evidence/{annotated_filename}",
        "originalImageUrl": orig_url,
        "hasGps": has_gps,
        "gpsCoordinates": coords,
        "gpsMessage": gps_message,
        "detections": react_detections,
        "modelUsed": pipeline_res["model_used"],
        "modelSha256": pipeline_res["model_sha256"],
    }

    # Update global latest state for downstream reporting
    LATEST_DETECTION_STATE["has_run"] = True
    LATEST_DETECTION_STATE["sample_name"] = display_name
    LATEST_DETECTION_STATE["result"] = response_data
    LATEST_DETECTION_STATE["classified_targets"] = pipeline_res["classified_targets"]

    return response_data


# ------------------------------------------------------------------------------
# 3. Pydantic Request Models
# ------------------------------------------------------------------------------
class DetectRequest(BaseModel):
    fileId: Optional[str] = None
    sampleKey: Optional[str] = None
    confidenceThreshold: float = 0.75


class ReportRequest(BaseModel):
    format: str = "PDF"


# ------------------------------------------------------------------------------
# 4. Core API Endpoints
# ------------------------------------------------------------------------------
@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Health check endpoint reporting real backend & model state."""
    is_ok, sha, msg = verify_model_integrity()
    return {
        "status": "ok" if is_ok else "error",
        "service": "MarineGuard MCP",
        "sss_model": "loaded" if is_ok else "unavailable",
        "user_facing_model": "SSS MODEL",
        "model_subtitle": "Unified Side-Scan Sonar Detection Engine",
        "model_name": "SSS MODEL",
        "checkpoint_name": "marineguard_full_512_b16-2",
        "model_path": AUTHORITATIVE_MODEL_PATH,
        "model_sha256": sha,
        "class_count": 50,
        "message": msg,
        "roles": {
            "role1_compiler": "available",
            "role2_yolo_detector": "available" if is_ok else "missing_weights",
            "role3_firewall_filter": "available",
            "role4_exporters": "available",
            "role5_react_api": "active",
        },
    }


@app.get("/api/demo-samples")
@app.get("/api/samples")
def get_demo_samples() -> Dict[str, Any]:
    """Dynamically returns repository-controlled SSS demo images from data/demo_sss/."""
    samples = load_demo_manifest()
    return {
        "status": "ok",
        "count": len(samples),
        "samples": samples,
    }


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    confidenceThreshold: Optional[float] = Form(0.75),
) -> Dict[str, Any]:
    """Receives, validates, stores an uploaded SSS image, and immediately runs
    real YOLOv8n inference with Role 3 post-processing.
    """
    safe_name = os.path.basename(file.filename or "upload.png")
    ext = os.path.splitext(safe_name)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        logger.error(f"[UPLOAD] Unsupported format '{ext}' for file '{safe_name}'")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. SSS images must be PNG, JPG, JPEG, BMP, or TIFF.",
        )

    file_bytes = await file.read()
    if not file_bytes or len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    unique_file_id = f"upload_{int(time.time()*1000)}_{safe_name}"
    file_path = os.path.join("data/uploads", unique_file_id)

    # Validate image bytes before saving
    import numpy as np
    nparr = np.frombuffer(file_bytes, np.uint8)
    decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if decoded_img is None or decoded_img.size == 0:
        logger.error(f"[UPLOAD] Failed to decode image bytes for {safe_name}")
        raise HTTPException(status_code=400, detail="SSS image could not be decoded.")

    # Save to disk
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Mandatory Development Logging (Requirement 6)
    logger.info(f"[UPLOAD] filename: {safe_name}")
    logger.info(f"[UPLOAD] content type: {file.content_type}")
    logger.info(f"[UPLOAD] byte size: {len(file_bytes)}")
    logger.info(f"[UPLOAD] temporary/stored path: {file_path}")

    # Immediately execute real YOLOv8n inference pipeline (Requirement 5)
    conf_thresh = confidenceThreshold if confidenceThreshold is not None else 0.75
    detection_res = execute_inference_pipeline(
        image_path=file_path,
        confidence_threshold=conf_thresh,
        sample_name=safe_name,
        metadata={"lat_lon": None, "depth_m": 24.0},
        file_id=unique_file_id,
    )

    # Attach upload-specific metadata
    detection_res["filename"] = safe_name
    detection_res["sizeBytes"] = len(file_bytes)
    detection_res["path"] = file_path
    detection_res["imageUrl"] = f"/static/data/uploads/{unique_file_id}"

    return detection_res


@app.post("/api/detect")
async def run_detection(req: DetectRequest) -> Dict[str, Any]:
    """Executes real YOLOv8n inference on SSS image, applies Role 3 filtering, and returns results.
    Never caches results across different invocations.
    """
    image_path = None
    metadata = None
    sample_display_name = ""

    demo_samples = load_demo_manifest()

    # 1. Resolve image from fileId (e.g. manual upload)
    if req.fileId:
        clean_file_id = os.path.basename(req.fileId)
        potential_upload = os.path.join("data/uploads", clean_file_id)
        if os.path.exists(potential_upload):
            image_path = potential_upload
            metadata = {"lat_lon": None, "depth_m": 24.0}
            sample_display_name = clean_file_id
        else:
            # Check if fileId matches any demo sample
            for s in demo_samples:
                if s["id"] == req.fileId or s["file"] == req.fileId or s["name"] == req.fileId:
                    image_path = s["path"]
                    metadata = {"lat_lon": s["lat_lon"], "depth_m": s["depth_m"]}
                    sample_display_name = s["name"]
                    break

    # 2. Resolve image from sampleKey (e.g. demo sample selector)
    if not image_path and req.sampleKey:
        # Match sampleKey directly or aliases
        for s in demo_samples:
            if (
                s["id"] == req.sampleKey
                or s["file"] == req.sampleKey
                or s["name"] == req.sampleKey
                or (req.sampleKey == "sample_01" and "01" in s["id"])
                or (req.sampleKey == "sample_02" and "02" in s["id"])
                or (req.sampleKey == "sample_bg" and "background" in s["id"])
            ):
                image_path = s["path"]
                metadata = {"lat_lon": s["lat_lon"], "depth_m": s["depth_m"]}
                sample_display_name = s["name"]
                break

    # 3. If still not resolved and neither was passed, default to first demo sample
    if not image_path and not req.fileId and not req.sampleKey and demo_samples:
        s = demo_samples[0]
        image_path = s["path"]
        metadata = {"lat_lon": s["lat_lon"], "depth_m": s["depth_m"]}
        sample_display_name = s["name"]

    if not image_path or not os.path.exists(image_path):
        key_desc = req.fileId or req.sampleKey or "unknown"
        logger.error(f"[INFERENCE] SSS image file not found on server for '{key_desc}'")
        raise HTTPException(status_code=404, detail=f"SSS image file '{key_desc}' not found on server.")

    # 4. Execute Real Pipeline
    return execute_inference_pipeline(
        image_path=image_path,
        confidence_threshold=req.confidenceThreshold,
        sample_name=sample_display_name,
        metadata=metadata,
        file_id=req.fileId or os.path.basename(image_path),
    )


@app.get("/api/detections/current")
def get_current_detections() -> Dict[str, Any]:
    """Returns the most recent detection result."""
    if not LATEST_DETECTION_STATE["has_run"] or not LATEST_DETECTION_STATE["result"]:
        # Auto-run demo #1 if no detection has run yet
        req = DetectRequest(sampleKey="ghost_net_contact_01", confidenceThreshold=0.75)
        import asyncio
        return asyncio.run(run_detection(req))
    return LATEST_DETECTION_STATE["result"]


@app.get("/api/detections/{detection_id}")
def get_detection_by_id(detection_id: str) -> Dict[str, Any]:
    """Returns specific detection details."""
    current = get_current_detections()
    for d in current.get("detections", []):
        if d["id"] == detection_id:
            return d
    raise HTTPException(status_code=404, detail=f"Detection {detection_id} not found")


@app.get("/api/metrics")
def get_metrics() -> Dict[str, Any]:
    """Returns model development validation benchmarks + live runtime stats."""
    latest = LATEST_DETECTION_STATE.get("result") or {}
    return {
        "modelName": "SSS MODEL",
        "productName": "SSS MODEL",
        "subtitle": "Unified Side-Scan Sonar Detection Engine",
        "architecture": "YOLOv8n Object Detection",
        "validationDataset": "MarineGuard SSS Reserved Val Split (190 images)",
        "metricsTitle": "SSS MODEL Exp #2 Validation Benchmarks",
        "precision": 0.9987,
        "recall": 1.0000,
        "f1Score": 0.9993,
        "map50": 0.9950,
        "map50_95": 0.9374,
        "precisionPct": "99.87%",
        "recallPct": "100.0%",
        "f1ScorePct": "99.93%",
        "bestEpoch": 66,
        "totalEpochs": 75,
        "batchSize": 16,
        "imgsz": 640,
        "currentAnalysis": {
            "hasRun": LATEST_DETECTION_STATE.get("has_run", False),
            "sampleName": LATEST_DETECTION_STATE.get("sample_name", ""),
            "totalDetections": latest.get("totalDetections", 0),
            "acceptedCount": latest.get("acceptedCount", 0),
            "filteredCount": latest.get("filteredCount", 0),
            "averageConfidence": latest.get("averageConfidence", 0.0),
            "processingTimeMs": latest.get("processingTimeMs"),
            "inferenceSpeedMs": latest.get("inferenceSpeedMs"),
        },
        "classes": [
            {
                "name": "Ghost Net",
                "classId": 0,
                "status": "READY",
                "precision": 0.9987,
                "recall": 1.0000,
                "ap50": 0.9950,
                "ap50_95": 0.9374,
                "validationImages": 190,
                "note": "Authoritative SSS YOLOv8n weights verified",
            },
            {
                "name": "Bottle",
                "classId": None,
                "status": "NOT SUPPORTED BY CURRENT SSS DATA",
                "precision": None,
                "recall": None,
                "ap50": None,
                "ap50_95": None,
                "validationImages": 0,
                "note": "Zero genuine SSS training samples exist in repository (present in optical/FLS sets only)",
            },
            {
                "name": "Can",
                "classId": None,
                "status": "NOT SUPPORTED BY CURRENT SSS DATA",
                "precision": None,
                "recall": None,
                "ap50": None,
                "ap50_95": None,
                "validationImages": 0,
                "note": "Zero genuine SSS training samples exist in repository (present in optical/FLS sets only)",
            },
            {
                "name": "Plastic",
                "classId": None,
                "status": "NOT SUPPORTED BY CURRENT SSS DATA",
                "precision": None,
                "recall": None,
                "ap50": None,
                "ap50_95": None,
                "validationImages": 0,
                "note": "Zero genuine SSS training samples exist in repository (present in optical/FLS sets only)",
            },
            {
                "name": "Tire",
                "classId": None,
                "status": "NOT SUPPORTED BY CURRENT SSS DATA",
                "precision": None,
                "recall": None,
                "ap50": None,
                "ap50_95": None,
                "validationImages": 0,
                "note": "Zero genuine SSS training samples exist in repository (present in optical/FLS sets only)",
            },
            {
                "name": "Other Debris",
                "classId": None,
                "status": "NOT SUPPORTED BY CURRENT SSS DATA",
                "precision": None,
                "recall": None,
                "ap50": None,
                "ap50_95": None,
                "validationImages": 0,
                "note": "Zero genuine SSS training samples exist in repository (present in optical/FLS sets only)",
            },
        ],
        "note": "Standalone development validation on reserved 190-image SSS validation split. Not to be misrepresented as live sea accuracy.",
    }


@app.get("/api/reports")
def list_reports() -> List[Dict[str, Any]]:
    """Returns list of generated reports."""
    reports = []
    pdf_path = "data/reports/MoES_MarineGuard_Survey_Report.pdf"
    if os.path.exists(pdf_path):
        reports.append({
            "id": "RPT-PDF-01",
            "title": "MoES Marine Debris Survey Report",
            "format": "PDF",
            "fileSize": f"{os.path.getsize(pdf_path)/1024:.1f} KB",
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(pdf_path))),
            "downloadUrl": "/api/reports/download/MoES_MarineGuard_Survey_Report.pdf",
        })

    geojson_path = "data/reports/marine_debris.geojson"
    if os.path.exists(geojson_path):
        reports.append({
            "id": "RPT-GEOJSON-01",
            "title": "Marine Debris GeoJSON Dataset",
            "format": "GeoJSON",
            "fileSize": f"{os.path.getsize(geojson_path)/1024:.1f} KB",
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(geojson_path))),
            "downloadUrl": "/api/reports/download/marine_debris.geojson",
        })

    s100_path = "data/reports/s100_catalog.json"
    if os.path.exists(s100_path):
        reports.append({
            "id": "RPT-S100-01",
            "title": "IHO S-100 Hydrographic Catalogue",
            "format": "JSON",
            "fileSize": f"{os.path.getsize(s100_path)/1024:.1f} KB",
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(s100_path))),
            "downloadUrl": "/api/reports/download/s100_catalog.json",
        })

    return reports


@app.post("/api/reports")
def generate_report(req: ReportRequest) -> Dict[str, Any]:
    """Generates official report file using Role 4 exporters from the active DetectionResult."""
    targets_dicts = LATEST_DETECTION_STATE.get("classified_targets", [])
    if not targets_dicts:
        # Run default detection to get targets if none exist
        res = run_sss_pipeline("data/demo_sss/ghost_net_contact_01.png", confidence_threshold=0.75)
        targets_dicts = res["classified_targets"]
        LATEST_DETECTION_STATE["classified_targets"] = targets_dicts

    targets = [ClassifiedTarget(**t) for t in targets_dicts]
    fmt = req.format.upper()

    export_res = mcp_server.export_report(export_format=fmt, targets=targets)
    file_path = export_res["file_path"]
    filename = os.path.basename(file_path)

    return {
        "id": f"RPT-{fmt}-{int(time.time())}",
        "format": fmt,
        "filename": filename,
        "filePath": file_path,
        "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "downloadUrl": f"/api/reports/download/{filename}",
    }


@app.get("/api/reports/download/{filename}")
def download_report(filename: str):
    """Serves the generated report file for browser download."""
    safe_filename = os.path.basename(filename)
    path = os.path.join("data/reports", safe_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Report file {safe_filename} not found")

    media_type = "application/octet-stream"
    if safe_filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif safe_filename.endswith(".json") or safe_filename.endswith(".geojson"):
        media_type = "application/json"
    elif safe_filename.endswith(".csv"):
        media_type = "text/csv"

    return FileResponse(path, media_type=media_type, filename=safe_filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
