#!/usr/bin/env python
"""Download already-computed public LSG case dumps from Figshare.

Usage (from project root):
  python scripts/download_published_benchmarks.py --dataset python_data
  python scripts/download_published_benchmarks.py --dataset carlisle
  python scripts/download_published_benchmarks.py --dataset comparison_results

Figshare redirects to University of Melbourne object storage. Follow the
signed Location URL (a bare ndownloader GET can yield an empty file).
Do not use urllib HEAD against ndownloader; use curl -sI with a short UA.

Signed object-storage URLs expire in seconds. Never retry the same signed
URL after a stall (curl --retry-all-errors caused a Carlisle resume to
lose progress). Refresh Location via curl -sI on each attempt.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

DATASETS = {
    "python_data": {
        "file_id": "44120348",
        "name": "Python_data.zip",
        "bytes": 108090,
        "md5": "e00ee95a1d17bdc6d950f70dba8fbb5f",
        "dest": "data/external/carlisle/Python_data.zip",
    },
    "carlisle": {
        "file_id": "44120405",
        "name": "Carlisle.zip",
        "bytes": 9603961435,
        "md5": "5b4bf7b6007d858a67050fdecc7e6b5f",
        "dest": "data/external/carlisle/Carlisle.zip",
    },
    "comparison_results": {
        "file_id": "44120360",
        "name": "Comparison_results.zip",
        "bytes": 279586627,
        "md5": "a34de5b89811804d8baa8c6bfb11ef7f",
        "dest": "data/external/carlisle/Comparison_results.zip",
    },
    "chowilla": {
        "file_id": "44120567",
        "name": "Chowilla.zip",
        "bytes": 31986950697,
        "md5": "16e3f4d2b8514b1493a1d78af2751707",
        "dest": "data/external/chowilla/Chowilla.zip",
    },
    "burnett": {
        "file_id": "44120564",
        "name": "BurnettRV.zip",
        "bytes": 31986950697,
        "md5": "93df54d5bb54e9b23a09e648648146d8",
        "dest": "data/external/burnett/BurnettRV.zip",
    },
}

# Short UA: a full Chrome UA can trigger Figshare/AWS WAF (HTTP 202 challenge).
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def signed_url(file_id: str) -> str:
    """Resolve Figshare ndownloader to a signed object-storage URL."""
    nd = f"https://ndownloader.figshare.com/files/{file_id}"
    curl = "curl.exe" if sys.platform.startswith("win") else "curl"
    proc = None
    for attempt in range(1, 6):
        proc = subprocess.run(
            [curl, "-sI", "-A", _UA, nd],
            capture_output=True,
            text=True,
            check=False,
        )
        loc = None
        for line in proc.stdout.splitlines():
            if line.lower().startswith("location:"):
                loc = line.split(":", 1)[1].strip()
        if loc:
            return loc
        print(f"[download] no Location (attempt {attempt}/5); retrying")
        time.sleep(2)
    raise SystemExit(
        f"no Location header for {nd} (curl exit {proc.returncode})\n{proc.stdout}"
    )


def md5_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.md5()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def download(dataset: str) -> Path:
    meta = DATASETS[dataset]
    dest = _ROOT / meta["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    expected = int(meta["bytes"])
    if dest.exists() and dest.stat().st_size == expected:
        print(f"[download] already complete: {dest} ({expected} bytes)")
        return dest

    print(f"[download] {meta['name']} -> {dest}")
    curl = "curl.exe" if sys.platform.startswith("win") else "curl"
    last_code = None
    size = dest.stat().st_size if dest.exists() else 0
    for attempt in range(1, 9):
        url = signed_url(str(meta["file_id"]))
        have = dest.stat().st_size if dest.exists() else 0
        print(f"[download] attempt {attempt}/8 from byte {have}")
        cmd = [
            curl,
            "-L",
            "--http1.1",
            "-A",
            _UA,
            "--speed-limit",
            "1024",
            "--speed-time",
            "60",
            "-C",
            "-",
            "-o",
            str(dest),
            url,
        ]
        proc = subprocess.run(cmd, check=False)
        last_code = proc.returncode
        size = dest.stat().st_size if dest.exists() else 0
        if last_code == 0 and size == expected:
            print(f"[download] ok {size} bytes")
            return dest
        print(
            f"[download] curl={last_code} size={size}/{expected}; "
            "refreshing signed URL"
        )
        time.sleep(3)
    raise SystemExit(f"download incomplete: curl={last_code} size={size}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        choices=tuple(DATASETS),
        default="carlisle",
    )
    parser.add_argument(
        "--verify-md5",
        action="store_true",
        help="Hash the file after download (slow for multi-GB zips)",
    )
    args = parser.parse_args()
    path = download(args.dataset)
    if args.verify_md5:
        got = md5_file(path)
        want = DATASETS[args.dataset]["md5"]
        if got != want:
            raise SystemExit(f"md5 mismatch: {got} != {want}")
        print(f"[download] md5 ok {got}")


if __name__ == "__main__":
    main()
