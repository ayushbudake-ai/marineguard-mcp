from ultralytics.models.yolo.detect import DetectionTrainer
from ultralytics.data.utils import check_det_dataset

from marineguard.preprocessing.v2_dataset import MarineGuardV2Dataset


class MarineGuardV2Trainer(DetectionTrainer):
    """V2 YOLO trainer using the MarineGuard custom dataset."""

    def build_dataset(self, img_path, mode="train", batch=None):
        gs = 32

        if self.model is not None and not isinstance(self.model, str):
            try:
                gs = max(int(self.model.stride.max()), 32)
            except (AttributeError, TypeError, ValueError):
                gs = 32

        return MarineGuardV2Dataset(
            img_path=img_path,
            imgsz=self.args.imgsz,
            batch_size=batch,
            augment=mode == "train",
            hyp=self.args,
            rect=self.args.rect if mode == "val" else False,
            cache=self.args.cache,
            single_cls=self.args.single_cls,
            stride=gs,
            pad=0.0 if mode == "train" else 0.5,
            prefix=f"{mode}: ",
            classes=self.args.classes,
            data=self.data,
            fraction=self.args.fraction if mode == "train" else 1.0,
        )
