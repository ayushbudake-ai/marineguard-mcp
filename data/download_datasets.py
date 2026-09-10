"""
Concurrent downloader for MarineGuard datasets with progress reporting and resume support.
"""

import os
import sys
import time
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

REPO = Path(__file__).resolve().parents[1]

DOWNLOADS = [
    {
        "name": "TrashCan 1.0",
        "url": "https://conservancy.umn.edu/bitstream/handle/11299/214865/dataset.zip?sequence=12&isAllowed=y",
        "dest": REPO / "data" / "raw" / "trashcan" / "dataset.zip",
        "expected_size": 552718336,
    },
    {
        "name": "SeaClear",
        "url": "https://data.4tu.nl/file/4f1dff25-e157-4399-a5d4-478055461689/e1240a2e-915e-4858-93ab-c004b26b5a5f",
        "dest": REPO / "data" / "raw" / "seaclear" / "seaclear.rar",
        "expected_size": 1711829309,
    },
    {
        "name": "UATD Training",
        "url": "https://ndownloader.figshare.com/files/37883163",
        "dest": REPO / "data" / "raw" / "uatd" / "UATD_Training.zip",
        "expected_size": 3869955319,
    },
    {
        "name": "UATD Test 1",
        "url": "https://ndownloader.figshare.com/files/37857276",
        "dest": REPO / "data" / "raw" / "uatd" / "UATD_Test_1.zip",
        "expected_size": 421934004,
    },
    {
        "name": "UATD Test 2",
        "url": "https://ndownloader.figshare.com/files/37857279",
        "dest": REPO / "data" / "raw" / "uatd" / "UATD_Test_2.zip",
        "expected_size": 424608381,
    },
]


def download_file(item):
    dest = Path(item["dest"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    name = item["name"]
    url = item["url"]

    downloaded = 0
    if dest.exists():
        downloaded = dest.stat().st_size
        if item.get("expected_size") and downloaded == item["expected_size"]:
            print(f"[{name}] Already fully downloaded ({downloaded / 1024 / 1024:.1f} MB).")
            return

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if downloaded > 0:
        headers["Range"] = f"bytes={downloaded}-"
        print(f"[{name}] Resuming from {downloaded / 1024 / 1024:.1f} MB...")
    else:
        print(f"[{name}] Starting download from {url}...")

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "ab" if downloaded > 0 else "wb") as f:
            total = int(resp.headers.get("Content-Length", 0)) + downloaded
            chunk_size = 1024 * 1024  # 1MB
            last_print = time.time()
            curr = downloaded

            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                curr += len(chunk)
                if time.time() - last_print > 5:
                    pct = (curr / total * 100) if total > 0 else 0
                    print(f"[{name}] {curr / 1024 / 1024:.1f} / {total / 1024 / 1024:.1f} MB ({pct:.1f}%)")
                    last_print = time.time()

        print(f"[{name}] Completed download successfully ({curr / 1024 / 1024:.1f} MB).")
    except Exception as exc:
        print(f"[{name}] Download error: {exc}")
        raise


if __name__ == "__main__":
    print(f"Starting downloads for {len(DOWNLOADS)} datasets...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(download_file, item) for item in DOWNLOADS]
        for f in futures:
            f.result()
    print("All downloads finished!")
