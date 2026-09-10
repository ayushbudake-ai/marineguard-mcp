import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

# ============================================================
# PATHS
# ============================================================

REPO = Path(__file__).resolve().parent

UATD_DIR = (
    REPO
    / "data"
    / "raw"
    / "uatd"
    / "UATD_Training"
)

ANNOTATIONS_DIR = UATD_DIR / "annotations"
LABELS_DIR = UATD_DIR / "labels"

LABELS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# UATD CLASSES
# ============================================================

CLASSES = [
    "ball",
    "circle cage",
    "cube",
    "cylinder",
    "human body",
    "metal bucket",
    "plane",
    "rov",
    "square cage",
    "tyre",
]

CLASS_TO_ID = {name: i for i, name in enumerate(CLASSES)}

# ============================================================
# CONVERSION
# ============================================================

xml_files = sorted(ANNOTATIONS_DIR.glob("*.xml"))

if not xml_files:
    raise FileNotFoundError(
        f"No XML files found in: {ANNOTATIONS_DIR}"
    )

total_boxes = 0
valid_boxes = 0
invalid_boxes = 0
images_with_no_valid_boxes = 0

class_counts = Counter()

for xml_file in xml_files:

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Image dimensions
    width = int(root.findtext("size/width"))
    height = int(root.findtext("size/height"))

    yolo_lines = []

    for obj in root.findall("object"):

        class_name = obj.findtext("name", "").strip()
        total_boxes += 1

        if class_name not in CLASS_TO_ID:
            print(
                f"WARNING: Unknown class '{class_name}' "
                f"in {xml_file.name} -- skipped"
            )
            invalid_boxes += 1
            continue

        bbox = obj.find("bndbox")

        if bbox is None:
            print(
                f"WARNING: Missing bndbox in {xml_file.name} "
                f"for class '{class_name}' -- skipped"
            )
            invalid_boxes += 1
            continue

        try:
            xmin = int(bbox.findtext("xmin"))
            ymin = int(bbox.findtext("ymin"))
            xmax = int(bbox.findtext("xmax"))
            ymax = int(bbox.findtext("ymax"))
        except (TypeError, ValueError):
            print(
                f"WARNING: Invalid coordinates in "
                f"{xml_file.name} -- skipped"
            )
            invalid_boxes += 1
            continue

        # Validate bounding box
        if not (
            0 <= xmin < xmax <= width
            and 0 <= ymin < ymax <= height
        ):
            print(
                f"WARNING: Invalid box in {xml_file.name}: "
                f"{class_name} "
                f"({xmin}, {ymin}, {xmax}, {ymax}) -- skipped"
            )
            invalid_boxes += 1
            continue

        # Convert Pascal VOC -> YOLO
        box_width = xmax - xmin
        box_height = ymax - ymin

        center_x = xmin + box_width / 2
        center_y = ymin + box_height / 2

        # Normalize
        center_x /= width
        center_y /= height
        box_width /= width
        box_height /= height

        class_id = CLASS_TO_ID[class_name]

        yolo_lines.append(
            f"{class_id} "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{box_width:.6f} "
            f"{box_height:.6f}"
        )

        valid_boxes += 1
        class_counts[class_name] += 1

    # Write one YOLO label file per XML
    label_file = LABELS_DIR / f"{xml_file.stem}.txt"

    if yolo_lines:
        label_file.write_text(
            "\n".join(yolo_lines),
            encoding="utf-8"
        )
    else:
        # No valid objects in this annotation
        label_file.write_text("", encoding="utf-8")
        images_with_no_valid_boxes += 1

# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 50)
print("UATD XML -> YOLO CONVERSION COMPLETE")
print("=" * 50)

print(f"XML files processed:       {len(xml_files)}")
print(f"Total original boxes:      {total_boxes}")
print(f"Valid boxes:               {valid_boxes}")
print(f"Invalid boxes skipped:     {invalid_boxes}")
print(f"Files with no valid boxes: {images_with_no_valid_boxes}")

print()
print("CLASS DISTRIBUTION")
print("-" * 30)

for class_name in CLASSES:
    print(
        f"{class_name:<20} "
        f"{class_counts[class_name]}"
    )

print()
print(f"Labels saved to:")
print(LABELS_DIR)

print()
print("IMPORTANT:")
print("Original UATD images and XML files were NOT modified.")
print("Images were NOT copied.")
print("Only YOLO .txt labels were created.")