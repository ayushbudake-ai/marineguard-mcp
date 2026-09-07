from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent / "data" / "processed_v2" / "marineguard" / "labels"

CLASS_NAMES = {
    0: "bottle",
    1: "can",
    2: "chain",
    3: "drink-carton",
    4: "hook",
    5: "propeller",
    6: "shampoo-bottle",
    7: "standing-bottle",
    8: "tire",
    9: "valve",
    10: "metal-bucket",
    11: "ball",
    12: "cube",
    13: "cylinder",
    14: "circle-cage",
    15: "square-cage",
    16: "human-body",
    17: "plane",
    18: "rov",
    19: "tarp",
    20: "plastic-container",
    21: "cement-tube",
    22: "plant",
    23: "animal",
    24: "sponge",
    25: "glass-bottle",
    26: "metal-wreckage",
    27: "unknown-object",
    28: "plastic-pipe",
    29: "net",
    30: "shell",
    31: "rope",
    32: "plastic-cup",
    33: "brick",
    34: "plastic-bag",
    35: "sanitary-waste",
    36: "clothing",
    37: "ceramic-cup",
    38: "rubber-boot",
    39: "glass-jar",
    40: "rov-cable",
    41: "rov-part",
    42: "wood-branch",
    43: "furniture",
    44: "snack-wrapper",
    45: "plastic-lid",
    46: "cardboard",
    47: "metal-cable",
    48: "fish",
    49: "starfish",
}

for split in ["train", "val", "test"]:

    counter = Counter()

    label_dir = ROOT / split

    for label_file in label_dir.glob("*.txt"):

        for line in label_file.read_text().splitlines():

            if not line.strip():
                continue

            class_id = int(line.split()[0])
            counter[class_id] += 1

    print("\n" + "=" * 65)
    print(f"{split.upper()} CLASS DISTRIBUTION")
    print("=" * 65)

    total = sum(counter.values())

    for class_id in range(50):
        count = counter[class_id]
        name = CLASS_NAMES[class_id]

        percentage = (count / total * 100) if total else 0

        print(
            f"{class_id:2d} | "
            f"{name:<20} | "
            f"{count:6d} | "
            f"{percentage:6.2f}%"
        )

    print("-" * 65)
    print(f"TOTAL BOXES: {total}")

print("\nSTATUS: DISTRIBUTION CHECK COMPLETE")