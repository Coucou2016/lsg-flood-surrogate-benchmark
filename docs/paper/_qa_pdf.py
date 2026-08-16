"""PDF/HTML visual QA notes written to docs/paper/_qa_report.txt"""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

root = Path(__file__).resolve().parent
pdf = root / "manuscript.pdf"
html = root / "manuscript.html"
out = root / "_qa_report.txt"

r = PdfReader(str(pdf))
lines = []
lines.append(f"pdf_pages={len(r.pages)}")
lines.append(f"pdf_bytes={pdf.stat().st_size}")
lines.append(f"html_bytes={html.stat().st_size}")

blank = []
for i, p in enumerate(r.pages):
    t = (p.extract_text() or "").strip()
    lines.append(f"page_{i+1:02d}_chars={len(t)}")
    if len(t) < 40:
        blank.append(i + 1)

lines.append(f"near_blank_pages={blank}")

# search for placeholders
joined = "\n".join((p.extract_text() or "") for p in r.pages)
lines.append(f"contains_dai_buchong={('待补充' in joined)}")
lines.append(f"contains_wei_yunxing={('未运行' in joined)}")
lines.append(f"contains_Abstract={'Abstract' in joined}")
lines.append(f"contains_Figure={'Figure' in joined or 'figure' in joined.lower()}")
lines.append(f"contains_O1={'O1' in joined}")
lines.append(f"title_ok={'spatial localization' in joined.lower()}")

# first page sample (unicode-safe file)
lines.append("--- page1_sample ---")
lines.append((r.pages[0].extract_text() or "")[:800])
lines.append("--- page_mid_sample ---")
mid = len(r.pages) // 2
lines.append((r.pages[mid].extract_text() or "")[:800])
lines.append("--- page_last_sample ---")
lines.append((r.pages[-1].extract_text() or "")[:800])

out.write_text("\n".join(lines), encoding="utf-8")
print(out)
print("pages", len(r.pages), "blanks", blank)
