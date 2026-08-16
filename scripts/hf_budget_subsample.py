#!/usr/bin/env python
"""Retrain LSG-Max on nested HF-event budgets (fixed test set).

Cheap diagnostic for a fixed high-fidelity training budget. Does not run
HEC-RAS or download data.

Usage (from project root):
  python scripts/hf_budget_subsample.py --config config/brisbane.yaml --synthetic
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg.config import load_config, resolve_path
from lsg.data import generate_synthetic_floodplain, resolve_train_test_indices
from lsg.diagnostics import hf_budget_curve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=_ROOT / "config" / "brisbane.yaml"
    )
    parser.add_argument("--synthetic", action="store_true", default=True)
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="*",
        default=[2, 3, 4, 6],
        help="Nested training sizes (prefixes of the train split)",
    )
    args = parser.parse_args()
    cfg = load_config(args.config)
    syn = cfg.get("synthetic_demo") or {
        "n_events": 8,
        "n_timesteps": 12,
        "grid_nx": 20,
        "grid_ny": 16,
        "lf_coarsening_factor": 4,
    }
    data = generate_synthetic_floodplain(
        n_events=int(syn.get("n_events", 8)),
        n_timesteps=int(syn.get("n_timesteps", 12)),
        shape_hf=(int(syn.get("grid_ny", 16)), int(syn.get("grid_nx", 20))),
        lf_factor=int(syn.get("lf_coarsening_factor", 4)),
        seed=int(cfg.get("lsg", {}).get("random_seed", 0)),
    )
    train_idx, test_idx, _ = resolve_train_test_indices(
        data["event_ids"], cfg, "lsg_max"
    )
    rows = hf_budget_curve(
        data["hf_depth"],
        data["lf_depth"],
        data["terrain_hf"],
        data["shape_hf"],
        data["shape_lf"],
        cfg,
        train_idx,
        test_idx,
        list(args.budgets),
    )
    out_dir = (
        resolve_path(cfg, "evaluation")
        if "evaluation" in cfg.get("paths", {})
        else _ROOT / "outputs" / "evaluation"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "hf_budget_curve.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
