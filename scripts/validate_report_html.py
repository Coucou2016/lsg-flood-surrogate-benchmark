#!/usr/bin/env python3
"""Validate self-contained report.html constraints."""
from __future__ import annotations

import re
import sys
from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "docs" / "report" / "report.html"
MD = Path(__file__).resolve().parents[1] / "docs" / "report" / "report.md"

REQUIRED_SECTION_HINTS = [
    "摘要与执行概要",
    "研究背景与目标",
    "文献与科学缺口",
    "数据来源与案例",
    "方法学基础",
    "完整研究过程",
    "数据摄取与对齐",
    "EXT+WSE",
    "SGPR",
    "层次残差",
    "不确定性量化",
    "O1–O4",
    "实验设计",
    "分案例结果",
    "跨案例比较",
    "等容量对照",
    "详细图件解读",
    "讨论与因果",
    "创新点",
    "可复现性",
    "局限性",
    "未来工作",
    "结论",
    "数据与代码可用性",
    "参考文献",
    "附录",
    "范围边界",
]


def main() -> int:
    text = HTML.read_text(encoding="utf-8")
    errors: list[str] = []

    if not text.lstrip().startswith("<!DOCTYPE html>"):
        errors.append("missing DOCTYPE")
    for tag in ("<html", "<head", "<style", "<body", "</html>"):
        if tag not in text:
            errors.append(f"missing {tag}")

    # external network / file refs
    if re.search(r'<link[^>]+href=["\']https?://', text, re.I):
        errors.append("external CSS link")
    if re.search(r'<script[^>]+src=["\']https?://', text, re.I):
        errors.append("external JS script")
    if re.search(r'src=["\']https?://', text, re.I):
        errors.append("http(s) src")
    if re.search(r'src=["\']file://', text, re.I):
        errors.append("file:// src")
    # img src must be data: or absent (we use inline svg)
    for m in re.finditer(r'<img\b[^>]*>', text, re.I):
        tag = m.group(0)
        if 'src="' in tag or "src='" in tag:
            if not re.search(r'src=["\']data:', tag, re.I):
                errors.append(f"non-data img: {tag[:120]}")

    # relative path images like outputs/
    if re.search(r'src=["\'][^"\']*outputs/', text):
        errors.append("relative outputs/ image path in HTML")

    for hint in REQUIRED_SECTION_HINTS:
        if hint not in text:
            errors.append(f"missing section hint: {hint}")

    if not MD.exists():
        errors.append("report.md missing")
    else:
        md = MD.read_text(encoding="utf-8")
        for hint in ("详细图件解读", "范围边界", "O1–O4", "fig01_study_domains"):
            if hint not in md:
                errors.append(f"md missing: {hint}")

    # count inline svgs
    n_svg = len(re.findall(r"<svg\b", text, re.I))
    print(f"html_bytes={HTML.stat().st_size}")
    print(f"inline_svg_count={n_svg}")
    print(f"md_bytes={MD.stat().st_size if MD.exists() else 0}")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS self-containment and section checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
