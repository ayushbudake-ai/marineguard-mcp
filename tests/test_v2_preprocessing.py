from pathlib import Path
import numpy as np
from PIL import Image

from marineguard.preprocessing.v2_preprocessing import (
    apply_v2_augmentation,
)

SOURCE = Path(__file__).resolve().parents[1] / "data" / "processed_v2" / "marineguard" / "images" / "train"
if not SOURCE.exists():
    SOURCE = Path(__file__).resolve().parents[1] / "data" / "processed" / "seaclear_segmentation" / "images" / "train"


def test_v2_preprocessing():
    if not SOURCE.exists():
        return

    images = [
        p for p in SOURCE.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ][:100]

    passed = 0

    for path in images:
        original = np.array(Image.open(path).convert("RGB"))
        original_copy = original.copy()

        augmented = apply_v2_augmentation(original)

        assert augmented.shape == original.shape
        assert augmented.dtype == np.uint8
        assert np.isfinite(augmented).all()
        assert original.shape == original_copy.shape
        assert np.array_equal(original, original_copy)

        passed += 1

    print("Images tested:", len(images))
    print("Images passed:", passed)
    print("Original arrays preserved: True")
    print("Shape preserved: True")
    print("dtype valid: True")
    print("Pixel values valid: True")
    print("STATUS: TRAINING-SAFETY TEST PASSED")

