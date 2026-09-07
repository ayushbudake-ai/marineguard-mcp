import json
import shutil
from pathlib import Path

# ============================================================
# TrashCan INSTANCE → MarineGuard 50-class YOLO converter
# ============================================================

TRASHCAN_TO_MARINEGUARD = {
    "rov": 18,
    "plant": 22,

    "animal_fish": 48,
    "animal_starfish": 49,
    "animal_shells": 30,
    "animal_crab": 23,
    "animal_eel": 23,
    "animal_etc": 23,

    "trash_clothing": 36,
    "trash_pipe": 28,
    "trash_bottle": 0,
    "trash_bag": 34,
    "trash_snack_wrapper": 44,
    "trash_can": 1,
    "trash_cup": 32,
    "trash_container": 20,
    "trash_unknown_instance": 27,
    "trash_branch": 42,
    "trash_wreckage": 26,
    "trash_tarp": 19,
    "trash_rope": 31,
    "trash_net": 29,
}

ROOT = Path(__file__).resolve().parent

TRASHCAN_ROOT = (
    ROOT
    / "data"
    / "raw"
    / "trashcan"
    / "dataset"
    / "dataset"
    / "instance_version"
)

OUTPUT_ROOT = ROOT / "data" / "processed_v2" / "trashcan"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def convert_split(split):
    json_path = TRASHCAN_ROOT / f"instances_{split}_trashcan.json"
    image_root = TRASHCAN_ROOT / split

    output_images = OUTPUT_ROOT / "images" / split
    output_labels = OUTPUT_ROOT / "labels" / split

    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"PROCESSING {split.upper()}")
    print(f"{'=' * 60}")

    data = load_json(json_path)

    category_names = {
        category["id"]: category["name"]
        for category in data["categories"]
    }

    images = {
        image["id"]: image
        for image in data["images"]
    }

    annotations_by_image = {}

    for annotation in data["annotations"]:
        image_id = annotation["image_id"]
        annotations_by_image.setdefault(image_id, []).append(annotation)

    converted_images = 0
    copied_images = 0
    written_boxes = 0
    skipped_annotations = 0
    missing_images = 0
    invalid_boxes = 0

    class_counts = {}

    for image_id, image_info in images.items():

        file_name = image_info["file_name"]
        width = image_info["width"]
        height = image_info["height"]

        source_image = image_root / file_name

        if not source_image.exists():
            missing_images += 1
            continue

        yolo_lines = []

        for annotation in annotations_by_image.get(image_id, []):

            category_id = annotation["category_id"]
            category_name = category_names.get(category_id)

            # Unknown category
            if category_name not in TRASHCAN_TO_MARINEGUARD:
                skipped_annotations += 1
                continue

            bbox = annotation.get("bbox")

            if not bbox or len(bbox) != 4:
                skipped_annotations += 1
                invalid_boxes += 1
                continue

            x, y, w, h = bbox

            # Invalid box
            if w <= 0 or h <= 0:
                skipped_annotations += 1
                invalid_boxes += 1
                continue

            # ------------------------------------------------
            # COCO XYWH → YOLO normalized XYWH
            # ------------------------------------------------

            x_center = x + (w / 2)
            y_center = y + (h / 2)

            x_center /= width
            y_center /= height
            w /= width
            h /= height

            # Clamp to valid YOLO range
            x_center = min(max(x_center, 0.0), 1.0)
            y_center = min(max(y_center, 0.0), 1.0)
            w = min(max(w, 0.0), 1.0)
            h = min(max(h, 0.0), 1.0)

            marineguard_id = TRASHCAN_TO_MARINEGUARD[category_name]

            yolo_lines.append(
                f"{marineguard_id} "
                f"{x_center:.6f} "
                f"{y_center:.6f} "
                f"{w:.6f} "
                f"{h:.6f}"
            )

            written_boxes += 1

            class_counts[category_name] = (
                class_counts.get(category_name, 0) + 1
            )

        # Copy image
        destination_image = output_images / file_name
        shutil.copy2(source_image, destination_image)

        copied_images += 1
        converted_images += 1

        # Write YOLO label
        label_path = (
            output_labels
            / Path(file_name).with_suffix(".txt").name
        )

        with open(label_path, "w", encoding="utf-8") as f:
            if yolo_lines:
                f.write("\n".join(yolo_lines) + "\n")

    print("\nRESULTS")
    print("-" * 60)
    print(f"Images in JSON:       {len(images)}")
    print(f"Images converted:     {converted_images}")
    print(f"Images copied:        {copied_images}")
    print(f"Missing images:       {missing_images}")
    print(f"Boxes written:        {written_boxes}")
    print(f"Annotations skipped:  {skipped_annotations}")
    print(f"Invalid boxes:        {invalid_boxes}")

    print("\nCLASS COUNTS")
    print("-" * 60)

    for class_name, count in sorted(class_counts.items()):
        marineguard_id = TRASHCAN_TO_MARINEGUARD[class_name]

        print(
            f"{class_name:25s} "
            f"→ {marineguard_id:2d} "
            f"{count:6d}"
        )

    return {
        "images": converted_images,
        "boxes": written_boxes,
        "skipped": skipped_annotations,
        "invalid_boxes": invalid_boxes,
        "missing": missing_images,
        "class_counts": class_counts,
    }


def main():

    print("=" * 60)
    print("TrashCan INSTANCE → MarineGuard V2")
    print("=" * 60)

    if not TRASHCAN_ROOT.exists():
        raise FileNotFoundError(
            f"TrashCan Instance directory not found:\n"
            f"{TRASHCAN_ROOT}"
        )

    # IMPORTANT:
    # Remove ONLY the previous TrashCan V2 conversion.
    # V1 data/processed is untouched.
    if OUTPUT_ROOT.exists():
        print(f"\nRemoving previous TrashCan conversion:")
        print(OUTPUT_ROOT)
        shutil.rmtree(OUTPUT_ROOT)

    train_stats = convert_split("train")
    val_stats = convert_split("val")

    print("\n" + "=" * 60)
    print("TRASHCAN INSTANCE CONVERSION COMPLETE")
    print("=" * 60)

    print("\nTOTAL")
    print("-" * 60)
    print(
        f"Images: {train_stats['images'] + val_stats['images']}"
    )
    print(
        f"Boxes:  {train_stats['boxes'] + val_stats['boxes']}"
    )
    print(
        f"Skipped: {train_stats['skipped'] + val_stats['skipped']}"
    )

    print("\nOutput:")
    print(OUTPUT_ROOT)

    print("\nMarineGuard V1 was NOT modified:")
    print(ROOT / "data" / "processed")


if __name__ == "__main__":
    main()