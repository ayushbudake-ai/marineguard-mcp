from pathlib import Path

ROOT = Path(__file__).resolve().parent / "data" / "processed_v2" / "marineguard" / "labels"

VALID_CLASSES = set(range(50))

total_boxes = 0
invalid_boxes = 0
invalid_files = 0

print("=" * 55)
print("MARINEGUARD V2 LABEL VALIDATION")
print("=" * 55)

for split in ["train", "val", "test"]:

    split_dir = ROOT / split

    if not split_dir.exists():
        print(f"WARNING: Missing split: {split}")
        continue

    for label_file in split_dir.glob("*.txt"):

        file_has_error = False

        try:
            lines = label_file.read_text().splitlines()

            for line_number, line in enumerate(lines, start=1):

                if not line.strip():
                    continue

                parts = line.split()

                if len(parts) != 5:
                    invalid_boxes += 1
                    file_has_error = True
                    continue

                try:
                    class_id = int(parts[0])
                    x, y, w, h = map(float, parts[1:])
                except ValueError:
                    invalid_boxes += 1
                    file_has_error = True
                    continue

                total_boxes += 1

                if class_id not in VALID_CLASSES:
                    invalid_boxes += 1
                    file_has_error = True
                    continue

                if not all(0 <= value <= 1 for value in [x, y, w, h]):
                    invalid_boxes += 1
                    file_has_error = True
                    continue

                if w <= 0 or h <= 0:
                    invalid_boxes += 1
                    file_has_error = True

        except Exception as e:
            print(f"ERROR: {label_file}: {e}")
            file_has_error = True

        if file_has_error:
            invalid_files += 1

print("\n" + "=" * 55)
print(f"Total boxes:   {total_boxes}")
print(f"Invalid boxes: {invalid_boxes}")
print(f"Invalid files: {invalid_files}")
print("=" * 55)

if invalid_boxes == 0 and invalid_files == 0:
    print("STATUS: ALL VALID")
else:
    print("STATUS: VALIDATION FAILED")
