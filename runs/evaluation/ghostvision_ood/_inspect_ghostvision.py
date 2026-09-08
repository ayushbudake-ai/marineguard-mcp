"""Read-only GhostVision inspection. Does not modify source files."""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from PIL import Image

GV = Path(r"C:\MarineGuard-SSS\GhostVision")
SPLITS = ("train", "valid", "test")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def md5_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main() -> None:
    report: dict = {
        "root": str(GV),
        "root_exists": GV.exists(),
        "top_level": sorted(p.name for p in GV.iterdir()) if GV.exists() else [],
        "splits": {},
        "totals": {},
    }
    all_images: list[Path] = []
    hashes: dict[str, list[str]] = {}
    formats = Counter()
    sizes = Counter()
    corrupt: list[str] = []
    unreadable: list[str] = []
    category_counts = Counter()
    images_with_ann = 0
    images_without_ann = 0
    total_boxes = 0
    bbox_format_notes: list[str] = []

    for split in SPLITS:
        d = GV / split
        jsonl = d / "metadata.jsonl"
        images = sorted(
            p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        )
        other = sorted(
            p.name
            for p in d.iterdir()
            if p.is_file() and p.suffix.lower() not in IMAGE_EXTS
        )
        split_cats = Counter()
        split_boxes = 0
        split_with_ann = 0
        split_without_ann = 0
        missing_images = []
        extra_images = set(p.name for p in images)
        rows = 0
        if jsonl.exists():
            with jsonl.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rows += 1
                    rec = json.loads(line)
                    fn = rec["file_name"]
                    extra_images.discard(fn)
                    img_path = d / fn
                    if not img_path.exists():
                        missing_images.append(fn)
                    objs = rec.get("objects") or {}
                    cats = objs.get("category") or []
                    bboxes = objs.get("bbox") or []
                    if cats or bboxes:
                        split_with_ann += 1
                    else:
                        split_without_ann += 1
                    split_boxes += len(bboxes)
                    for c in cats:
                        split_cats[c] += 1
                    if bboxes and not bbox_format_notes:
                        sample = bboxes[0]
                        bbox_format_notes.append(
                            f"sample bbox len={len(sample)} values={sample}"
                        )
        for img in images:
            all_images.append(img)
            try:
                with Image.open(img) as im:
                    im.verify()
                with Image.open(img) as im:
                    formats[im.format or img.suffix.lower()] += 1
                    sizes[(im.size[0], im.size[1])] += 1
            except Exception as exc:  # noqa: BLE001
                corrupt.append(f"{split}/{img.name}: {exc}")
            try:
                digest = md5_file(img)
                hashes.setdefault(digest, []).append(f"{split}/{img.name}")
            except Exception as exc:  # noqa: BLE001
                unreadable.append(f"{split}/{img.name}: {exc}")

        category_counts.update(split_cats)
        images_with_ann += split_with_ann
        images_without_ann += split_without_ann
        total_boxes += split_boxes
        report["splits"][split] = {
            "image_count": len(images),
            "jsonl_exists": jsonl.exists(),
            "jsonl_rows": rows,
            "other_files": other,
            "images_with_annotations": split_with_ann,
            "images_without_annotations": split_without_ann,
            "annotation_boxes": split_boxes,
            "categories": dict(split_cats),
            "missing_images_referenced_in_jsonl": missing_images,
            "images_not_in_jsonl": sorted(extra_images),
        }

    dup_groups = {h: names for h, names in hashes.items() if len(names) > 1}
    report["totals"] = {
        "images": len(all_images),
        "image_formats": dict(formats),
        "unique_resolutions": {f"{w}x{h}": n for (w, h), n in sizes.most_common()},
        "resolution_count": len(sizes),
        "corrupt_or_unopenable": corrupt,
        "hash_unreadable": unreadable,
        "duplicate_hash_groups": len(dup_groups),
        "duplicate_examples": {k: v for i, (k, v) in enumerate(dup_groups.items()) if i < 10},
        "annotation_format": "HuggingFace JSONL (metadata.jsonl) with objects.bbox xywh pixel coords and objects.category strings",
        "bbox_sample": bbox_format_notes,
        "images_with_annotations": images_with_ann,
        "images_without_annotations": images_without_ann,
        "total_annotation_boxes": total_boxes,
        "categories": dict(category_counts),
        "existing_splits": list(SPLITS),
    }
    out = Path(r"D:\Marine Drive\marineguard-mcp\runs\evaluation\ghostvision_ood\ghostvision_inspection.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["totals"], indent=2))
    print("SPLITS")
    print(json.dumps(report["splits"], indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
