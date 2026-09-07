from ultralytics.data.augment import BaseTransform

from marineguard.preprocessing.v2_preprocessing import (
    apply_v2_augmentation,
)


class MarineGuardV2Transform(BaseTransform):
    """MarineGuard V2 appearance preprocessing for Ultralytics training."""

    def __init__(self):
        super().__init__()

    def apply_image(self, labels, params=None):
        """Apply appearance-only preprocessing to the training image."""
        labels["img"] = apply_v2_augmentation(labels["img"])
        return labels

    def apply_instances(self, labels, params=None):
        """Bounding boxes remain unchanged because no geometry is modified."""
        return labels
