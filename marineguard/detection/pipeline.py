"""
End-to-End Image Detection Pipeline for MarineGuard MCP — Role 2: AI Inference & Integration

Flow:
    Image (Path / Bytes / np.ndarray / PIL)
    ↓
    Validation (Format, Decodability, Non-zero Dimensions)
    ↓
    Preprocessing Interface (Hook for Member 1)
    ↓
    Detector (BaseDetector: YOLO in Prod, Mock in Test)
    ↓
    Post-Processing (BBox validation, clipping, confidence thresholding)
    ↓
    Structured DetectionResult
"""

import io
from pathlib import Path
from typing import Union, Optional, Tuple, Dict, Any
import numpy as np
from PIL import Image, UnidentifiedImageError

from marineguard.detection.schema import DetectionResult
from marineguard.detection.detector import BaseDetector, YOLODetector
from marineguard.detection.preprocessing import BasePreprocessor, DefaultPreprocessor
from marineguard.detection.postprocessing import PostProcessor
from marineguard.detection.filtering import DetectionFilter
from marineguard.detection.model_loader import ModelNotFoundError


class ImageValidationError(ValueError):
    """Raised when an input image fails decoding or dimension validation."""
    pass


class ImageDetectionPipeline:
    """Coordinates validation, preprocessing, model inference, postprocessing, and Role 3 filtering."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

    def __init__(
        self,
        detector: Optional[BaseDetector] = None,
        preprocessor: Optional[BasePreprocessor] = None,
        postprocessor: Optional[PostProcessor] = None,
        detection_filter: Optional[DetectionFilter] = None,
        confidence_threshold: float = 0.50,
        enable_filtering: bool = True,
    ):
        self.detector = detector if detector is not None else YOLODetector(confidence_threshold=confidence_threshold)
        self.preprocessor = preprocessor if preprocessor is not None else DefaultPreprocessor()
        self.postprocessor = postprocessor if postprocessor is not None else PostProcessor(confidence_threshold=confidence_threshold)
        self.enable_filtering = enable_filtering
        self.detection_filter = detection_filter if detection_filter is not None else DetectionFilter(confidence_threshold=confidence_threshold)

    def validate_and_load_image(self, image_input: Union[str, Path, bytes, np.ndarray, Image.Image]) -> Tuple[np.ndarray, int, int]:
        """Validates input and converts to numpy array [H, W, C] along with (width, height).

        Raises:
            ImageValidationError: If image cannot be found, decoded, or has invalid dimensions.
        """
        # Case 1: File Path
        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if not path.exists() or not path.is_file():
                raise ImageValidationError(f"Image file not found: '{path}'")
            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                raise ImageValidationError(
                    f"Unsupported image extension '{path.suffix}'. "
                    f"Supported formats: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
                )
            try:
                pil_img = Image.open(path)
                pil_img.verify()  # Validate image integrity
                pil_img = Image.open(path)  # Re-open after verify
                img_array = np.array(pil_img.convert("RGB"))
            except Exception as exc:
                raise ImageValidationError(f"Failed to decode image file '{path}': {exc}") from exc

        # Case 2: Raw Bytes
        elif isinstance(image_input, (bytes, bytearray)):
            if len(image_input) == 0:
                raise ImageValidationError("Input image bytes are empty (0 bytes).")
            try:
                pil_img = Image.open(io.BytesIO(image_input))
                pil_img.verify()
                pil_img = Image.open(io.BytesIO(image_input))
                img_array = np.array(pil_img.convert("RGB"))
            except Exception as exc:
                raise ImageValidationError(f"Failed to decode image bytes: {exc}") from exc

        # Case 3: PIL Image
        elif isinstance(image_input, Image.Image):
            try:
                img_array = np.array(image_input.convert("RGB"))
            except Exception as exc:
                raise ImageValidationError(f"Failed to convert PIL Image: {exc}") from exc

        # Case 4: Numpy array
        elif isinstance(image_input, np.ndarray):
            if image_input.size == 0:
                raise ImageValidationError("Empty numpy image array (0 elements).")
            if len(image_input.shape) not in (2, 3):
                raise ImageValidationError(f"Invalid numpy array shape {image_input.shape}. Expected 2D or 3D.")
            img_array = image_input

        else:
            raise ImageValidationError(
                f"Unsupported image input type '{type(image_input)}'. "
                f"Expected str, Path, bytes, np.ndarray, or PIL.Image."
            )

        h, w = img_array.shape[:2]
        if h <= 0 or w <= 0:
            raise ImageValidationError(f"Invalid image dimensions: {w}x{h}")

        return img_array, w, h

    def process(self, image_input: Union[str, Path, bytes, np.ndarray, Image.Image]) -> DetectionResult:
        """Runs the complete end-to-end detection pipeline on an image."""
        # 1. Validation & Loading
        raw_image, width, height = self.validate_and_load_image(image_input)

        # 2. Preprocessing Hook
        preprocessed_image = self.preprocessor.preprocess(raw_image)

        # 3. Detector Inference
        raw_result = self.detector.detect(preprocessed_image)

        # 4. Post-processing (Role 2)
        postprocessed_result = self.postprocessor.process(
            result=raw_result,
            image_width=width,
            image_height=height,
        )

        # 5. Role 3 Filtering & Confidence Presentation & Evidence
        if self.enable_filtering and self.detection_filter is not None:
            if hasattr(self.postprocessor, "confidence_threshold"):
                self.detection_filter.confidence_threshold = self.postprocessor.confidence_threshold
            filtered_result = self.detection_filter.filter(
                postprocessed_result,
                image_width=width,
                image_height=height,
            )
            final_result = filtered_result.to_detection_result()
        else:
            final_result = postprocessed_result

        return final_result
