from pathlib import Path
import random
import os

REPO = Path(__file__).resolve().parent

SEACLEAR = REPO / "data" / "raw" / "seaclear"
LABEL_DIR = SEACLEAR / "labels"
YOLO_DIR = SEACLEAR / "yolo"

TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
SEED = 42

# ------------------------------------------------------------
# Find all SeaClear images
# ------------------------------------------------------------

images = sorted(
    p for p in SEACLEAR.rglob("*.jpg")
    if "yolo" not in p.parts and p.parent.name != "labels"
)

if not images:
    raise FileNotFoundError("No SeaClear JPG images found.")

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

# ------------------------------------------------------------
# Create directories
# ------------------------------------------------------------

for split in splits:
    (YOLO_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
    (YOLO_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Create hard links
# ------------------------------------------------------------

for split, split_images in splits.items():

    linked = 0
    skipped = 0

    for image in split_images:

        label = LABEL_DIR / f"{image.stem}.txt"

        # Every image should have a generated label file.
        if not label.exists():
            skipped += 1
            continue

        image_target = YOLO_DIR / "images" / split / image.name
        label_target = YOLO_DIR / "labels" / split / label.name

        if not image_target.exists():
            os.link(image, image_target)

        if not label_target.exists():
            label_target.write_bytes(label.read_bytes())

        linked += 1

    print(f"{split}: {linked} images, {skipped} skipped")

print()
print("=" * 50)
print("SEACLEAR YOLO SPLIT CREATED")
print("=" * 50)
print("Total source images:", total)
print("Train:", len(splits["train"]))
print("Val:", len(splits["val"]))
print("Test:", len(splits["test"]))
print("Location:", YOLO_DIR)
