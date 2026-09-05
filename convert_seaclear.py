import json
import yaml
from pathlib import Path
from collections import Counter

# ============================================================
# PATHS
# ============================================================

REPO = Path(__file__).resolve().parent

SEACLEAR_DIR = REPO / "data" / "raw" / "seaclear"
JSON_FILE = SEACLEAR_DIR / "dataset.json"
LABEL_DIR = SEACLEAR_DIR / "labels"

LABEL_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# LOAD MARINEGUARD TAXONOMY
# ============================================================

CLASS_FILE = REPO / "marineguard_classes.yaml"

with open(CLASS_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

CLASSES = config["classes"]
SEACLEAR_MAPPING = config["mapping"]["seaclear"]

NAME_TO_ID = {
    name: int(class_id)
    for class_id, name in CLASSES.items()
}

# ============================================================
# LOAD COCO DATASET
# ============================================================

with open(JSON_FILE, "r", encoding="utf-8") as f:
    coco = json.load(f)

images = coco["images"]
annotations = coco["annotations"]
categories = coco["categories"]

category_id_to_name = {
    c["id"]: c["name"]
    for c in categories
}

image_id_to_info = {
    image["id"]: image
    for image in images
}

# ============================================================
# GROUP ANNOTATIONS BY IMAGE
# ============================================================

annotations_by_image = {}

for ann in annotations:
    image_id = ann["image_id"]
    annotations_by_image.setdefault(image_id, []).append(ann)

# ============================================================
# CONVERSION
# ============================================================

total_annotations = 0
valid_annotations = 0
invalid_annotations = 0
unmapped_annotations = 0

class_counts = Counter()

for image in images:

    image_id = image["id"]
    width = image["width"]
    height = image["height"]

    output_lines = []

    for ann in annotations_by_image.get(image_id, []):

        total_annotations += 1

        category_id = ann.get("category_id")

        if category_id not in category_id_to_name:
            print(
                f"WARNING: Unknown category ID {category_id} "
                f"in annotation {ann.get('id')}"
            )
            unmapped_annotations += 1
            continue

        source_class = category_id_to_name[category_id]

        # ----------------------------------------------------
        # Map SeaClear class -> MarineGuard class
        # ----------------------------------------------------

        if source_class not in SEACLEAR_MAPPING:
            print(
                f"WARNING: No mapping for '{source_class}' "
                f"in annotation {ann.get('id')}"
            )
            unmapped_annotations += 1
            continue

        target_class = SEACLEAR_MAPPING[source_class]

        if target_class not in NAME_TO_ID:
            print(
                f"WARNING: Target class '{target_class}' "
                f"not found in unified taxonomy"
            )
            unmapped_annotations += 1
            continue

        # ----------------------------------------------------
        # Get bounding box
        # COCO format:
        # [xmin, ymin, width, height]
        # ----------------------------------------------------

        bbox = ann.get("bbox")

        if not bbox or len(bbox) != 4:
            invalid_annotations += 1
            continue

        xmin, ymin, box_width, box_height = bbox

        xmax = xmin + box_width
        ymax = ymin + box_height

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        if (
            box_width <= 0
            or box_height <= 0
            or xmin < 0
            or ymin < 0
            or xmax > width
            or ymax > height
        ):
            print(
                f"WARNING: Invalid bbox "
                f"image_id={image_id}, "
                f"category={source_class}, "
                f"bbox={bbox}"
            )
            invalid_annotations += 1
            continue

        # ----------------------------------------------------
        # Convert COCO -> YOLO
        # ----------------------------------------------------

        center_x = xmin + box_width / 2
        center_y = ymin + box_height / 2

        center_x /= width
        center_y /= height
        box_width /= width
        box_height /= height

        class_id = NAME_TO_ID[target_class]

        output_lines.append(
            f"{class_id} "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{box_width:.6f} "
            f"{box_height:.6f}"
        )

        valid_annotations += 1
        class_counts[target_class] += 1

    # --------------------------------------------------------
    # Save YOLO label file
    # --------------------------------------------------------

    image_name = Path(image["file_name"]).stem
    label_file = LABEL_DIR / f"{image_name}.txt"

    label_file.write_text(
        "\n".join(output_lines),
        encoding="utf-8"
    )

# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("SEACLEAR COCO -> YOLO CONVERSION COMPLETE")
print("=" * 60)

print(f"Images processed:          {len(images)}")
print(f"Categories:                {len(categories)}")
print(f"Original annotations:      {total_annotations}")
print(f"Valid annotations:         {valid_annotations}")
print(f"Invalid annotations:       {invalid_annotations}")
print(f"Unmapped annotations:      {unmapped_annotations}")

print()
print("MARINEGUARD CLASS DISTRIBUTION")
print("-" * 40)

for class_id, class_name in CLASSES.items():
    print(
        f"{int(class_id):2d}  "
        f"{class_name:<25} "
        f"{class_counts[class_name]}"
    )

print()
print("Labels saved to:")
print(LABEL_DIR)
print()
print("SeaClear images were NOT copied or modified.")
print("Segmentation polygons were intentionally not converted.")
print("Only bounding boxes were converted for the YOLO detection pipeline.")