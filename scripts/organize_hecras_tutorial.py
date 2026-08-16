#!/usr/bin/env python
"""Copy (or hardlink) official HEC-RAS tutorial files into case subfolders.

Never modifies ``original/``. Terrain, GIS, DSS/hydrographs, and land-cover
files are copied into terrain/, gis/, and boundary/.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

TERRAIN_EXT = {".tif", ".tiff", ".flt", ".hdr", ".adf", ".img", ".hdf", ".vrt", ".aux"}
GIS_EXT = {".shp", ".shx", ".dbf", ".prj", ".cpg", ".sbn", ".sbx", ".xml", ".lyr", ".gpkg", ".geojson"}
BOUNDARY_EXT = {".dss", ".dsx", ".csv", ".txt", ".rdb"}
LANDCOVER_HINTS = ("landcover", "land_cover", "nlcd", "manning", "n_value")


def _classify(rel: Path) -> str | None:
    name = rel.name.lower()
    parts = [p.lower() for p in rel.parts]
    suffix = rel.suffix.lower()
    if suffix in {".zip"}:
        return None
    if any(h in name or any(h in p for p in parts) for h in LANDCOVER_HINTS):
        return "gis"
    if any("terrain" in p or "usgs" in p or "dem" in p for p in parts):
        return "terrain"
    if suffix in TERRAIN_EXT and not any("gis" in p for p in parts):
        return "terrain"
    if suffix in BOUNDARY_EXT or "dss" in name or "hydro" in name or "flow" in name:
        return "boundary"
    if suffix in GIS_EXT or any(p in {"gis", "gisdata", "shapefile", "shp"} for p in parts):
        return "gis"
    if suffix in {".prj", ".p01", ".p02", ".g01", ".g02", ".u01", ".u02", ".hdf"}:
        return None
    return None


def _copy_or_link(src: Path, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return "exists"
    try:
        if src.stat().st_size >= 50 * 1024 * 1024:
            os.link(src, dest)
            return "hardlink"
    except OSError:
        pass
    shutil.copy2(src, dest)
    return "copy"


def organize(original: Path, case_root: Path) -> dict[str, int]:
    counts = {"terrain": 0, "gis": 0, "boundary": 0, "skipped": 0}
    if not original.is_dir():
        raise FileNotFoundError(original)
    for src in original.rglob("*"):
        if not src.is_file():
            continue
        try:
            rel = src.relative_to(original)
        except ValueError:
            continue
        bucket = _classify(rel)
        if bucket is None:
            counts["skipped"] += 1
            continue
        dest = case_root / bucket / rel.name
        if dest.exists() and dest.stat().st_size == src.stat().st_size:
            counts[bucket] += 1
            continue
        if dest.exists():
            dest = case_root / bucket / "__".join(rel.parts)
        _copy_or_link(src, dest)
        counts[bucket] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--original", type=Path, default=None)
    args = parser.parse_args()
    case_root = args.case_root
    original = args.original or (case_root / "original")
    counts = organize(original, case_root)
    print(f"[organize] {case_root} {counts}")


if __name__ == "__main__":
    main()
