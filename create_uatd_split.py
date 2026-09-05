import random
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent

UATD_DIR = REPO / "data" / "raw" / "uatd" / "UATD_Training"
IMAGE_DIR = UATD_DIR / "images"
LABEL_DIR = UATD_DIR / "labels"
SPLIT_DIR = UATD_DIR / "splits"

TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
TEST_RATIO = 0.10
SEED = 42

images = sorted(IMAGE_DIR.glob("*.bmp"))

random.seed(SEED)
random.shuffle(images)

total = len(images)

train_end = int(total * TRAIN_RATIO)
val_end = train_end + int(total * VAL_RATIO)

splits = {
    "train": images[:train_end],
    "val": images[train_end:val_end],
    "test": images[val_end:],
}

for split_name, split_images in splits.items():
    split_dir = SPLIT_DIR / split_name
    split_dir.mkdir(parents=True, exist_ok=True)

    for image in split_images:
        label = LABEL_DIR / f"{image.stem}.txt"

        # Store paths only; do not copy the large BMP files.
        (split_dir / f"{image.stem}.txt").write_text(
            str(image.resolve()) + "\n" + str(label.resolve()),
            encoding="utf-8"
        )

    print(split_name, ":", len(split_images))

print("TOTAL:", sum(len(v) for v in splits.values()))