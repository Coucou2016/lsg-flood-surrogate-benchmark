#!/usr/bin/env python
"""Re-score UQ from saved Carlisle dual states with CRPS variance calibration.

No retrain: load ``lsg_*_state.npz``, ingest Fraehr grids, fit a global
predictive-variance scale on train (active cells, CRPS), apply on test, and
write a distinctly named summary JSON. Point CSI/RMSE are re-checked from the
unchanged latent mean / operational map.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg import evaluation, uq
from lsg.config import load_config, resolve_path
from lsg.data import resolve_train_test_indices
from lsg.lsg_max import LSGMaxModel
from lsg.lsg_ts import LSGTSModel
from lsg.spatial import unpadded_rows

import importlib.util

_wf_spec = importlib.util.spec_from_file_location(
    "run_lsg_workflow", _ROOT / "scripts" / "run_lsg_workflow.py"
)
assert _wf_spec is not None and _wf_spec.loader is not None
_wf = importlib.util.module_from_spec(_wf_spec)
_wf_spec.loader.exec_module(_wf)
_load_data = _wf._load_data
_max_surface = _wf._max_surface
_mesh_args = _wf._mesh_args
_to_jsonable = _wf._to_jsonable


def _drop_padded(*cubes: np.ndarray) -> tuple[np.ndarray, ...]:
    flat = [np.asarray(c).reshape(-1, np.asarray(c).shape[-1]) for c in cubes]
    real = unpadded_rows(flat[0])
    return tuple(arr[real] for arr in flat)


def _calib_subset(
    hf: np.ndarray,
    lf: np.ndarray,
    *,
    time_series: bool,
    max_rows: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    if not time_series or max_rows <= 0 or lf.ndim != 3:
        return hf, lf
    if hf.shape[:2] != lf.shape[:2]:
        raise ValueError(
            f"HF/LF time shape mismatch for calib subset: {hf.shape} vs {lf.shape}"
        )
    n_ev, n_t = lf.shape[0], lf.shape[1]
    # Fraehr LF stays on the LF mesh until predict-time interpolation, so n_cells differ.
    lf_flat = np.asarray(lf, dtype=np.float64).reshape(n_ev * n_t, -1)
    hf_flat = np.asarray(hf, dtype=np.float64).reshape(n_ev * n_t, -1)
    idx = np.flatnonzero(unpadded_rows(lf_flat))
    if idx.size == 0:
        idx = np.flatnonzero(unpadded_rows(hf_flat))
    if idx.size == 0:
        return hf, lf
    if idx.size > max_rows:
        rng = np.random.default_rng(seed)
        pick = rng.choice(idx, size=max_rows, replace=False)
    else:
        pick = idx
    # (n_sub, 1, C) keeps LSG-TS predict_uq's (n_ev, n_t, C) contract.
    return hf_flat[pick][:, np.newaxis, :], lf_flat[pick][:, np.newaxis, :]


def _score_variant(
    name: str,
    model,
    hf_train: np.ndarray,
    lf_train: np.ndarray,
    hf_test: np.ndarray,
    lf_test: np.ndarray,
    terrain: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    mesh: dict[str, Any],
    *,
    calib_method: str,
    max_rows: int,
    seed: int,
    baseline_uq: dict[str, Any] | None,
) -> dict[str, Any]:
    time_series = name == "lsg_ts"
    thresh = float(model.cfg["hydrodynamic"]["depth_threshold_m"])
    xy_h, xy_l = mesh.get("xy_hf"), mesh.get("xy_lf")
    terrain_lf = mesh.get("terrain_lf")

    # Point metrics (mean path) — must match the uncalibrated stack.
    t0 = time.perf_counter()
    pred = model.predict(
        lf_test,
        terrain,
        shape_hf,
        shape_lf,
        xy_hf=xy_h,
        xy_lf=xy_l,
        terrain_lf=terrain_lf,
    )
    pred_s = time.perf_counter() - t0
    metrics = model.evaluate(pred, hf_test)
    if time_series:
        pred_max = _max_surface(pred)
        hf_max = _max_surface(hf_test)
        max_only = evaluation.extent_metrics(pred_max, hf_max, thresh)
        metrics = {**metrics, **{f"eval_{k}": v for k, v in max_only.items()}}
        metrics["max_csi"] = max_only["csi"]
        metrics["max_rmse"] = max_only["rmse"]
    else:
        metrics["csi"] = metrics.get("csi")
        metrics["rmse"] = metrics.get("rmse")

    # --- raw UQ (scale = 1) ---
    uq.set_state_uq_var_scale(model.state, 1.0)
    fmap_raw = model.predict_uq(
        lf_test,
        terrain,
        shape_hf,
        shape_lf,
        xy_hf=xy_h,
        xy_lf=xy_l,
        terrain_lf=terrain_lf,
    )
    obs = hf_test if time_series else _max_surface(hf_test)
    obs_s, mean_s, var_s, prob_s = _drop_padded(
        obs,
        fmap_raw["latent_mean"],
        fmap_raw["latent_var"],
        fmap_raw["inundation_prob"],
    )
    uq_raw = uq.score_probabilistic(obs_s, mean_s, var_s, thresh)
    uq_raw["mean_inundation_prob"] = float(np.mean(prob_s))
    uq_raw["var_scale"] = 1.0
    if baseline_uq:
        uq_raw["baseline_summary_coverage_90"] = baseline_uq.get("coverage_90")
        uq_raw["baseline_summary_crps"] = baseline_uq.get("crps")

    # --- calibrate on train ---
    hf_cal, lf_cal = _calib_subset(
        hf_train,
        lf_train,
        time_series=time_series,
        max_rows=max_rows,
        seed=seed,
    )
    t1 = time.perf_counter()
    fmap_tr = model.predict_uq(
        lf_cal,
        terrain,
        shape_hf,
        shape_lf,
        xy_hf=xy_h,
        xy_lf=xy_l,
        terrain_lf=terrain_lf,
    )
    obs_tr = hf_cal if time_series else _max_surface(hf_cal)
    obs_tr, mean_tr, var_tr = _drop_padded(
        obs_tr, fmap_tr["latent_mean"], fmap_tr["latent_var"]
    )
    del fmap_tr
    calib = uq.fit_variance_scale(
        obs_tr, mean_tr, var_tr, method=calib_method, threshold_m=thresh
    )
    calib["n_calib_rows"] = int(np.asarray(obs_tr).reshape(-1, obs_tr.shape[-1]).shape[0])
    calib["fit_s"] = float(time.perf_counter() - t1)
    uq.set_state_uq_var_scale(model.state, calib["var_scale"])

    # --- calibrated test UQ (re-use raw moments × scale; avoid second full predict) ---
    uq_cal = uq.score_probabilistic(
        obs_s, mean_s, var_s, thresh, var_scale=float(calib["var_scale"])
    )
    # inundation_prob under calibrated var
    fmap_cal = uq.probabilistic_flood_map(
        mean_s, uq.apply_variance_scale(var_s, calib["var_scale"]), thresh
    )
    uq_cal["mean_inundation_prob"] = float(np.mean(fmap_cal["inundation_prob"]))
    uq_cal["calibration"] = calib
    uq_cal["var_scale"] = float(calib["var_scale"])

    metrics["runtime_predict_s"] = float(pred_s)
    metrics["uq_uncalibrated"] = uq_raw
    metrics["uq"] = uq_cal
    metrics["uq_calibration"] = calib
    metrics["gp_backend"] = getattr(model.state, "gp_backend", None)
    return metrics


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=_ROOT / "config" / "carlisle.yaml")
    p.add_argument(
        "--summary-in",
        type=Path,
        default=_ROOT
        / "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json",
    )
    p.add_argument(
        "--summary-out",
        type=Path,
        default=_ROOT
        / "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix_uq_calibrated.json",
    )
    p.add_argument(
        "--method",
        default=None,
        help="Override evaluation.uq_calibration (default: config / crps_scale)",
    )
    p.add_argument("--max-rows", type=int, default=None)
    p.add_argument(
        "--variants",
        default="lsg_max,lsg_ts",
        help="Comma-separated: lsg_max,lsg_ts",
    )
    p.add_argument("--events", default=None, help="Optional ingest subset, e.g. E2,E3,E6")
    args = p.parse_args()

    # argparse Namespace expected by _load_data
    class _Args:
        synthetic = False
        regenerate_synthetic = False
        data = None
        events = args.events
        lf_resolution = None

    cfg = load_config(args.config)
    method = args.method or (cfg.get("evaluation") or {}).get(
        "uq_calibration", "crps_scale"
    )
    max_rows = args.max_rows
    if max_rows is None:
        max_rows = int(
            (cfg.get("evaluation") or {}).get("uq_calibration_max_rows", 256)
        )
    seed = int((cfg.get("lsg") or {}).get("random_seed", 0))

    print(f"[UQ-cal] loading data (method={method}, max_rows={max_rows}) …")
    data, real_status = _load_data(cfg, _Args())
    if not real_status.get("available") and str(
        (data.get("meta") or {}).get("source", "")
    ) not in {"fraehr", "real"}:
        raise SystemExit("Real Fraehr Carlisle data required for this rescore.")

    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]
    event_ids = [str(e) for e in data["event_ids"]]
    mesh = _mesh_args(data)
    models_dir = resolve_path(cfg, "models")

    baseline: dict[str, Any] = {}
    if args.summary_in.is_file():
        with args.summary_in.open(encoding="utf-8") as f:
            baseline = json.load(f)

    out: dict[str, Any] = {
        "project_root": str(cfg["_project_root"]),
        "data_source": "fraehr",
        "data_mode": "real",
        "lsg_field": (cfg.get("lsg") or {}).get("field"),
        "lsg_zoning": (cfg.get("lsg") or {}).get("zoning"),
        "event_ids": event_ids,
        "uq_calibration_method": method,
        "uq_calibration_max_rows": max_rows,
        "baseline_summary": str(args.summary_in),
        "note": (
            "UQ re-score from saved states with CRPS (or coverage_90) global "
            "variance scale fit on train; latent mean / point CSI-RMSE unchanged."
        ),
    }
    if baseline:
        for key in ("resolution", "split_protocol", "score_protocol", "lf_only_max"):
            if key in baseline:
                out[key] = baseline[key]

    wanted = {v.strip() for v in str(args.variants).split(",") if v.strip()}
    for name, cls, state_name, split_key in (
        ("lsg_max", LSGMaxModel, "lsg_max_state.npz", "lsg_max"),
        ("lsg_ts", LSGTSModel, "lsg_ts_state.npz", "lsg_ts"),
    ):
        if name not in wanted:
            continue
        state_path = models_dir / state_name
        if not state_path.is_file():
            raise SystemExit(f"missing state: {state_path}")
        train_idx, test_idx, split_name = resolve_train_test_indices(
            event_ids, cfg, split_key
        )
        print(f"[UQ-cal] {name}: load {state_path.name}, split={split_name}")
        model = cls.load_from(state_path, cfg)
        base_block = (baseline.get(name) or {}) if baseline else {}
        metrics = _score_variant(
            name,
            model,
            hf[train_idx],
            lf[train_idx],
            hf[test_idx],
            lf[test_idx],
            terrain,
            shape_hf,
            shape_lf,
            mesh,
            calib_method=str(method),
            max_rows=int(max_rows),
            seed=seed,
            baseline_uq=base_block.get("uq"),
        )
        metrics["split"] = split_name
        metrics["train_ids"] = [event_ids[i] for i in train_idx.tolist()]
        metrics["test_ids"] = [event_ids[i] for i in test_idx.tolist()]
        metrics["model_path"] = str(state_path)
        metrics["n_train"] = int(train_idx.size)
        metrics["n_test"] = int(test_idx.size)
        # Preserve point metrics from baseline when present for CSI/RMSE check.
        if base_block:
            metrics["baseline_csi"] = base_block.get("csi") or base_block.get("eval_csi")
            metrics["baseline_rmse"] = base_block.get("rmse") or base_block.get(
                "eval_rmse"
            )
            if name == "lsg_ts":
                metrics["baseline_max_csi"] = base_block.get("max_csi") or base_block.get(
                    "eval_csi"
                )
                metrics["baseline_max_rmse"] = base_block.get("max_rmse") or base_block.get(
                    "eval_rmse"
                )
        out[name] = metrics
        u0, u1 = metrics["uq_uncalibrated"], metrics["uq"]
        print(
            f"  scale={u1['var_scale']:.4g}  "
            f"CRPS {u0['crps']:.4g}->{u1['crps']:.4g}  "
            f"cov90 {u0['coverage_90']:.3f}->{u1['coverage_90']:.3f}  "
            f"cov50 {u0['coverage_50']:.3f}->{u1['coverage_50']:.3f}  "
            f"active90 {u0.get('coverage_90_active', float('nan')):.3f}"
            f"->{u1.get('coverage_90_active', float('nan')):.3f}"
        )

    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    with args.summary_out.open("w", encoding="utf-8") as f:
        json.dump(_to_jsonable(out), f, indent=2)
    print(f"[UQ-cal] wrote {args.summary_out}")


if __name__ == "__main__":
    main()
