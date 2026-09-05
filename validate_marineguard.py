from pathlib import Path

ROOT = Path(r"data\processed\marineguard\labels")

bad = []
total = 0

for label_file in ROOT.rglob("*.txt"):
    lines = label_file.read_text(encoding="utf-8").splitlines()

    for line_number, line in enumerate(lines, start=1):
        parts = line.split()
        total += 1

        if len(parts) != 5:
            bad.append((label_file.name, line_number, line, "wrong field count"))
            continue

        try:
            class_id = int(parts[0])
            values = [float(x) for x in parts[1:]]
        except ValueError:
            bad.append((label_file.name, line_number, line, "non-numeric value"))
            continue

        if not 0 <= class_id < 50:
            bad.append((label_file.name, line_number, line, "invalid class id"))
            continue

        if any(x < 0 or x > 1 for x in values):
            bad.append((label_file.name, line_number, line, "value outside 0-1"))
            continue

print("=" * 50)
print("MARINEGUARD LABEL VALIDATION")
print("=" * 50)
print("Total boxes:", total)
print("Invalid boxes:", len(bad))

if bad:
    print("\nFIRST INVALID ENTRIES:")
    for item in bad[:20]:
        print(item)
    print("\nSTATUS: CHECK DATASET")
else:
    print("STATUS: ALL VALID")