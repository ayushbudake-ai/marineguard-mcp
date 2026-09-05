from pathlib import Path
import os
import yaml

REPO = Path(__file__).resolve().parent

OUT = REPO / "data" / "processed" / "marineguard"
CLASS_FILE = REPO / "marineguard_classes.yaml"

# ------------------------------------------------------------
# Unified 50-class taxonomy
# ------------------------------------------------------------

with open(CLASS_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

CLASSES = {
    int(k): v
    for k, v in config["classes"].items()
}

NAME_TO_ID = {
    name: class_id
    for class_id, name in CLASSES.items()
}

# ------------------------------------------------------------
# Source dataset mappings
# ------------------------------------------------------------

FLS_MAP = config["mapping"]["fls"]
UATD_MAP = config["mapping"]["uatd"]

SOURCE_CONFIG = {
    "fls": {
        "images": REPO / "data" / "processed" / "fls" / "images",
        "labels": REPO / "data" / "processed" / "fls" / "labels",
        "class_names": [
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
        ],
        "mapping": FLS_MAP,
        "prefix": "fls_",
    },

    "uatd": {
        "images": REPO / "data" / "raw" / "uatd" / "UATD_Training" / "yolo" / "images",
        "labels": REPO / "data" / "raw" / "uatd" / "UATD_Training" / "yolo" / "labels",
        "class_names": [
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
        ],
        "mapping": UATD_MAP,
        "prefix": "uatd_",
    },

    "seaclear": {
        "images": REPO / "data" / "raw" / "seaclear" / "yolo" / "images",
        "labels": REPO / "data" / "raw" / "seaclear" / "yolo" / "labels",
        "class_names": None,
        "mapping": None,
        "prefix": "seaclear_",
    },
}

# ------------------------------------------------------------
# Create output folders
# ------------------------------------------------------------

for split in ["train", "val", "test"]:
    (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Convert a source label file into unified 50-class IDs
# ------------------------------------------------------------

def convert_label_file(source_label, dataset_name):
    if dataset_name == "seaclear":
        # SeaClear labels already use the unified 50-class IDs.
        return source_label.read_text(encoding="utf-8")

    cfg = SOURCE_CONFIG[dataset_name]
    class_names = cfg["class_names"]
    mapping = cfg["mapping"]

    output = []

    for line in source_label.read_text(encoding="utf-8").splitlines():

        parts = line.split()

        if len(parts) != 5:
            continue

        source_id = int(parts[0])

        if source_id < 0 or source_id >= len(class_names):
            continue

        source_name = class_names[source_id]
        target_name = mapping[source_name]
        target_id = NAME_TO_ID[target_name]

        output.append(
            f"{target_id} "
            f"{parts[1]} "
            f"{parts[2]} "
            f"{parts[3]} "
            f"{parts[4]}"
        )

    return "\n".join(output)


# ------------------------------------------------------------
# Build combined dataset
# ------------------------------------------------------------

stats = {
    "fls": {"train": 0, "val": 0, "test": 0},
    "uatd": {"train": 0, "val": 0, "test": 0},
    "seaclear": {"train": 0, "val": 0, "test": 0},
}

for dataset_name, cfg in SOURCE_CONFIG.items():

    print()
    print("=" * 60)
    print("PROCESSING:", dataset_name.upper())
    print("=" * 60)

    for split in ["train", "val", "test"]:

        image_dir = cfg["images"] / split
        label_dir = cfg["labels"] / split

        images = list(image_dir.glob("*"))

        for image in images:

            if not image.is_file():
                continue

            label = label_dir / f"{image.stem}.txt"

            if not label.exists():
                continue

            # Prefix prevents filename collisions between datasets.
            new_name = cfg["prefix"] + image.name

            image_target = OUT / "images" / split / new_name
            label_target = OUT / "labels" / split / (
                cfg["prefix"] + image.stem + ".txt"
            )

            # Hard-link image -- no second physical copy.
            if not image_target.exists():
                os.link(image, image_target)

            # Convert/write unified label.
            unified_labels = convert_label_file(
                label,
                dataset_name
            )

            if unified_labels.strip():
                label_target.write_text(
                    unified_labels,
                    encoding="utf-8"
                )
                stats[dataset_name][split] += 1
            else:
                # Remove image if there are no usable labels.
                if image_target.exists():
                    image_target.unlink()

        print(
            f"{split}: "
            f"{stats[dataset_name][split]} usable images"
        )

# ------------------------------------------------------------
# Create final data.yaml
# ------------------------------------------------------------

yaml_data = {
    "path": str(OUT).replace("\\", "/"),
    "train": "images/train",
    "val": "images/val",
    "test": "images/test",
    "names": CLASSES,
}

with open(OUT / "data.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(
        yaml_data,
        f,
        sort_keys=False,
        allow_unicode=True
    )

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print()
print("=" * 60)
print("MARINEGUARD COMBINED DATASET CREATED")
print("=" * 60)

for dataset_name in stats:
    print()
    print(dataset_name.upper())
    print("  Train:", stats[dataset_name]["train"])
    print("  Val:  ", stats[dataset_name]["val"])
    print("  Test: ", stats[dataset_name]["test"])

print()
print("OUTPUT:", OUT)
print("CLASSES:", len(CLASSES))
print()
print("Images were hard-linked; they were NOT duplicated.")
