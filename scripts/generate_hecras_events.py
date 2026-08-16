#!/usr/bin/env python
"""Generate HEC-RAS event-library parameters and hydrograph CSVs.

Writes the 40-event protocol even when only a 10-event hydrograph subset
is materialised. Does not invent inundation fields.

Usage (from project root):
  python scripts/generate_hecras_events.py --config config/merced.yaml
  python scripts/generate_hecras_events.py --config config/bald_eagle.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg.config import load_config, resolve_path_value
from lsg.events import (
    DEFAULT_N_EVENTS,
    DEFAULT_SEED,
    generate_event_library,
    load_base_hydrograph,
    protocol_dict,
    write_event_hydrographs,
    write_event_table,
    write_protocol_yaml,
)


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.is_file():
            return path
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HEC-RAS event library")
    parser.add_argument("--config", type=Path, default=_ROOT / "config" / "merced.yaml")
    parser.add_argument("--n-events", type=int, default=None)
    parser.add_argument(
        "--write-hydrographs",
        type=int,
        default=10,
        help="Write this many hydrograph CSVs (test events first). 0 = none.",
    )
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    events_cfg = cfg.get("events") or {}
    case_id = str(cfg.get("study_area", {}).get("id") or Path(args.config).stem)
    n_events = int(args.n_events or events_cfg.get("n_events_design") or DEFAULT_N_EVENTS)
    seed = int(args.seed if args.seed is not None else events_cfg.get("seed", DEFAULT_SEED))
    drives = list(events_cfg.get("drives") or [])
    tributaries = list(events_cfg.get("tributaries") or [])
    id_prefix = str(events_cfg.get("id_prefix") or "E")

    out_dir = resolve_path_value(cfg, events_cfg.get("output_dir", "data/external/hecras_merced/events"))
    out_dir.mkdir(parents=True, exist_ok=True)

    specs = generate_event_library(
        n_events=n_events,
        seed=seed,
        drives=drives,
        tributaries=tributaries,
        id_prefix=id_prefix,
    )
    table_path = out_dir / "event_parameters.csv"
    write_event_table(table_path, specs)
    protocol_path = out_dir / "event_protocol.yaml"
    write_protocol_yaml(
        protocol_path,
        protocol_dict(
            case_id=case_id,
            drives=drives,
            n_events=n_events,
            seed=seed,
            tributaries=tributaries,
        ),
    )

    hydro_dir = out_dir / "hydrographs"
    written: list[Path] = []
    n_hydro = int(args.write_hydrographs)
    base_rel = events_cfg.get("base_hydrograph")
    base_path = resolve_path_value(cfg, base_rel) if base_rel else None
    if n_hydro > 0:
        candidates = []
        if base_path is not None:
            candidates.append(base_path)
        boundary = out_dir.parent / "boundary"
        candidates.extend(sorted(boundary.glob("*.csv")))
        candidates.extend(sorted(boundary.glob("*usgs*.txt")))
        candidates.extend(sorted(boundary.glob("*.rdb")))
        found = _first_existing(candidates)
        if found is None:
            print(
                f"[events] No base hydrograph at {base_path}. "
                "Wrote parameters only; export DSS to CSV or place USGS RDB in boundary/."
            )
        else:
            t_hours, q0 = load_base_hydrograph(found)
            # Prefer the 10 test events; fill from train/val if needed.
            ordered = [e for e in specs if e.split == "test"] + [
                e for e in specs if e.split != "test"
            ]
            subset = ordered[:n_hydro]
            written = write_event_hydrographs(
                hydro_dir,
                subset,
                t_hours,
                q0,
                tributaries=tributaries,
            )
            print(f"[events] base hydrograph {found} n={len(t_hours)}")

    print(f"[events] case={case_id} n={n_events} seed={seed}")
    print(f"[events] parameters {table_path}")
    print(f"[events] protocol {protocol_path}")
    if written:
        print(f"[events] hydrographs {len(written)} files in {hydro_dir}")


if __name__ == "__main__":
    main()
