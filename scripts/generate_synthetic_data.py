#!/usr/bin/env python
"""Generate synthetic HF/LF flood data for smoke tests."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg.config import load_config
from lsg.data import generate_synthetic_floodplain, save_event_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Brisbane-style data")
    parser.add_argument(
        "--config",
        type=Path,
        default=_ROOT / "config" / "brisbane.yaml",
    )
    args = parser.parse_args()
    cfg = load_config(args.config)
    syn = cfg["synthetic_demo"]
    data = generate_synthetic_floodplain(
        n_events=syn["n_events"],
        n_timesteps=syn["n_timesteps"],
        shape_hf=(syn["grid_ny"], syn["grid_nx"]),
        lf_factor=syn["lf_coarsening_factor"],
        seed=cfg["lsg"]["random_seed"],
    )
    out = Path(cfg["_project_root"]) / "data" / "synthetic" / "training_events.npz"
    save_event_bundle(
        out,
        data["hf_depth"],
        data["lf_depth"],
        data["terrain_hf"],
        data["shape_hf"],
        data["shape_lf"],
        data["event_ids"],
        data["meta"],
    )
    print(f"Wrote {out} events={data['event_ids']}")


if __name__ == "__main__":
    main()
