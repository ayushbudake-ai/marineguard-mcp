from ultralytics.data.dataset import YOLODataset
from ultralytics.data.augment import Compose

from marineguard.preprocessing.v2_ultralytics import MarineGuardV2Transform


class MarineGuardV2Dataset(YOLODataset):
    """YOLODataset with MarineGuard V2 appearance preprocessing."""

    def build_transforms(self, hyp=None):
        transforms = super().build_transforms(hyp)

        if self.augment:
            transforms.insert(0, MarineGuardV2Transform())

        return transforms
