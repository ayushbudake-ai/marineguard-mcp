from pathlib import Path

ROOT = Path(r"data\processed\marineguard\labels\train")

FILES = [
    "seaclear_Cam1_16_23_22_10_11_2020.mp4_00574.txt",
    "seaclear_Cam1_16_26_03_10_11_2020.mp4_02419.txt",
    "seaclear_Cam1_16_26_03_10_11_2020.mp4_02425.txt",
    "seaclear_Cam1_16_26_03_10_11_2020.mp4_02427.txt",
]

for name in FILES:
    path = ROOT / name

    text = path.read_text(encoding="utf-8")

    # Remove the literal characters backslash + n.
    text = text.replace("\\n", "")

    # Remove extra blank space and put exactly one real newline
    # at the end of the label file.
    text = text.strip() + "\n"

    path.write_text(text, encoding="utf-8")

    print("Fixed:", name)

print("DONE")
