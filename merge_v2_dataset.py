from pathlib import Path
import shutil

# ============================================================
# MarineGuard V2 Dataset Merge
# V1 + TrashCan
#
# IMPORTANT:
# - V1 data is READ-ONLY
# - Nothing is moved or deleted from V1
# - V2 is created separately
# ============================================================

V1_ROOT = Path("data/processed/marineguard")
TRASHCAN_ROOT = Path("data/processed_v2/trashcan")
V2_ROOT = Path("data/processed_v2/marineguard")

SPLITS = ["train", "val", "test"]


def copy_split(source_root, destination_root, split, prefix):
    """Copy images and labels while preventing filename collisions."""

    source_images = source_root / "images" / split
    source_labels = source_root / "labels" / split

    destination_images = destination_root / "images" / split
    destination_labels = destination_root / "labels" / split

    if not source_images.exists():
        print(f"  No images found: {source_images}")
        return 0

    destination_images.mkdir(parents=True, exist_ok=True)
    destination_labels.mkdir(parents=True, exist_ok=True)

    count = 0

    for image_path in source_images.iterdir():

        if not image_path.is_file():
            continue

        # Prefix guarantees uniqueness between datasets
        new_name = f"{prefix}_{image_path.name}"
        destination_image = destination_images / new_name

        shutil.copy2(image_path, destination_image)

        # Corresponding YOLO label
        label_path = source_labels / f"{image_path.stem}.txt"

        if not label_path.exists():
            print(f"WARNING: Missing label for {image_path.name}")
            continue

        destination_label = destination_labels / f"{prefix}_{image_path.stem}.txt"

        shutil.copy2(label_path, destination_label)

        count += 1

    return count


def count_files(path):
    if not path.exists():
        return 0
    return sum(1 for x in path.iterdir() if x.is_file())


def main():

    print("=" * 60)
    print("MARINEGUARD V2 DATASET MERGE")
    print("=" * 60)

    print("\nV1 source:")
    print(V1_ROOT.resolve())

    print("\nTrashCan source:")
    print(TRASHCAN_ROOT.resolve())

    print("\nV2 destination:")
    print(V2_ROOT.resolve())

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if V2_ROOT.exists():
        print("\nWARNING: V2 destination already exists.")
        print("Delete it manually if you want a completely fresh merge.")
        return

    # --------------------------------------------------------
    # Create V2 directories
    # --------------------------------------------------------

    for split in SPLITS:
        (V2_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
        (V2_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Copy V1
    # --------------------------------------------------------

    print("\n[1/2] Copying V1 dataset...")

    for split in SPLITS:
        copied = copy_split(
            V1_ROOT,
            V2_ROOT,
            split,
            "v1"
        )

        print(f"  {split}: {copied} image/label pairs")

    # --------------------------------------------------------
    # Copy TrashCan
    # --------------------------------------------------------

    print("\n[2/2] Copying TrashCan...")

    for split in ["train", "val"]:
        copied = copy_split(
            TRASHCAN_ROOT,
            V2_ROOT,
            split,
            "trashcan"
        )

        print(f"  {split}: {copied} image/label pairs")

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FINAL V2 DATASET COUNTS")
    print("=" * 60)

    total_images = 0
    total_labels = 0

    for split in SPLITS:

        image_count = count_files(
            V2_ROOT / "images" / split
        )

        label_count = count_files(
            V2_ROOT / "labels" / split
        )

        total_images += image_count
        total_labels += label_count

        print(
            f"{split:5} | "
            f"images: {image_count:5} | "
            f"labels: {label_count:5}"
        )

    print("-" * 60)
    print(
        f"TOTAL | "
        f"images: {total_images:5} | "
        f"labels: {total_labels:5}"
    )

    print("\nExpected:")
    print("Train : 18,717")
    print("Val   :  4,760")
    print("Test  :  1,808")
    print("Total : 25,285")

    if total_images == 25285 and total_labels == 25285:
        print("\nSTATUS: V2 MERGE SUCCESSFUL")
    else:
        print("\nSTATUS: COUNT MISMATCH — DO NOT TRAIN")


if __name__ == "__main__":
    main()