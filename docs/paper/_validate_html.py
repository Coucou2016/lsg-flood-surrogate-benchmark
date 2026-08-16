"""Validate manuscript.html embedding and section requirements."""
from __future__ import annotations

import pathlib
import re
import sys

HTML = pathlib.Path(__file__).resolve().parent / "manuscript.html"
text = HTML.read_text(encoding="utf-8")

errors: list[str] = []

if not text.lstrip().startswith("<!DOCTYPE html>"):
    errors.append("missing DOCTYPE")
if "<html" not in text or "<head>" not in text or "<body>" not in text:
    errors.append("missing html/head/body")
if "<style>" not in text:
    errors.append("missing internal style")

# external assets
if re.search(r"<link[^>]+stylesheet", text, re.I):
    errors.append("external stylesheet link found")
if re.search(r"<script[^>]+src=", text, re.I):
    errors.append("external script found")
if "cdn." in text.lower() or "fonts.googleapis" in text.lower():
    errors.append("CDN/network font reference found")
if "file://" in text:
    errors.append("file:// URI found")

imgs = re.findall(r"<img\b[^>]*>", text, flags=re.I)
if not imgs:
    errors.append("no img tags")
for tag in imgs:
    m = re.search(r'src="([^"]*)"', tag)
    if not m:
        errors.append(f"img without src: {tag[:80]}")
        continue
    src = m.group(1)
    if not src.startswith("data:"):
        errors.append(f"non-data img src: {src[:120]}")
    if src.startswith("http") or src.startswith("/") or "\\" in src or src.startswith("outputs"):
        errors.append(f"local/network img src: {src[:120]}")

required = [
    "Abstract",
    "Introduction",
    "Methods",
    "Results",
    "Discussion",
    "Limitations",
    "Conclusions",
    "Data and code availability",
    "Author contributions",
    "Competing interests",
    "References",
]
for sec in required:
    if sec not in text:
        errors.append(f"missing section: {sec}")

print(f"size_bytes={HTML.stat().st_size}")
print(f"img_count={len(imgs)}")
print(f"data_uri_imgs={sum(1 for t in imgs if 'src=\"data:' in t)}")
if errors:
    print("FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("PASS")
