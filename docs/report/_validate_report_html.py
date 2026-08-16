"""Quick self-containment checks for report.html."""
from __future__ import annotations

import re
from pathlib import Path

HTML = Path(__file__).resolve().parent / "report.html"
h = HTML.read_text(encoding="utf-8")
errs: list[str] = []
if re.search(r"<script[^>]+src=['\"]https?://", h, re.I):
    errs.append("external script")
if re.search(r"<link[^>]+href=['\"]https?://", h, re.I):
    errs.append("external link")
for needle in ("cdn.jsdelivr", "unpkg.com", "cdnjs.cloudflare"):
    if needle in h:
        errs.append(f"cdn:{needle}")
if "<style>" not in h:
    errs.append("missing internal css")
if "fig06" not in h:
    errs.append("missing fig06")
print(f"size_bytes={HTML.stat().st_size}")
print(f"figure_embed_count={h.count('figure-embed')}")
if errs:
    print("FAIL")
    for e in errs:
        print(" -", e)
    raise SystemExit(1)
print("PASS")
