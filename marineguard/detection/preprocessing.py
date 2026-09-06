"""
Preprocessing Interface & Hooks for MarineGuard MCP — Role 2: AI Inference & Integration

Defines a clean, modular preprocessing hook so Member 1's scientific preprocessing
pipeline (speckle denoising, sensor resolution normalization, acoustic-shadow calibration)
can be plugged directly into the detection pipeline without refactoring detector or API code.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
import numpy as np
from PIL import Image


class BasePreprocessor(ABC):
    """Abstract interface for image/sensor frame preprocessors."""

    @abstractmethod
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Applies preprocessing transformations to an input image.

        Args:
            image: Raw input numpy array [H, W, C] or [H, W].

        Returns:
            np.ndarray: Preprocessed image array ready for detector inference.
        """
        pass


class DefaultPreprocessor(BasePreprocessor):
    """Standard preprocessor for standard optical and sonar inputs.

    Performs non-scientific image normalization (dimension checks,
    color space conversion, optional target resizing).
    Serves as the default until Member 1 supplies domain-specific filters.
    """

    def __init__(self, target_size: Optional[Tuple[int, int]] = None, normalize_channels: bool = True):
        self.target_size = target_size  # (width, height)
        self.normalize_channels = normalize_channels

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        if not isinstance(image, np.ndarray):
            raise TypeError(f"Expected numpy.ndarray for preprocessing, got {type(image)}")

        if image.size == 0 or len(image.shape) < 2:
            raise ValueError(f"Invalid image array with shape {image.shape}")

        processed = image.copy()

        # Handle 2D Grayscale -> ensure 3-channel for standard YOLO if needed
        if len(processed.shape) == 2 and self.normalize_channels:
            processed = np.stack([processed] * 3, axis=-1)
        elif len(processed.shape) == 3 and processed.shape[2] == 4:
            # Drop alpha channel (RGBA -> RGB)
            processed = processed[:, :, :3]

        # Optional resizing
        if self.target_size is not None:
            pil_img = Image.fromarray(processed)
            pil_resized = pil_img.resize(self.target_size, Image.Resampling.BILINEAR)
            processed = np.array(pil_resized)

        return processed
