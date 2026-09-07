from pathlib import Path

ROOT = Path(__file__).resolve().parent / "data" / "processed_v2" / "trashcan" / "labels"

bad = []
total = 0
files = 0

for label_file in ROOT.rglob("*.txt"):
    files += 1

    lines = label_file.read_text(encoding="utf-8").splitlines()

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        parts = line.split()
        total += 1

        if len(parts) != 5:
            bad.append(
                (label_file.name, line_number, line, "wrong field count")
            )
            continue

        try:
            class_id = int(parts[0])
            values = [float(x) for x in parts[1:]]
        except ValueError:
            bad.append(
                (label_file.name, line_number, line, "non-numeric value")
            )
            continue

        if not 0 <= class_id < 50:
            bad.append(
                (label_file.name, line_number, line, "invalid class id")
            )
            continue

        if any(x < 0 or x > 1 for x in values):
            bad.append(
                (label_file.name, line_number, line, "value outside 0-1")
            )
            continue

        # YOLO width/height must be > 0
        if values[2] <= 0 or values[3] <= 0:
            bad.append(
                (label_file.name, line_number, line, "zero/negative width or height")
            )
            continue

print("=" * 55)
print("TRASHCAN V2 LABEL VALIDATION")
print("=" * 55)
print("Label files:", files)
print("Total boxes:", total)
print("Invalid boxes:", len(bad))

if bad:
    print("\nFIRST INVALID ENTRIES:")
    for item in bad[:20]:
        print(item)

    print("\nSTATUS: CHECK DATASET")
else:
    print("\nSTATUS: ALL VALID")
