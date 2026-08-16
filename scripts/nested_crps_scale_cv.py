#!/usr/bin/env python
"""Leave-one-train-event nested CV for CRPS variance scale ``s`` (cheap cases).

Fits ``s`` on all-but-one train events, evaluates CRPS on the held-out train
event and on the official test fold. Uses a saved dual state (no retrain).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg import uq
from lsg.config import load_config
from lsg.data import resolve_train_test_indices
from lsg.lsg_max import LSGMaxModel
from lsg.spatial import unpadded_rows

import importlib.util

_wf_spec = importlib.util.spec_from_file_location(
    "run_lsg_workflow", _ROOT / "scripts" / "run_lsg_workflow.py"
)
assert _wf_spec is not None and _wf_spec.loader is not None
_wf = importlib.util.module_from_spec(_wf_spec)
_wf_spec.loader.exec_module(_wf)


def _max_surface(cube: np.ndarray) -> np.ndarray:
    arr = np.asarray(cube, dtype=np.float64)
    if arr.ndim == 3:
        return np.nanmax(arr, axis=1)
    return arr


def _drop_padded(*arrays: np.ndarray) -> tuple[np.ndarray, ...]:
    flat0 = np.asarray(arrays[0]).reshape(-1, np.asarray(arrays[0]).shape[-1])
    real = unpadded_rows(flat0)
    out = []
    for a in arrays:
        arr = np.asarray(a)
        if arr.ndim == 1:
            out.append(arr)
        else:
            out.append(arr.reshape(-1, arr.shape[-1])[real])
    return tuple(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_ROOT / "config" / "chowilla.yaml")
    parser.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Saved lsg_max_state.npz (default: paths.models/lsg_max_state.npz)",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=_ROOT
        / "outputs"
        / "evaluation"
        / "chowilla"
        / "nested_crps_scale_cv.json",
    )
    parser.add_argument("--max-folds", type=int, default=8)
    args = parser.parse_args()

    t0 = time.perf_counter()
    cfg = load_config(args.config)
    from lsg.config import resolve_path

    model_path = args.model
    if model_path is None:
        model_path = resolve_path(cfg, "models") / "lsg_max_state.npz"
    data, _ = _wf._load_data(
        cfg,
        SimpleNamespace(
            synthetic=False,
            regenerate_synthetic=False,
            events=None,
            time_reduction=None,
            data=None,
            lf_resolution=None,
        ),
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]
    event_ids = [str(e) for e in data["event_ids"]]
    mesh = _wf._mesh_args(data)
    train_idx, test_idx, split_name = resolve_train_test_indices(
        event_ids, cfg, "lsg_max"
    )
    thresh = float(cfg["hydrodynamic"]["depth_threshold_m"])
    seed = int((cfg.get("lsg") or {}).get("random_seed", 0))

    model = LSGMaxModel.load_from(model_path, cfg)
    assert model.state is not None
    uq.set_state_uq_var_scale(model.state, 1.0)

    # Precompute UQ maps for all train + test once (var_scale=1).
    def _uq_maps(idx: np.ndarray):
        fmap = model.predict_uq(
            lf[idx],
            terrain,
            shape_hf,
            shape_lf,
            xy_hf=mesh.get("xy_hf"),
            xy_lf=mesh.get("xy_lf"),
            terrain_lf=mesh.get("terrain_lf"),
        )
        obs = _max_surface(hf[idx])
        obs, mean, var = _drop_padded(obs, fmap["latent_mean"], fmap["latent_var"])
        return obs, mean, var

    train_obs, train_mean, train_var = _uq_maps(train_idx)
    test_obs, test_mean, test_var = _uq_maps(test_idx)

    # Per-event row blocks after padding drop: Max has one row/event if unpadded.
    # Rebuild event-aligned views from original indices (no pad expected for Fraehr max).
    hf_tr = _max_surface(hf[train_idx])
    n_train_ev = int(train_idx.size)
    assert hf_tr.shape[0] == n_train_ev

    folds = []
    fold_ids = list(range(n_train_ev))
    if args.max_folds > 0 and len(fold_ids) > args.max_folds:
        rng = np.random.default_rng(seed)
        fold_ids = sorted(rng.choice(fold_ids, size=args.max_folds, replace=False).tolist())

    for i in fold_ids:
        calib_mask = np.ones(n_train_ev, dtype=bool)
        calib_mask[i] = False
        # Align with dropped-pad train arrays: for max surfaces, rows == events.
        obs_c = train_obs[calib_mask]
        mean_c = train_mean[calib_mask]
        var_c = train_var[calib_mask]
        calib = uq.fit_variance_scale(
            obs_c, mean_c, var_c, method="crps_scale", threshold_m=thresh, seed=seed
        )
        s = float(calib["var_scale"])
        hold_obs = train_obs[i : i + 1]
        hold_mean = train_mean[i : i + 1]
        hold_var = train_var[i : i + 1] * s
        hold_score = uq.score_probabilistic(hold_obs, hold_mean, hold_var, thresh)
        test_score = uq.score_probabilistic(
            test_obs, test_mean, test_var * s, thresh
        )
        folds.append(
            {
                "holdout_train_id": event_ids[int(train_idx[i])],
                "var_scale": s,
                "holdout_crps": hold_score.get("crps"),
                "holdout_coverage_90": hold_score.get("coverage_90"),
                "test_crps": test_score.get("crps"),
                "test_coverage_90": test_score.get("coverage_90"),
            }
        )
        print(
            f"[fold {event_ids[int(train_idx[i])]}] s={s:.4f} "
            f"hold_crps={hold_score.get('crps')} test_crps={test_score.get('crps')}"
        )

    scales = np.asarray([f["var_scale"] for f in folds], dtype=np.float64)
    # Full-train fit (protocol baseline)
    full = uq.fit_variance_scale(
        train_obs, train_mean, train_var, method="crps_scale", threshold_m=thresh, seed=seed
    )
    out = {
        "case": str((cfg.get("study_area") or {}).get("id", "")),
        "split": split_name,
        "model_path": str(model_path),
        "n_train": n_train_ev,
        "n_test": int(test_idx.size),
        "max_folds": int(args.max_folds),
        "folds_used": [f["holdout_train_id"] for f in folds],
        "full_train_var_scale": float(full["var_scale"]),
        "fold_var_scale_mean": float(np.mean(scales)),
        "fold_var_scale_std": float(np.std(scales)),
        "fold_var_scale_min": float(np.min(scales)),
        "fold_var_scale_max": float(np.max(scales)),
        "folds": folds,
        "runtime_s": float(time.perf_counter() - t0),
    }
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(
        f"[nested_crps] s_full={out['full_train_var_scale']:.4f} "
        f"s_fold={out['fold_var_scale_mean']:.4f}±{out['fold_var_scale_std']:.4f} "
        f"wrote {args.summary_out}"
    )


if __name__ == "__main__":
    main()
