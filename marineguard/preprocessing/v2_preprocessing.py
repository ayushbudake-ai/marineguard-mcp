"""
MarineGuard V2 preprocessing and augmentation utilities.

The original dataset is never modified by this module.
"""

from __future__ import annotations

import cv2
import numpy as np


def speckle_noise_reduction(
    image: np.ndarray,
    strength: int = 5,
) -> np.ndarray:
    """Reduce speckle-like noise while preserving object boundaries."""
    if image is None:
        raise ValueError("image cannot be None")

    if image.dtype != np.uint8:
        raise ValueError("image must be uint8")

    strength = max(1, int(strength))

    return cv2.bilateralFilter(
        image,
        d=strength,
        sigmaColor=50,
        sigmaSpace=50,
    )


def normalize_resolution(
    image: np.ndarray,
    target_size: tuple[int, int] = (512, 512),
) -> np.ndarray:
    """Letterbox an image to target size without stretching."""
    if image is None:
        raise ValueError("image cannot be None")

    target_w, target_h = target_size
    h, w = image.shape[:2]

    scale = min(target_w / w, target_h / h)

    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = cv2.resize(
        image,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA,
    )

    canvas = np.zeros(
        (target_h, target_w, image.shape[2]),
        dtype=image.dtype,
    )

    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2

    canvas[y:y + new_h, x:x + new_w] = resized

    return canvas


def acoustic_shadow_augmentation(
    image: np.ndarray,
    probability: float = 0.25,
) -> np.ndarray:
    """Simulate localized dark acoustic-shadow-like regions."""
    if image is None:
        raise ValueError("image cannot be None")

    if np.random.random() > probability:
        return image.copy()

    result = image.copy()
    h, w = result.shape[:2]

    shadow_w = np.random.randint(
        max(1, w // 10),
        max(2, w // 3),
    )

    shadow_h = np.random.randint(
        max(1, h // 10),
        max(2, h // 2),
    )

    x1 = np.random.randint(0, max(1, w - shadow_w))
    y1 = np.random.randint(0, max(1, h - shadow_h))

    x2 = min(w, x1 + shadow_w)
    y2 = min(h, y1 + shadow_h)

    mask = np.zeros((h, w), dtype=np.uint8)

    cv2.ellipse(
        mask,
        (
            (x1 + x2) // 2,
            (y1 + y2) // 2,
        ),
        (
            max(1, (x2 - x1) // 2),
            max(1, (y2 - y1) // 2),
        ),
        0,
        0,
        360,
        255,
        -1,
    )

    darkness = np.random.uniform(0.35, 0.70)

    darkened = (
        result.astype(np.float32) * darkness
    ).astype(np.uint8)

    mask_3ch = cv2.merge([mask, mask, mask])

    return np.where(
        mask_3ch > 0,
        darkened,
        result,
    ).astype(np.uint8)


def heave_pitch_roll_dropout(
    image: np.ndarray,
    probability: float = 0.20,
) -> np.ndarray:
    """Simulate partial frame dropout caused by sensor/motion instability."""
    if image is None:
        raise ValueError("image cannot be None")

    if np.random.random() > probability:
        return image.copy()

    result = image.copy()
    h, w = result.shape[:2]

    dropout_height = np.random.randint(
        max(1, h // 20),
        max(2, h // 8),
    )

    dropout_width = np.random.randint(
        max(1, w // 20),
        max(2, w // 8),
    )

    if np.random.random() < 0.5:
        result[:dropout_height, :] = 0
    else:
        result[h - dropout_height:, :] = 0

    if np.random.random() < 0.5:
        if np.random.random() < 0.5:
            result[:, :dropout_width] = 0
        else:
            result[:, w - dropout_width:] = 0

    return result


def apply_v2_augmentation(
    image: np.ndarray,
) -> np.ndarray:
    """Apply the complete V2 appearance augmentation pipeline."""
    if image is None:
        raise ValueError("image cannot be None")

    result = image.copy()

    result = speckle_noise_reduction(result)

    result = acoustic_shadow_augmentation(
        result,
        probability=0.25,
    )

    result = heave_pitch_roll_dropout(
        result,
        probability=0.20,
    )

    return result
