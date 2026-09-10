from pathlib import Path
import random
import os

REPO = Path(__file__).resolve().parent

UATD = REPO / "data" / "raw" / "uatd" / "UATD_Training"
IMAGE_DIR = UATD / "images"
LABEL_DIR = UATD / "labels"
SPLIT_DIR = UATD / "yolo"

TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
SEED = 42

for split in ["train", "val", "test"]:
    (SPLIT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
    (SPLIT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

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

for split, split_images in splits.items():
    linked = 0

    for image in split_images:
        label = LABEL_DIR / f"{image.stem}.txt"

        # Skip images with no valid annotations
        if not label.exists() or label.read_text(encoding="utf-8").strip() == "":
            continue

        image_target = SPLIT_DIR / "images" / split / image.name
        label_target = SPLIT_DIR / "labels" / split / label.name

        # Hard-link image instead of copying it
        if not image_target.exists():
            os.link(image, image_target)

        # Copy the small label file
        if not label_target.exists():
            label_target.write_bytes(label.read_bytes())

        linked += 1

    print(f"{split}: {linked} images")

print()
print("UATD YOLO DATASET CREATED")
print("Location:", SPLIT_DIR)