#!/usr/bin/env python3
"""Secret / credential scan before public push."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"I:\Projects\_publish_lsg-flood-surrogate-benchmark")

# Patterns that are almost always secrets (high confidence)
PATTERNS = [
    (re.compile(r"(?i)-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"), "PEM private key"),
    (re.compile(r"(?i)github_pat_[A-Za-z0-9_]{20,}"), "GitHub PAT"),
    (re.compile(r"(?i)ghp_[A-Za-z0-9]{20,}"), "GitHub classic token"),
    (re.compile(r"(?i)gho_[A-Za-z0-9]{20,}"), "GitHub OAuth token"),
    (re.compile(r"(?i)sk-[A-Za-z0-9]{20,}"), "OpenAI-like secret key"),
    (re.compile(r"(?i)AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"(?i)xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"), "key=value literal"),
    # MinerU / OpenXLab JWT-style tokens (never commit). Assembled so this
    # source file does not contain a contiguous JWT header substring.
    (re.compile("eyJ" + "0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ" + r"\."), "MinerU/OpenXLab JWT"),
    (re.compile(r"(?i)mineru[_-]?token\s*[:=]\s*['\"]?[A-Za-z0-9._\-]{40,}"), "MinerU token assignment"),
]

SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache"}
# Binary / large / expected base64-heavy docs
SKIP_SUFFIX = {".pdf", ".png", ".npz", ".npz5", ".h5", ".zip", ".pkl", ".pt", ".ckpt", ".npz"}
# manuscript.html embeds SVG as data URIs — skip deep scan of huge HTML embeds
MAX_BYTES = 5_000_000


def tracked_or_all_files() -> list[Path]:
    # Prefer git status + tracked + untracked that are about to be added
    out = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--others", "--cached", "--exclude-standard"],
        text=False,
    )
    names = [n.decode("utf-8", "replace") for n in out.split(b"\0") if n]
    return [ROOT / n for n in names]


def main() -> int:
    hits: list[str] = []
    scanned = 0
    for path in tracked_or_all_files():
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIX:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_BYTES:
            continue
        # Skip huge HTML with embedded figures (data URIs look like secrets to naive scanners)
        if path.suffix.lower() == ".html" and size > 500_000:
            # Still check for PEM / token substrings without loading full as text if possible
            head = path.read_bytes()[:200_000]
            text = head.decode("utf-8", "replace")
        else:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
        scanned += 1
        for rx, label in PATTERNS:
            m = rx.search(text)
            if m:
                rel = path.relative_to(ROOT)
                hits.append(f"{rel}: {label} @ {m.start()}")
    print(f"scanned_files={scanned}")
    if hits:
        print("SECRET_SCAN_FAIL")
        for h in hits:
            print(" -", h)
        return 1
    print("SECRET_SCAN_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
