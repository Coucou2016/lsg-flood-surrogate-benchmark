#!/usr/bin/env python
"""Export cell-wise inundation_prob into an existing pred_examples.npz (no retrain).

Loads saved LSG-Max (and optionally LSG-TS) states, runs predict_uq on the
hold-out events implied by the config split, and merges
``inundation_prob_lsg_max`` (and ``inundation_prob_lsg_ts_max`` when shapes
match) into the prediction artifact used by spatial figures.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg.config import load_config, resolve_path
from lsg.data import resolve_train_test_indices
from lsg.lsg_max import LSGMaxModel
from lsg.lsg_ts import LSGTSModel

_wf_spec = importlib.util.spec_from_file_location(
    "run_lsg_workflow", _ROOT / "scripts" / "run_lsg_workflow.py"
)
assert _wf_spec is not None and _wf_spec.loader is not None
_wf = importlib.util.module_from_spec(_wf_spec)
_wf_spec.loader.exec_module(_wf)
_load_data = _wf._load_data
_mesh_args = _wf._mesh_args
_max_surface = _wf._max_surface


def _as_event_prob(prob: np.ndarray) -> np.ndarray:
    arr = np.asarray(prob, dtype=np.float64)
    if arr.ndim == 3:
        return np.nanmax(arr, axis=1)
    return arr


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument(
        "--pred-examples",
        type=Path,
        default=None,
        help="pred_examples.npz to update (default: evaluation/pred_examples.npz)",
    )
    p.add_argument(
        "--variants",
        default="lsg_max",
        help="Comma-separated: lsg_max,lsg_ts",
    )
    p.add_argument("--events", default=None)
    args = p.parse_args()

    class _Args:
        synthetic = False
        regenerate_synthetic = False
        data = None
        events = args.events
        lf_resolution = None
        time_reduction = None

    cfg = load_config(args.config)
    models_dir = resolve_path(cfg, "models")
    out_dir = resolve_path(cfg, "evaluation")
    pred_path = (
        Path(args.pred_examples)
        if args.pred_examples is not None
        else out_dir / "pred_examples.npz"
    )
    if not pred_path.is_file():
        raise SystemExit(f"missing pred_examples: {pred_path}")

    print(f"[Pwet] loading data for {args.config} …")
    data, real_status = _load_data(cfg, _Args())
    if not real_status.get("available") and str(
        (data.get("meta") or {}).get("source", "")
    ) not in {"fraehr", "real"}:
        raise SystemExit("Real Fraehr data required.")

    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]
    event_ids = [str(e) for e in data["event_ids"]]
    mesh = _mesh_args(data)
    xy_h, xy_l = mesh.get("xy_hf"), mesh.get("xy_lf")
    terrain_lf = mesh.get("terrain_lf")

    existing = dict(np.load(pred_path, allow_pickle=True))
    wanted = {v.strip() for v in str(args.variants).split(",") if v.strip()}
    updates: dict[str, Any] = {}

    for name, cls, state_name, key_out in (
        ("lsg_max", LSGMaxModel, "lsg_max_state.npz", "inundation_prob_lsg_max"),
        (
            "lsg_ts",
            LSGTSModel,
            "lsg_ts_state.npz",
            "inundation_prob_lsg_ts_max",
        ),
    ):
        if name not in wanted:
            continue
        state_path = models_dir / state_name
        if not state_path.is_file():
            raise SystemExit(f"missing state: {state_path}")
        train_idx, test_idx, split_name = resolve_train_test_indices(
            event_ids, cfg, name
        )
        print(f"[Pwet] {name}: {state_path.name} split={split_name} n_test={test_idx.size}")
        model = cls.load_from(state_path, cfg)
        t0 = time.perf_counter()
        fmap = model.predict_uq(
            lf[test_idx],
            terrain,
            shape_hf,
            shape_lf,
            xy_hf=xy_h,
            xy_lf=xy_l,
            terrain_lf=terrain_lf,
        )
        elapsed = time.perf_counter() - t0
        prob = _as_event_prob(fmap["inundation_prob"])
        pred_ref = existing.get("pred_lsg_max" if name == "lsg_max" else "pred_lsg_ts_max")
        if pred_ref is not None and np.asarray(pred_ref).shape != prob.shape:
            # Fall back: if TS max pred missing, still store under max key shape check.
            if name == "lsg_ts" and "pred_lsg_ts_max" not in existing:
                print(f"  skip {key_out}: pred_lsg_ts_max absent in artifact")
                continue
            raise SystemExit(
                f"shape mismatch for {key_out}: prob {prob.shape} vs pred "
                f"{np.asarray(pred_ref).shape}"
            )
        updates[key_out] = prob
        scale = float(getattr(model.state, "uq_var_scale", 1.0) or 1.0)
        print(
            f"  wrote {key_out} shape={prob.shape} mean={float(np.mean(prob)):.4g} "
            f"var_scale={scale:.4g} predict_uq_s={elapsed:.1f}"
        )

    if not updates:
        raise SystemExit("no inundation_prob arrays produced")

    merged = {**existing, **updates}
    np.savez_compressed(pred_path, **merged)
    print(f"[Pwet] updated {pred_path} keys+= {sorted(updates)}")


if __name__ == "__main__":
    main()
