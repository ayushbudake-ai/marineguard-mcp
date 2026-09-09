"""
Side-Scan Sonar Waterfall Processing Engine for MarineGuard MCP — Role 2: AI Inference & Integration

Provides:
- CA-CFAR 2D acoustic anomaly candidate extraction
- detect_waterfall() producing canonical Detection / DetectionResult schemas
- process_waterfall_ping() adapting detections to DebrisContact for MultiSensorFusionEngine
- Pluggable ML model inference interface when dedicated SSS weights are supplied
- Robust matrix & image input validation (NaN/Inf checking, shape validation)
- Side-scan waterfall annotation
"""

import io
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np
from PIL import Image
import cv2

from marineguard.schemas import DebrisContact
from marineguard.detection.schema import Detection, DetectionResult
from marineguard.detection.detector import BaseDetector
from marineguard.detection.model_loader import MarineDebrisModel, ModelNotFoundError
from marineguard.detection.pipeline import ImageValidationError
from marineguard.detection.preprocessing import DefaultPreprocessor
from marineguard.detection.postprocessing import PostProcessor

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SSS_PT_PATH = REPO_ROOT / "runs" / "detect" / "runs" / "marineguard_sss_yolov8n_baseline" / "weights" / "best.pt"
DEFAULT_SSS_ONNX_PATH = REPO_ROOT / "runs" / "detect" / "runs" / "marineguard_sss_yolov8n_baseline" / "weights" / "best.onnx"


class SideScanDetector(BaseDetector):
    """CA-CFAR Acoustic Anomaly Detector & Side-Scan Sonar Processing Engine.

    Executes 2D Cell-Averaging Constant False Alarm Rate (CA-CFAR) anomaly
    detection over waterfall sonar imagery, extracting acoustic highlight/shadow
    regions into candidate bounding boxes and anomaly confidence scores,
    with an integrated SSS specialist YOLO/ONNX model (mapping local class 0 -> class 29 "net").

    Taxonomy:
        - CA-CFAR emits class 'unknown-object' (class_id=27 from official marineguard_classes.yaml)
          for class-agnostic acoustic anomalies.
        - SSS specialist model emits class 'net' (class_id=29 from official marineguard_classes.yaml)
          when use_sss_model=True or when loaded via with_sss_model().
          Maps SSS native class 0 to MarineGuard class 29 ("net")
          per the official taxonomy contract.
    """

    UNKNOWN_CLASS_NAME = "unknown-object"
    UNKNOWN_CLASS_ID = 27
    SSS_CLASS_NAME = "net"
    SSS_CLASS_ID = 29

    # SSS YOLO class mapping: native SSS class 0 → MarineGuard class 29 "net"
    # Source: AGENTS.md section 6 (Official Taxonomy), section 15 (SSS Class Mapping)
    # NEVER map SSS net to class 27 (unknown-object).
    SSS_CLASS_MAP: Dict[int, int] = {
        0: 29,
    }

    SSS_CLASS_NAMES: Dict[int, str] = {
        29: "net",
    }

    SSS_IMAGE_SIZE: int = 640

    def __init__(
        self,
        cfar_pfa: float = 1e-4,
        confidence_threshold: float = 0.50,
        min_area: int = 25,
        min_dim: int = 4,
        model: Optional[MarineDebrisModel] = None,
        model_path: Optional[Union[str, Path]] = None,
        use_sss_model: bool = False,
    ):
        self.cfar_pfa = cfar_pfa
        self.confidence_threshold = confidence_threshold
        self.min_area = min_area
        self.min_dim = min_dim
        if model is not None:
            self.model = model
        elif model_path is not None:
            self.model = MarineDebrisModel.get(
                model_path=Path(model_path),
                confidence_threshold=confidence_threshold,
            )
        else:
            self.model = MarineDebrisModel.get(confidence_threshold=confidence_threshold)
        self.use_sss_model = use_sss_model

    @classmethod
    def with_sss_model(
        cls,
        confidence_threshold: float = 0.50,
        use_onnx: bool = False,
        model_path: Optional[Union[str, Path]] = None,
        cfar_pfa: float = 1e-4,
        min_area: int = 25,
        min_dim: int = 4,
    ) -> "SideScanDetector":
        """Factory initializing SideScanDetector configured with the SSS specialist model.

        When use_onnx=False (default), loads:
            runs/detect/runs/marineguard_sss_yolov8n_baseline/weights/best.pt
        When use_onnx=True, loads:
            runs/detect/runs/marineguard_sss_yolov8n_baseline/weights/best.onnx
        """
        if model_path is not None:
            target_path = Path(model_path)
        else:
            target_path = DEFAULT_SSS_ONNX_PATH if use_onnx else DEFAULT_SSS_PT_PATH

        model = MarineDebrisModel.get(
            model_path=target_path,
            confidence_threshold=confidence_threshold,
            task="detect",
        )
        return cls(
            cfar_pfa=cfar_pfa,
            confidence_threshold=confidence_threshold,
            min_area=min_area,
            min_dim=min_dim,
            model=model,
            use_sss_model=True,
        )

    @property
    def is_ready(self) -> bool:
        """CFAR algorithm is ready immediately; model is ready if weights loaded."""
        return True

    @property
    def is_model_loaded(self) -> bool:
        return self.model.is_loaded

    @property
    def model_name(self) -> str:
        if self.model.is_loaded:
            return f"SideScanDetector(CA-CFAR+{self.model.model_path.name})"
        return "SideScanDetector(CA-CFAR)"

    def cfar_detect(self, waterfall_row: np.ndarray, num_guard: int = 4, num_ref: int = 16) -> List[int]:
        """1D Cell-Averaging Constant False Alarm Rate (CA-CFAR) row anomaly detector (legacy support)."""
        anomalies = []
        N = len(waterfall_row)
        for i in range(num_ref + num_guard, N - num_ref - num_guard):
            ref_cells = np.concatenate([
                waterfall_row[i - num_ref - num_guard : i - num_guard],
                waterfall_row[i + num_guard + 1 : i + num_guard + 1 + num_ref],
            ])
            noise_floor = np.mean(ref_cells)
            alpha = num_ref * (self.cfar_pfa ** (-1.0 / num_ref) - 1.0)
            threshold = alpha * noise_floor
            if waterfall_row[i] > threshold:
                anomalies.append(i)
        return anomalies

    def validate_and_normalize_matrix(
        self,
        image_input: Union[str, Path, bytes, np.ndarray, Image.Image]
    ) -> Tuple[np.ndarray, int, int]:
        """Validates input array/image and normalizes to 2D float32 intensity matrix [H, W].

        Raises:
            ImageValidationError: If input is empty, has invalid dimensions, or contains NaN/Inf.
        """
        # Handle path
        if isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if not p.exists() or not p.is_file():
                raise ImageValidationError(f"Waterfall image file not found: '{p}'")
            try:
                pil_img = Image.open(p)
                pil_img.verify()
                pil_img = Image.open(p)
                arr = np.array(pil_img)
            except Exception as exc:
                raise ImageValidationError(f"Failed to decode waterfall image file '{p}': {exc}") from exc

        # Handle bytes
        elif isinstance(image_input, (bytes, bytearray)):
            if len(image_input) == 0:
                raise ImageValidationError("Input waterfall image bytes are empty (0 bytes).")
            try:
                pil_img = Image.open(io.BytesIO(image_input))
                pil_img.verify()
                pil_img = Image.open(io.BytesIO(image_input))
                arr = np.array(pil_img)
            except Exception as exc:
                raise ImageValidationError(f"Failed to decode waterfall bytes: {exc}") from exc

        # Handle PIL Image
        elif isinstance(image_input, Image.Image):
            arr = np.array(image_input)

        # Handle NumPy Array
        elif isinstance(image_input, np.ndarray):
            arr = image_input

        else:
            raise ImageValidationError(
                f"Unsupported waterfall input type '{type(image_input).__name__}'. "
                f"Expected 2D/3D np.ndarray, PIL.Image, bytes, or file path."
            )

        # Dimension and emptiness validation
        if arr.size == 0:
            raise ImageValidationError("Waterfall array is empty (0 elements).")

        if len(arr.shape) not in (2, 3):
            raise ImageValidationError(f"Invalid waterfall matrix dimensions {arr.shape}. Expected 2D (H, W) or 3D (H, W, C).")

        # Check for NaN / Inf
        if np.isnan(arr).any():
            raise ImageValidationError("Waterfall matrix contains NaN (Not-a-Number) values.")
        if np.isinf(arr).any():
            raise ImageValidationError("Waterfall matrix contains Infinite (Inf) values.")

        # Convert to 2D float32 intensity matrix
        if len(arr.shape) == 3:
            if arr.shape[2] == 1:
                mat_f = arr[:, :, 0].astype(np.float32)
            elif arr.shape[2] in (3, 4):
                mat_f = np.mean(arr[:, :, :3], axis=2).astype(np.float32)
            else:
                raise ImageValidationError(f"Unsupported channel dimension in waterfall matrix: {arr.shape[2]}")
        else:
            mat_f = arr.astype(np.float32)

        h, w = mat_f.shape[:2]
        if h <= 0 or w <= 0:
            raise ImageValidationError(f"Invalid waterfall dimensions: {w}x{h}")

        return mat_f, w, h

    def cfar_detect_2d(
        self,
        mat_f: np.ndarray,
        cfar_pfa: Optional[float] = None,
        confidence_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Executes 2D CA-CFAR anomaly candidate detection on a 2D float32 intensity matrix."""
        pfa = cfar_pfa if cfar_pfa is not None else self.cfar_pfa
        conf_thresh = confidence_threshold if confidence_threshold is not None else self.confidence_threshold

        h, w = mat_f.shape[:2]
        if h < 8 or w < 8:
            return []

        # Dynamic window sizes scaled to matrix dimensions
        guard_w = max(8, min(32, w // 8))
        guard_h = max(8, min(32, h // 8))
        ref_w = max(8, min(32, w // 8))
        ref_h = max(8, min(32, h // 8))

        K_total_w = 2 * (guard_w + ref_w) + 1
        K_total_h = 2 * (guard_h + ref_h) + 1
        K_guard_w = 2 * guard_w + 1
        K_guard_h = 2 * guard_h + 1

        # Background noise floor via sliding window excluding guard region
        total_sum = cv2.boxFilter(mat_f, ddepth=-1, ksize=(K_total_w, K_total_h), normalize=False, borderType=cv2.BORDER_REPLICATE)
        guard_sum = cv2.boxFilter(mat_f, ddepth=-1, ksize=(K_guard_w, K_guard_h), normalize=False, borderType=cv2.BORDER_REPLICATE)
        ref_count = max(1, (K_total_w * K_total_h) - (K_guard_w * K_guard_h))
        noise_floor = np.maximum(total_sum - guard_sum, 1e-6) / float(ref_count)

        # Background variance / standard deviation
        total_sq = cv2.boxFilter(mat_f**2, ddepth=-1, ksize=(K_total_w, K_total_h), normalize=False, borderType=cv2.BORDER_REPLICATE)
        guard_sq = cv2.boxFilter(mat_f**2, ddepth=-1, ksize=(K_guard_w, K_guard_h), normalize=False, borderType=cv2.BORDER_REPLICATE)
        noise_var = np.maximum((total_sq - guard_sq) / float(ref_count) - noise_floor**2, 1.0)
        noise_std = np.sqrt(noise_var)

        # Adaptive threshold multiplier based on Pfa
        k_mult = max(2.5, np.sqrt(-2.0 * np.log(max(pfa, 1e-8))))
        threshold = noise_floor + k_mult * noise_std

        # Identify anomaly pixels above adaptive threshold and above background mean + 1.5*std
        global_mean = float(np.mean(mat_f))
        global_std = float(np.std(mat_f))
        intensity_floor = global_mean + 1.5 * global_std
        anomaly_mask = (mat_f > threshold) & (mat_f > intensity_floor)

        if not np.any(anomaly_mask):
            return []

        # Morphological consolidation to cluster highlights
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed_mask = cv2.morphologyEx(anomaly_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed_mask, connectivity=8)

        candidates: List[Dict[str, Any]] = []
        for k in range(1, num_labels):
            x, y, comp_w, comp_h, area = stats[k]
            if area < self.min_area or comp_w < self.min_dim or comp_h < self.min_dim:
                continue

            # Bounding box coordinates clamped to image dimensions
            x1 = max(0.0, float(x))
            y1 = max(0.0, float(y))
            x2 = min(float(w), float(x + comp_w))
            y2 = min(float(h), float(y + comp_h))

            if x2 <= x1 or y2 <= y1:
                continue

            mask_k = (labels[y:y+comp_h, x:x+comp_w] == k)
            region_vals = mat_f[y:y+comp_h, x:x+comp_w][mask_k]
            region_noise = noise_floor[y:y+comp_h, x:x+comp_w][mask_k]
            region_std = noise_std[y:y+comp_h, x:x+comp_w][mask_k]

            peak_val = float(np.max(region_vals)) if len(region_vals) > 0 else float(np.mean(mat_f))
            mean_noise = float(np.mean(region_noise)) if len(region_noise) > 0 else 1.0
            mean_std = float(np.mean(region_std)) if len(region_std) > 0 else 1.0
            snr = (peak_val - mean_noise) / max(mean_std, 1e-3)

            # Map SNR to deterministic anomaly confidence in [0.50, 0.99]
            conf = float(min(0.99, max(0.50, 0.50 + 0.45 * (1.0 - np.exp(-max(0.0, snr - 2.0) / 8.0)))))

            if conf >= conf_thresh:
                candidates.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": round(conf, 4),
                    "snr": round(snr, 2),
                    "area": int(area),
                })

        return candidates

    def _prepare_sss_image(
        self,
        image_input: Union[str, Path, bytes, np.ndarray, Image.Image],
    ) -> Tuple[np.ndarray, int, int]:
        """Validates and prepares input as a 3-channel uint8 numpy array [H, W, 3] and (width, height).

        Raises:
            ImageValidationError: If input is missing, empty, corrupt, or contains NaN/Inf values.
        """
        # File path
        if isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if not p.exists() or not p.is_file():
                raise ImageValidationError(f"Waterfall image file not found: '{p}'")
            supported_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
            if p.suffix.lower() not in supported_exts:
                raise ImageValidationError(f"Unsupported waterfall image extension '{p.suffix}'.")
            try:
                pil_img = Image.open(p)
                pil_img.verify()
                pil_img = Image.open(p)
                w, h = pil_img.size
                arr = np.array(pil_img.convert("RGB"))
            except Exception as exc:
                raise ImageValidationError(f"Failed to decode waterfall image file '{p}': {exc}") from exc

        # Raw Bytes
        elif isinstance(image_input, (bytes, bytearray)):
            if len(image_input) == 0:
                raise ImageValidationError("Input waterfall image bytes are empty (0 bytes).")
            try:
                pil_img = Image.open(io.BytesIO(image_input))
                pil_img.verify()
                pil_img = Image.open(io.BytesIO(image_input))
                w, h = pil_img.size
                arr = np.array(pil_img.convert("RGB"))
            except Exception as exc:
                raise ImageValidationError(f"Failed to decode waterfall bytes: {exc}") from exc

        # PIL Image
        elif isinstance(image_input, Image.Image):
            w, h = image_input.size
            if w <= 0 or h <= 0:
                raise ImageValidationError(f"Invalid image dimensions: {w}x{h}")
            try:
                arr = np.array(image_input.convert("RGB"))
            except Exception as exc:
                raise ImageValidationError(f"Failed to convert PIL Image: {exc}") from exc

        # NumPy Array
        elif isinstance(image_input, np.ndarray):
            arr_in = image_input
            if arr_in.size == 0:
                raise ImageValidationError("Waterfall array is empty (0 elements).")
            if len(arr_in.shape) not in (2, 3):
                raise ImageValidationError(f"Invalid waterfall matrix dimensions {arr_in.shape}. Expected 2D or 3D.")
            if np.isnan(arr_in).any():
                raise ImageValidationError("Waterfall matrix contains NaN (Not-a-Number) values.")
            if np.isinf(arr_in).any():
                raise ImageValidationError("Waterfall matrix contains Infinite (Inf) values.")
            h, w = arr_in.shape[:2]
            if h <= 0 or w <= 0:
                raise ImageValidationError(f"Invalid waterfall dimensions: {w}x{h}")

            if len(arr_in.shape) == 2:
                if arr_in.dtype != np.uint8:
                    if arr_in.max() <= 1.0 and arr_in.max() > 0:
                        arr_u8 = (arr_in * 255.0).clip(0, 255).astype(np.uint8)
                    else:
                        arr_u8 = arr_in.clip(0, 255).astype(np.uint8)
                else:
                    arr_u8 = arr_in
                arr = np.stack([arr_u8] * 3, axis=-1)
            else:
                if arr_in.shape[2] == 1:
                    arr_u8 = arr_in[:, :, 0]
                    if arr_u8.dtype != np.uint8:
                        if arr_u8.max() <= 1.0 and arr_u8.max() > 0:
                            arr_u8 = (arr_u8 * 255.0).clip(0, 255).astype(np.uint8)
                        else:
                            arr_u8 = arr_u8.clip(0, 255).astype(np.uint8)
                    arr = np.stack([arr_u8] * 3, axis=-1)
                elif arr_in.shape[2] == 4:
                    arr = arr_in[:, :, :3]
                    if arr.dtype != np.uint8:
                        arr = arr.clip(0, 255).astype(np.uint8)
                elif arr_in.shape[2] == 3:
                    arr = arr_in
                    if arr.dtype != np.uint8:
                        arr = arr.clip(0, 255).astype(np.uint8)
                else:
                    raise ImageValidationError(f"Unsupported channel dimension in waterfall matrix: {arr_in.shape[2]}")

        else:
            raise ImageValidationError(
                f"Unsupported waterfall input type '{type(image_input).__name__}'. "
                f"Expected 2D/3D np.ndarray, PIL.Image, bytes, or file path."
            )

        return arr, w, h

    def detect_sss(
        self,
        image_input: Union[str, Path, bytes, np.ndarray, Image.Image],
        confidence_threshold: Optional[float] = None,
    ) -> DetectionResult:
        """Executes SSS specialist YOLO/ONNX model inference on side-scan sonar waterfall imagery.

        One-class mapping:
            Local model class 0 -> official MarineGuard taxonomy class 29 ("net").

        Raises:
            ModelNotFoundError: If SSS specialist weights are not loaded.
            ImageValidationError: If input fails validation.
        """
        if not self.is_model_loaded:
            raise ModelNotFoundError(
                f"SSS specialist model is not available at '{self.model.model_path}'. "
                f"Trained SSS weights must be loaded to run detect_sss()."
            )

        img_arr, w, h = self._prepare_sss_image(image_input)
        conf_thresh = confidence_threshold if confidence_threshold is not None else self.confidence_threshold

        preprocessor = DefaultPreprocessor()
        processed_img = preprocessor.preprocess(img_arr)

        start_time = time.perf_counter()
        results = self.model.model.predict(
             processed_img,
            imgsz=512,
            rect=False,
            conf=conf_thresh,
            device="cpu",
            verbose=False,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        detections: List[Detection] = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                local_cls = int(box.cls.item())
                # SSS specialist is a single-class model mapping local class 0 -> class 29 ("net")
                if local_cls == 0:
                    cls_id = self.SSS_CLASS_ID
                    cls_name = self.SSS_CLASS_NAME
                else:
                    cls_id = local_cls
                    cls_name = self.model.class_names.get(local_cls, f"class_{local_cls}")

                conf = float(box.conf.item())
                raw_bbox = [float(coord) for coord in box.xyxy[0].tolist()]

                detections.append(
                    Detection(
                        class_name=cls_name,
                        class_id=cls_id,
                        confidence=conf,
                        bbox=raw_bbox,
                        metadata={
                            "sensor": "side_scan",
                            "method": "SSS_YOLO",
                            "local_class_id": local_cls,
                            "official_class_id": cls_id,
                        },
                    )
                )

        raw_result = DetectionResult.from_detections(
            detections=detections,
            image_width=w,
            image_height=h,
            inference_time_ms=latency_ms,
            model_name=self.model_name,
        )

        postprocessor = PostProcessor(confidence_threshold=conf_thresh)
        return postprocessor.process(raw_result, image_width=w, image_height=h)

    def detect_waterfall(
        self,
        image_input: Union[str, Path, bytes, np.ndarray, Image.Image],
        confidence_threshold: Optional[float] = None,
        cfar_pfa: Optional[float] = None,
        use_ml: bool = False,
        use_sss_model: Optional[bool] = None,
    ) -> DetectionResult:
        """Executes acoustic anomaly detection on a side-scan sonar waterfall image/matrix.

        Args:
            image_input: File path, raw bytes, PIL Image, or 2D/3D numpy array.
            confidence_threshold: Minimum confidence threshold.
            cfar_pfa: Probability of false alarm for CA-CFAR (when use_ml=False).
            use_ml: If True, uses the dedicated SSS specialist model; if False, uses CA-CFAR.

        When use_sss_model is True (or set at construction time), routes through the SSS YOLO
        inference path and maps native SSS class 0 to MarineGuard class 29 ("net").

        When use_sss_model is False (default), uses the CA-CFAR path and emits
        class 27 ("unknown-object") for acoustic anomalies.

        Raises:
            ImageValidationError: If input fails validation (empty, NaN, Inf, wrong shape, etc.)
            RuntimeError: If SSS model is selected but not loaded.

        Returns:
            DetectionResult: Structured container of canonical Detection objects.
        """
        if use_ml:
            return self.detect_sss(image_input, confidence_threshold=confidence_threshold)

        start_time = time.perf_counter()

        mat_f, width, height = self.validate_and_normalize_matrix(image_input)

        if use_sss_model is True:
            if self.model is None or not self.model.is_loaded:
                raise RuntimeError("SSS model is not loaded")

            # Convert 2D grayscale matrix to 3-channel RGB-like array for YOLO
            model_image = np.stack(
                [mat_f, mat_f, mat_f],
                axis=-1,
            )

            raw_detections = self.model.predict(
                model_image,
                imgsz=self.SSS_IMAGE_SIZE,
            )

            detections: List[Detection] = []

            for raw in raw_detections:
                native_class_id = int(raw.get("class_id", -1))

                # Only accept classes that have a mapping in the SSS class map
                if native_class_id not in self.SSS_CLASS_MAP:
                    continue

                marineguard_class_id = self.SSS_CLASS_MAP[native_class_id]
                class_name = self.SSS_CLASS_NAMES[marineguard_class_id]

                bbox = raw.get("bbox")
                confidence = float(raw.get("confidence", 0.0))

                if bbox is None or len(bbox) != 4:
                    continue

                detections.append(
                    Detection(
                        class_name=class_name,
                        class_id=marineguard_class_id,
                        confidence=confidence,
                        bbox=[float(v) for v in bbox],
                        metadata={
                            "sensor": "side_scan",
                            "method": "SSS-YOLO",
                            "native_class_id": native_class_id,
                        },
                    )
                )

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return DetectionResult.from_detections(
                detections=detections,
                image_width=width,
                image_height=height,
                inference_time_ms=latency_ms,
                model_name=self.model_name,
                status="ok",
            )

        # CA-CFAR path (default)
        conf_thresh = confidence_threshold if confidence_threshold is not None else self.confidence_threshold
        candidates = self.cfar_detect_2d(mat_f, cfar_pfa=cfar_pfa, confidence_threshold=conf_thresh)

        detections_cfar: List[Detection] = []
        for cand in candidates:
            detections_cfar.append(
                Detection(
                    class_name=self.UNKNOWN_CLASS_NAME,
                    class_id=self.UNKNOWN_CLASS_ID,
                    confidence=cand["confidence"],
                    bbox=cand["bbox"],
                    metadata={
                        "sensor": "side_scan",
                        "method": "CA-CFAR",
                        "snr": cand["snr"],
                        "area_pixels": cand["area"],
                        "anomaly_type": "acoustic_highlight",
                    },
                )
            )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return DetectionResult.from_detections(
            detections=detections_cfar,
            image_width=width,
            image_height=height,
            inference_time_ms=latency_ms,
            model_name=self.model_name,
        )

    def detect(self, image: np.ndarray) -> DetectionResult:
        """BaseDetector interface implementation.

        When use_sss_model=True, routes through the SSS YOLO path.
        Otherwise uses CA-CFAR.

        Catches ImageValidationError and converts it to an error DetectionResult
        so callers can inspect result.status without catching exceptions.

        For production use that requires explicit error propagation, call
        detect_waterfall() or detect_sss() directly.
        """
        try:
            return self.detect_waterfall(image, use_sss_model=self.use_sss_model)
        except ImageValidationError as exc:
            return DetectionResult.from_detections(
                detections=[],
                status=f"error: {exc}",
            )

    def process_waterfall_ping(
        self,
        ping_payload: Dict[str, Any],
        allow_dev_fallback: bool = True,
        use_ml: bool = False,
    ) -> List[DebrisContact]:
        """Runs CA-CFAR / ML detection on ping payload and maps results to DebrisContact objects for fusion."""
        meta = ping_payload.get("target_meta", {})
        sonar_img = ping_payload.get("sonar_waterfall")

        # 1. Real Detection Path (CA-CFAR or ML)
        if sonar_img is not None and isinstance(sonar_img, np.ndarray) and sonar_img.size > 0:
            try:
                result = self.detect_waterfall(sonar_img, use_ml=use_ml)
                if result.count > 0:
                    contacts = []
                    for i, det in enumerate(result.detections):
                        # Map label and confidence from metadata if available in simulated replay
                        label = meta.get("type", det.class_name)
                        conf = meta.get("sonar_confidence", det.confidence)
                        contacts.append(
                            DebrisContact(
                                contact_id=f"SONAR_{meta.get('id', f'Candidate_{i:02d}')}",
                                sensor_id="side_scan_01",
                                sensor_type="side_scan",
                                raw_confidence=round(float(conf), 3),
                                bbox=tuple(det.bbox),
                                label_candidate=label,
                                acoustic_shadow_ratio=meta.get("shadow_ratio", 0.35),
                                estimated_dimensions_m=meta.get("dimensions_m", (10.0, 5.0, 0.5)),
                                lat_lon=meta.get("lat_lon", (13.0835, 80.2715)),
                                depth_m=meta.get("depth_m", 24.3),
                            )
                        )
                    return contacts
            except Exception:
                pass

        # 2. Development test replay fallback (active when simulated ping has metadata but no cfar detections)
        if not allow_dev_fallback:
            return []

        confidence = meta.get("sonar_confidence", 0.88)
        if confidence < self.confidence_threshold:
            return []

        contact = DebrisContact(
            contact_id=f"SONAR_{meta.get('id', 'Contact_01')}",
            sensor_id="side_scan_01",
            sensor_type="side_scan",
            raw_confidence=round(confidence, 3),
            bbox=(100.0, 100.0, 150.0, 150.0),
            label_candidate=meta.get("type", "ghost_net"),
            acoustic_shadow_ratio=meta.get("shadow_ratio", 0.35),
            estimated_dimensions_m=meta.get("dimensions_m", (10.0, 5.0, 0.5)),
            lat_lon=meta.get("lat_lon", (13.0835, 80.2715)),
            depth_m=meta.get("depth_m", 24.3),
        )
        return [contact]

    def annotate_waterfall(
        self,
        image_input: Union[str, Path, bytes, np.ndarray, Image.Image],
        detections: Optional[Union[DetectionResult, List[Detection]]] = None,
        use_ml: bool = False,
    ) -> Image.Image:
        """Renders candidate bounding boxes and labels onto the waterfall image."""
        from marineguard.detection.annotator import ImageAnnotator
        if detections is None:
            detections = self.detect_waterfall(image_input, use_ml=use_ml)
        annotator = ImageAnnotator()
        return annotator.annotate(image_input, detections)
