#!/usr/bin/env python
"""Probe local HEC-RAS install and HDF files for a case directory.

Usage:
  python scripts/probe_hecras.py --case-root data/external/hecras_merced
  python scripts/probe_hecras.py --run-plan --timeout 1200
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg.hecras import (
    detect_hecras_install,
    find_ras_hdf,
    run_hecras_plan,
    summarize_hdf,
    walk_hdf,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe HEC-RAS install and HDF")
    parser.add_argument("--case-root", type=Path, default=_ROOT / "data" / "external" / "hecras_merced")
    parser.add_argument("--hdf", type=Path, default=None)
    parser.add_argument("--run-plan", action="store_true")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--list-paths", action="store_true")
    args = parser.parse_args()

    install = detect_hecras_install()
    if install is None:
        print("[hecras] not installed (checked Program Files HEC and $HECRAS_HOME)")
    else:
        print(f"[hecras] {install.ras_exe} version_dir={install.version_name}")

    hdf_files = [args.hdf] if args.hdf else find_ras_hdf(args.case_root)
    if not hdf_files:
        print(f"[hecras] no .hdf under {args.case_root}")
        print(
            "[hecras] geometry/terrain can still be listed from GIS; "
            "paired HF/LF depth cubes need a local HEC-RAS plan run."
        )
    for hdf in hdf_files:
        summary = summarize_hdf(hdf)
        print(json.dumps(summary, indent=2))
        if args.list_paths:
            for row in walk_hdf(hdf):
                extra = ""
                if row["kind"] == "dataset":
                    extra = f" {row['shape']} {row['dtype']}"
                print(f"  {row['kind']:7s} {row['path']}{extra}")

    if args.run_plan:
        if install is None:
            print("[hecras] cannot run plan: Ras.exe not found")
            return
        prj = list(args.case_root.rglob("*.prj"))
        rasmap = [p for p in prj if p.name.lower() != "projection.prj"]
        if not rasmap:
            print("[hecras] no .prj project file found; official tutorial may be GIS-only")
            return
        project = rasmap[0]
        print(f"[hecras] running {project} timeout={args.timeout}s")
        result = run_hecras_plan(project, timeout_s=args.timeout)
        print(json.dumps({k: result[k] for k in result if k not in {"stdout", "stderr"}}, indent=2))
        if result.get("stdout"):
            print(result["stdout"][-1500:])
        if result.get("stderr"):
            print(result["stderr"][-1500:])


if __name__ == "__main__":
    main()
