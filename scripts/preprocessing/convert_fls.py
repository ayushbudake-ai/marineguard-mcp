import json
import random
import shutil
from pathlib import Path
from PIL import Image

# ============================================================
# PATHS
# ============================================================

REPO = Path(__file__).resolve().parent

SOURCE_DIR = (
    REPO
    / "data"
    / "raw"
    / "fls"
    / "marine-debris-watertank-release-1.0"
    / "marine-debris-watertank-release"
    / "fls-images"
)

OUTPUT_DIR = REPO / "data" / "processed" / "fls"

ANNOTATION_FILE = SOURCE_DIR / "annotations.json"

# ============================================================
# FLS CLASS MAPPING
# ============================================================

CLASSES = [
    "bottle",
    "can",
    "chain",
    "drink-carton",
    "hook",
    "propeller",
    "shampoo-bottle",
    "standing-bottle",
    "tire",
    "valve",
]

CLASS_TO_ID = {name: i for i, name in enumerate(CLASSES)}

# ============================================================
# TRAIN / VAL / TEST SPLIT
# ============================================================

TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
TEST_RATIO = 0.10

SEED = 42

# ============================================================
# CREATE OUTPUT DIRECTORIES
# ============================================================

for split in ["train", "val", "test"]:
    (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

# ============================================================
# LOAD ANNOTATIONS
# ============================================================

if not ANNOTATION_FILE.exists():
    raise FileNotFoundError(f"Annotation file not found: {ANNOTATION_FILE}")

with open(ANNOTATION_FILE, "r", encoding="utf-8") as f:
    annotations = json.load(f)

image_files = [
    SOURCE_DIR / name
    for name in annotations.keys()
    if (SOURCE_DIR / name).exists()
]

print(f"Found {len(image_files)} annotated images.")

# ============================================================
# SHUFFLE + SPLIT
# ============================================================

random.seed(SEED)
random.shuffle(image_files)

total = len(image_files)

train_end = int(total * TRAIN_RATIO)
val_end = train_end + int(total * VAL_RATIO)

splits = {
    "train": image_files[:train_end],
    "val": image_files[train_end:val_end],
    "test": image_files[val_end:],
}

print()
print("DATASET SPLIT")
print("----------------")
print("Train:", len(splits["train"]))
print("Val  :", len(splits["val"]))
print("Test :", len(splits["test"]))
print("Total:", sum(len(v) for v in splits.values()))

# ============================================================
# CONVERT ONE IMAGE
# ============================================================

def convert_image(src_path: Path, split: str):
    filename = src_path.name

    image_annotations = annotations[filename]
    boxes = image_annotations.get("bounding-boxes", [])

    # Read image size
    with Image.open(src_path) as img:
        width, height = img.size

    yolo_lines = []

    for box in boxes:
        class_name = box["class"]

        if class_name not in CLASS_TO_ID:
            raise ValueError(
                f"Unknown class '{class_name}' in {filename}"
            )

        class_id = CLASS_TO_ID[class_name]

        x = box["top-left-x"]
        y = box["top-left-y"]
        w = box["width"]
        h = box["height"]

        # Convert top-left format to YOLO center format
        center_x = x + (w / 2)
        center_y = y + (h / 2)

        # Normalize to 0-1
        center_x /= width
        center_y /= height
        w /= width
        h /= height

        # Extra safety check
        if not (
            0 <= center_x <= 1
            and 0 <= center_y <= 1
            and 0 < w <= 1
            and 0 < h <= 1
        ):
            raise ValueError(
                f"Invalid YOLO box generated for {filename}: "
                f"{center_x}, {center_y}, {w}, {h}"
            )

        yolo_lines.append(
            f"{class_id} "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{w:.6f} "
            f"{h:.6f}"
        )

    # Copy image
    output_image = OUTPUT_DIR / "images" / split / filename
    shutil.copy2(src_path, output_image)

    # Create label file
    label_name = src_path.stem + ".txt"
    output_label = OUTPUT_DIR / "labels" / split / label_name

    with open(output_label, "w", encoding="utf-8") as f:
        f.write("\n".join(yolo_lines))


# ============================================================
# PROCESS DATASET
# ============================================================

processed = 0

for split, files in splits.items():
    print(f"\nProcessing {split}...")

    for image_path in files:
        convert_image(image_path, split)
        processed += 1

print()
print("========================================")
print("FLS CONVERSION COMPLETE")
print("========================================")
print("Images processed:", processed)
print()
print("Output:")
print(OUTPUT_DIR)
print()
print("Classes:")

for class_id, class_name in enumerate(CLASSES):
    print(f"{class_id}: {class_name}")

print()
print("IMPORTANT:")
print("Original FLS images are preserved.")
print("No resizing or augmentation was performed.")
print("Only the annotations were converted to YOLO format.")