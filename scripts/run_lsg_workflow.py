#!/usr/bin/env python
"""
End-to-end LSG workflow: train LSG-Max and LSG-TS, evaluate, compare LF resolutions.

Usage (from project root):
  python scripts/run_lsg_workflow.py --config config/carlisle.yaml
  python scripts/run_lsg_workflow.py --config config/brisbane.yaml --synthetic
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

from lsg import base, gp
from lsg.config import load_config, resolve_path, resolve_path_value
from lsg.data import (
    PAPER_VE_MAP,
    coarsen_event_cube,
    detect_real_event_data,
    generate_synthetic_floodplain,
    ingest_lf_hf_npz_dir,
    load_event_bundle,
    normalize_event_id,
    resolve_train_test_indices,
    save_event_bundle,
)
from lsg.fraehr import ingest_fraehr_case
from lsg.lsg_max import LSGMaxModel
from lsg.lsg_ts import LSGTSModel
from lsg.wse_ext import field_mode

_MINI_SYNTHETIC = {
    "n_events": 8,
    "n_timesteps": 12,
    "grid_nx": 20,
    "grid_ny": 16,
    "lf_coarsening_factor": 4,
}


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer, np.bool_)):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _max_surface(depth: np.ndarray) -> np.ndarray:
    if depth.ndim == 3:
        return np.nanmax(depth, axis=1)
    return np.asarray(depth)


def _per_event_holdout(
    pred_max: np.ndarray,
    hf_max: np.ndarray,
    test_ids: list[str],
    threshold_m: float,
) -> dict[str, dict[str, Any]]:
    from lsg import evaluation

    out: dict[str, dict[str, Any]] = {}
    for i, eid in enumerate(test_ids):
        metrics = evaluation.extent_metrics(
            pred_max[i : i + 1], hf_max[i : i + 1], threshold_m
        )
        nid = normalize_event_id(eid)
        metrics["ve_label"] = PAPER_VE_MAP.get(nid)
        out[str(eid)] = metrics
    return out


def _drop_padded_rows(*cubes: np.ndarray) -> tuple[np.ndarray, ...]:
    """Flatten to (n_samples, n_cells) and drop the NaN pads of ragged events."""
    from lsg.spatial import unpadded_rows

    flat = [np.asarray(c).reshape(-1, np.asarray(c).shape[-1]) for c in cubes]
    real = unpadded_rows(flat[0])
    return tuple(arr[real] for arr in flat)


def _mesh_args(data: dict) -> dict[str, Any]:
    return {
        "xy_hf": data.get("xy_hf"),
        "xy_lf": data.get("xy_lf"),
        "area_hf": data.get("area_hf"),
        "terrain_lf": data.get("terrain_lf"),
    }


def run_variant(
    name: str,
    model,
    hf_train,
    lf_train,
    hf_test,
    lf_test,
    terrain,
    shape_hf,
    shape_lf,
    test_ids: list[str],
    mesh: dict[str, Any] | None = None,
) -> tuple[dict, np.ndarray]:
    mesh = mesh or {}
    t0 = time.perf_counter()
    model.fit(hf_train, lf_train, terrain, shape_hf, shape_lf, **mesh)
    train_s = time.perf_counter() - t0
    t1 = time.perf_counter()
    pred = model.predict(
        lf_test,
        terrain,
        shape_hf,
        shape_lf,
        xy_hf=mesh.get("xy_hf"),
        xy_lf=mesh.get("xy_lf"),
        terrain_lf=mesh.get("terrain_lf"),
    )
    pred_s = time.perf_counter() - t1
    metrics = model.evaluate(pred, hf_test)
    if name == "lsg_ts":
        pred_max = _max_surface(pred)
        hf_max = _max_surface(hf_test)
        from lsg import evaluation

        max_only = evaluation.extent_metrics(
            pred_max, hf_max, model.cfg["hydrodynamic"]["depth_threshold_m"]
        )
        metrics = {**metrics, **{f"eval_{k}": v for k, v in max_only.items()}}
    else:
        pred_max = pred
        hf_max = _max_surface(hf_test)
    thresh = model.cfg["hydrodynamic"]["depth_threshold_m"]
    metrics["holdout"] = _per_event_holdout(pred_max, hf_max, test_ids, thresh)
    metrics["runtime_train_s"] = float(train_s)
    metrics["runtime_predict_s"] = float(pred_s)
    metrics["n_train"] = int(hf_train.shape[0])
    metrics["n_test"] = int(hf_test.shape[0])
    backend = "numpy"
    if model.state is not None:
        backend = model.state.gp_backend
    metrics["gp_backend"] = backend
    ev = model.cfg.get("evaluation") or {}
    xy_h, xy_l = mesh.get("xy_hf"), mesh.get("xy_lf")
    time_series = name == "lsg_ts"
    if ev.get("uq") and hasattr(model, "predict_uq"):
        from lsg import uq as lsg_uq

        thresh = model.cfg["hydrodynamic"]["depth_threshold_m"]
        calib_method = ev.get("uq_calibration", "crps_scale")
        # Fit variance scale on train predictions (no test leakage); mean maps unchanged.
        if calib_method and str(calib_method).lower() not in {
            "none",
            "off",
            "false",
            "0",
        }:
            lf_cal = lf_train
            hf_cal = hf_train
            max_rows = int(ev.get("uq_calibration_max_rows", 256))
            seed = int(model.cfg.get("lsg", {}).get("random_seed", 0))
            if time_series and max_rows > 0 and lf_train.ndim == 3:
                from lsg.spatial import unpadded_rows

                if hf_train.shape[:2] != lf_train.shape[:2]:
                    raise ValueError(
                        f"HF/LF time shape mismatch: {hf_train.shape} vs {lf_train.shape}"
                    )
                n_ev, n_t = lf_train.shape[0], lf_train.shape[1]
                # LF mesh cell count differs from HF until predict-time interpolation.
                lf_flat = np.asarray(lf_train, dtype=np.float64).reshape(n_ev * n_t, -1)
                hf_flat = np.asarray(hf_train, dtype=np.float64).reshape(n_ev * n_t, -1)
                idx = np.flatnonzero(unpadded_rows(lf_flat))
                if idx.size == 0:
                    idx = np.flatnonzero(unpadded_rows(hf_flat))
                if idx.size > max_rows:
                    rng = np.random.default_rng(seed)
                    pick = rng.choice(idx, size=max_rows, replace=False)
                else:
                    pick = idx
                if pick.size:
                    # (n_sub, 1, C) keeps LSG-TS predict_uq's (n_ev, n_t, C) contract.
                    lf_cal = lf_flat[pick][:, np.newaxis, :]
                    hf_cal = hf_flat[pick][:, np.newaxis, :]

            prior = float(getattr(model.state, "uq_var_scale", 1.0) or 1.0)
            lsg_uq.set_state_uq_var_scale(model.state, 1.0)
            fmap_tr = model.predict_uq(
                lf_cal,
                terrain,
                shape_hf,
                shape_lf,
                xy_hf=xy_h,
                xy_lf=xy_l,
                terrain_lf=mesh.get("terrain_lf"),
            )
            obs_tr = hf_cal if time_series else _max_surface(hf_cal)
            obs_tr, mean_tr, var_tr = _drop_padded_rows(
                obs_tr,
                fmap_tr["latent_mean"],
                fmap_tr["latent_var"],
            )
            del fmap_tr
            calib = lsg_uq.fit_variance_scale(
                obs_tr,
                mean_tr,
                var_tr,
                method=str(calib_method),
                threshold_m=thresh,
                seed=seed,
            )
            lsg_uq.set_state_uq_var_scale(model.state, calib["var_scale"])
            calib["prior_var_scale"] = prior
            calib["n_calib_rows"] = int(
                np.asarray(obs_tr).reshape(-1, np.asarray(obs_tr).shape[-1]).shape[0]
            )
            metrics["uq_calibration"] = calib
            print(
                f"[LSG] {name} UQ var_scale={calib['var_scale']:.4g} "
                f"({calib['method']}, cells={calib.get('n_calib_cells')}, "
                f"rows={calib.get('n_calib_rows')})"
            )

        fmap = model.predict_uq(
            lf_test,
            terrain,
            shape_hf,
            shape_lf,
            xy_hf=xy_h,
            xy_lf=xy_l,
            terrain_lf=mesh.get("terrain_lf"),
        )
        obs = hf_test if time_series else _max_surface(hf_test)
        obs, mean, var, prob = _drop_padded_rows(
            obs,
            fmap["latent_mean"],
            fmap["latent_var"],
            fmap["inundation_prob"],
        )
        # Scale already applied inside predict_uq when state.uq_var_scale != 1.
        metrics["uq"] = lsg_uq.score_probabilistic(obs, mean, var, thresh)
        metrics["uq"]["mean_inundation_prob"] = float(np.mean(prob))
        metrics["uq"]["var_scale"] = float(
            getattr(model.state, "uq_var_scale", 1.0) or 1.0
        )
        if "uq_calibration" in metrics:
            metrics["uq"]["calibration"] = metrics["uq_calibration"]
    if ev.get("error_budget") and model.state is not None:
        from lsg import diagnostics

        rows = [
            diagnostics.error_budget_from_state(
                model.state,
                hf_train,
                lf_train,
                terrain,
                shape_hf,
                shape_lf,
                time_series,
                split="train",
                xy_hf=xy_h,
                xy_lf=xy_l,
                terrain_lf=mesh.get("terrain_lf"),
            ),
            diagnostics.error_budget_from_state(
                model.state,
                hf_test,
                lf_test,
                terrain,
                shape_hf,
                shape_lf,
                time_series,
                split="test",
                xy_hf=xy_h,
                xy_lf=xy_l,
                terrain_lf=mesh.get("terrain_lf"),
            ),
        ]
        metrics["error_budget"] = diagnostics.budget_table(rows)
        print(f"[LSG] {name} error budget:")
        for row in metrics["error_budget"]:
            o4 = row["o4_rmse"]
            o4s = "n/a" if o4 is None else f"{float(o4):.4g}"
            o1 = row["o1_rmse"]
            if o1 is None:
                print(
                    f"      {row['split']}: skipped "
                    f"({row.get('notes', 'no depth-path budget')})"
                )
                continue
            print(
                f"      {row['split']}: O1={row['o1_rmse']:.4g} "
                f"O2={row['o2_rmse']:.4g} O3={row['o3_rmse']:.4g} "
                f"O4={o4s} (k={row['n_modes']}/{row['n_modes_full']})"
            )
    return metrics, pred


def _synthetic_lf_factors(cfg: dict) -> dict[str, int]:
    syn = cfg.get("synthetic_demo") or {}
    factors = syn.get("lf_resolution_factors")
    if factors:
        return {str(k): int(v) for k, v in factors.items()}
    return {"lf120": 4, "lf300": 10}


def lf_resolution_comparison(
    cfg: dict,
    hf: np.ndarray,
    terrain,
    shape_hf,
    event_ids: list[str],
    real_status: dict,
) -> dict:
    """Compare LF120 vs LF300. Real paired dirs win; else coarsen the same HF cube."""
    if real_status.get("kind") == "fraehr":
        return {
            "_mode": "skipped",
            "reason": "published case has a single LF mesh; no lf120/lf300 pair",
        }
    results: dict = {}
    hf_dir = real_status.get("hf_dir")
    real_lf = real_status.get("lf_resolution_dirs") or {}
    if hf_dir and real_lf:
        for label, lf_dir in real_lf.items():
            try:
                data = ingest_lf_hf_npz_dir(hf_dir, lf_dir, strict=False)
            except FileNotFoundError as exc:
                results[label] = {"error": str(exc)}
                continue
            train_idx, test_idx, split_name = resolve_train_test_indices(
                data["event_ids"], cfg, "lsg_ts"
            )
            m = LSGTSModel(cfg)
            t0 = time.perf_counter()
            m.fit(
                data["hf_depth"][train_idx],
                data["lf_depth"][train_idx],
                data["terrain_hf"],
                data["shape_hf"],
                data["shape_lf"],
            )
            train_s = time.perf_counter() - t0
            t1 = time.perf_counter()
            pred = m.predict(
                data["lf_depth"][test_idx],
                data["terrain_hf"],
                data["shape_hf"],
                data["shape_lf"],
            )
            pred_s = time.perf_counter() - t1
            metrics = m.evaluate(pred, data["hf_depth"][test_idx])
            metrics["split"] = split_name
            metrics["n_train"] = int(train_idx.size)
            metrics["n_test"] = int(test_idx.size)
            metrics["runtime_train_s"] = float(train_s)
            metrics["runtime_predict_s"] = float(pred_s)
            results[label] = metrics
        if results:
            results["_mode"] = "real"
            return results

    for label, factor in _synthetic_lf_factors(cfg).items():
        lf_cube, shape_lf = coarsen_event_cube(hf, shape_hf, factor)
        train_idx, test_idx, split_name = resolve_train_test_indices(
            event_ids, cfg, "lsg_ts"
        )
        m = LSGTSModel(cfg)
        t0 = time.perf_counter()
        m.fit(
            hf[train_idx],
            lf_cube[train_idx],
            terrain,
            shape_hf,
            shape_lf,
        )
        train_s = time.perf_counter() - t0
        t1 = time.perf_counter()
        pred = m.predict(
            lf_cube[test_idx],
            terrain,
            shape_hf,
            shape_lf,
        )
        pred_s = time.perf_counter() - t1
        metrics = m.evaluate(pred, hf[test_idx])
        metrics["split"] = split_name
        metrics["lf_coarsening_factor"] = factor
        metrics["lf_cell_size_m"] = int(
            cfg["hydrodynamic"]["hf_cell_size_m"] * factor
        )
        metrics["n_train"] = int(train_idx.size)
        metrics["n_test"] = int(test_idx.size)
        metrics["runtime_train_s"] = float(train_s)
        metrics["runtime_predict_s"] = float(pred_s)
        results[label] = metrics
    results["_mode"] = "synthetic"
    return results


def _requested_event_ids(cfg: dict, args) -> list[str] | None:
    """``--events E1,E2`` or ``events.include`` in the config; None means all."""
    raw = args.events if args.events else (cfg.get("events") or {}).get("include")
    if not raw:
        return None
    if isinstance(raw, str):
        raw = raw.split(",")
    ids = [str(e).strip() for e in raw if str(e).strip()]
    return ids or None


def _load_data(cfg: dict, args) -> tuple[dict, dict]:
    status = detect_real_event_data(cfg)
    if args.data is not None:
        data_path = Path(args.data)
        if not data_path.exists():
            raise FileNotFoundError(data_path)
        print(f"[LSG] Loading NPZ bundle {data_path}")
        return load_event_bundle(data_path), status

    if not args.synthetic and status.get("kind") == "fraehr" and status["available"]:
        case_root = status["case_root"]
        wanted = _requested_event_ids(cfg, args)
        print(f"[LSG] Using published Fraehr HF/LF results under {case_root}")
        print(f"      events: {wanted or status['paired_event_ids']}")
        time_reduction = getattr(args, "time_reduction", None)
        if not time_reduction:
            time_reduction = (cfg.get("ingest") or {}).get("time_reduction")
        if str(time_reduction).lower() in {"", "none", "full"}:
            time_reduction = None
        data = ingest_fraehr_case(
            case_root,
            threshold_m=float(cfg["hydrodynamic"]["depth_threshold_m"]),
            event_ids=wanted,
            time_reduction=time_reduction,
        )
        return data, status

    if not args.synthetic and status["available"]:
        lf_label = args.lf_resolution
        lf_dir = status["lf_dir"]
        if lf_label:
            mapped = (cfg.get("paths", {}).get("lf_resolutions") or {}).get(lf_label)
            if mapped:
                lf_dir = resolve_path_value(cfg, mapped)
        print(
            "[LSG] Using real HF/LF event files:\n"
            f"      HF: {status['hf_dir']}\n"
            f"      LF: {lf_dir}\n"
            f"      events: {status['paired_event_ids']}"
        )
        data = ingest_lf_hf_npz_dir(status["hf_dir"], lf_dir, strict=False)
        data["meta"] = {
            **data.get("meta", {}),
            "source": "real",
            "lf_dir": str(lf_dir),
        }
        return data, status

    reason = (
        "forced --synthetic"
        if args.synthetic
        else (
            "no paired HF/LF NPZ/NetCDF under "
            f"{status['hf_dir']} and {status['lf_dir']}"
        )
    )
    case_id = str((cfg.get("study_area") or {}).get("id") or "unknown")
    print(
        f"[LSG] Real case-study grids not used ({reason}).\n"
        f"[LSG] case={case_id}. See data/DATA_INVENTORY.md.\n"
        "[LSG] Running synthetic demo (not real hydraulics)."
    )
    syn = cfg.get("synthetic_demo")
    if args.synthetic and not syn:
        syn = dict(_MINI_SYNTHETIC)
        cfg["synthetic_demo"] = syn
    if not syn:
        raise SystemExit(
            f"No paired HF/LF files and no synthetic_demo block in this config "
            f"(case={case_id}). For Carlisle, download the Figshare dump:\n"
            f"  python scripts/download_published_benchmarks.py --dataset carlisle\n"
            "Then unzip into data/external/carlisle/. Do not run HEC-RAS yourself.\n"
            "Or pass --synthetic to run a mini in-process fixture."
        )
    data_path = Path(cfg["_project_root"]) / "data" / "synthetic" / "training_events.npz"
    if data_path.exists() and not args.regenerate_synthetic:
        data = load_event_bundle(data_path)
        data.setdefault("meta", {})["source"] = data["meta"].get("source", "synthetic")
        ids = {normalize_event_id(str(e)) for e in data["event_ids"]}
        if any(v in ids for v in ("FE21", "FE26", "FE50", "FE51")):
            return data, status
        print(
            "[LSG] Existing synthetic bundle uses non-paper event IDs; "
            "regenerating so splits.yaml applies."
        )

    data = generate_synthetic_floodplain(
        n_events=syn["n_events"],
        n_timesteps=syn["n_timesteps"],
        shape_hf=(syn["grid_ny"], syn["grid_nx"]),
        lf_factor=syn["lf_coarsening_factor"],
        seed=cfg["lsg"]["random_seed"],
    )
    save_event_bundle(
        data_path,
        data["hf_depth"],
        data["lf_depth"],
        data["terrain_hf"],
        data["shape_hf"],
        data["shape_lf"],
        data["event_ids"],
        data["meta"],
        terrain_lf=data.get("terrain_lf"),
    )
    print(f"[LSG] Wrote synthetic bundle {data_path}")
    return data, status


def _verify_reload(
    model, path: Path, lf_test, terrain, shape_hf, shape_lf, mesh=None
) -> bool:
    mesh = mesh or {}
    cls = type(model)
    loaded = cls.load_from(path, model.cfg)
    pred_a = model.predict(
        lf_test,
        terrain,
        shape_hf,
        shape_lf,
        xy_hf=mesh.get("xy_hf"),
        xy_lf=mesh.get("xy_lf"),
        terrain_lf=mesh.get("terrain_lf"),
    )
    pred_b = loaded.predict(
        lf_test,
        terrain,
        shape_hf,
        shape_lf,
        xy_hf=mesh.get("xy_hf"),
        xy_lf=mesh.get("xy_lf"),
        terrain_lf=mesh.get("terrain_lf"),
    )
    return bool(np.allclose(pred_a, pred_b, equal_nan=True, atol=1e-6))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=_ROOT / "config" / "carlisle.yaml",
    )
    parser.add_argument("--data", type=Path, default=None, help="NPZ bundle path")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Force synthetic demo even if data/raw has paired events",
    )
    parser.add_argument(
        "--regenerate-synthetic",
        action="store_true",
        help="Rebuild the synthetic NPZ bundle",
    )
    parser.add_argument(
        "--events",
        default=None,
        help="Comma-separated event ids to ingest, e.g. E2,E3,E6 (default: all paired)",
    )
    parser.add_argument(
        "--time-reduction",
        choices=("full", "max"),
        default=None,
        help=(
            "Fraehr ingest: full unsteady cubes, or per-event max depth "
            "(Summary Maximum Water Surface). Overrides ingest.time_reduction."
        ),
    )
    parser.add_argument(
        "--lf-resolution",
        choices=("lf120", "lf300"),
        default=None,
        help="Which configured LF directory to use for the main run",
    )
    args = parser.parse_args()
    cfg = load_config(args.config)
    root = Path(cfg["_project_root"])
    print(f"[LSG] project_root={root}")

    data, real_status = _load_data(cfg, args)
    hf, lf = data["hf_depth"], data["lf_depth"]
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]
    event_ids = [str(e) for e in data["event_ids"]]
    data_source_raw = str((data.get("meta") or {}).get("source", "unknown"))
    is_synthetic = data_source_raw == "synthetic" or bool(args.synthetic)
    if is_synthetic:
        cfg.setdefault("events", {})["synthetic_only"] = True
        data_source = "synthetic"
    elif data_source_raw in {"real", "fraehr"} or real_status.get("available"):
        data_source = str(data_source_raw if data_source_raw not in {"unknown", ""} else "real")
    else:
        data_source = data_source_raw

    out_dir = resolve_path(cfg, "evaluation") if "evaluation" in cfg.get("paths", {}) else root / "outputs" / "evaluation"
    models_dir = resolve_path(cfg, "models") if "models" in cfg.get("paths", {}) else root / "outputs" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    hf_cell = float(cfg["hydrodynamic"]["hf_cell_size_m"])
    syn_factor = int((cfg.get("synthetic_demo") or {}).get("lf_coarsening_factor", 4))
    lf_main_m = hf_cell * syn_factor if data_source == "synthetic" else None
    if args.lf_resolution == "lf120":
        lf_main_m = 120.0
    elif args.lf_resolution == "lf300":
        lf_main_m = 300.0

    summary: dict = {
        "project_root": str(root),
        "data_source": data_source,
        "data_mode": "synthetic" if data_source == "synthetic" else "real",
        "lsg_field": field_mode(cfg),
        "lsg_zoning": base._zoning_method(cfg),
        "gpflow_enabled": bool(gp.gpflow_available()),
        "gp_backend": "gpflow" if gp.gpflow_available() else "numpy",
        "event_ids": event_ids,
        "real_data_available": bool(real_status.get("available")),
        "resolution": {
            "hf_cell_size_m": hf_cell,
            "hf_output_cell_size_m": cfg["hydrodynamic"].get("hf_output_cell_size_m"),
            "lf_main_cell_size_m": lf_main_m,
            "lf120_m": (cfg.get("hydrodynamic", {}).get("lf_resolutions_m") or {})
            .get("lf120", {})
            .get("computational_m", 120),
            "lf300_m": (cfg.get("hydrodynamic", {}).get("lf_resolutions_m") or {})
            .get("lf300", {})
            .get("computational_m", 300),
        },
        "split_protocol": "splits.yaml / Wang et al. 2026" if data_source == "synthetic" or real_status.get("available") else "unknown",
    }

    mesh = _mesh_args(data)
    preds: dict[str, np.ndarray] = {}
    test_ids_by_variant: dict[str, list[str]] = {}
    test_idx_by_variant: dict[str, np.ndarray] = {}

    for label, cls in [("lsg_max", LSGMaxModel), ("lsg_ts", LSGTSModel)]:
        train_idx, test_idx, split_name = resolve_train_test_indices(
            event_ids, cfg, label
        )
        train_ids = [event_ids[i] for i in train_idx.tolist()]
        test_ids = [event_ids[i] for i in test_idx.tolist()]
        test_ids_by_variant[label] = test_ids
        test_idx_by_variant[label] = test_idx
        print(
            f"[LSG] {label} split={split_name} "
            f"n_train={train_idx.size} n_test={test_idx.size} "
            f"train={train_ids} test={test_ids}"
        )
        model = cls(cfg)
        metrics, pred = run_variant(
            label,
            model,
            hf[train_idx],
            lf[train_idx],
            hf[test_idx],
            lf[test_idx],
            terrain,
            shape_hf,
            shape_lf,
            test_ids,
            mesh=mesh,
        )
        state_path = models_dir / f"{label}_state.npz"
        model.save(state_path)
        reload_ok = _verify_reload(
            model,
            state_path,
            lf[test_idx],
            terrain,
            shape_hf,
            shape_lf,
            mesh=mesh,
        )
        print(f"[LSG] {label} saved {state_path} reload_ok={reload_ok}")
        metrics["split"] = split_name
        metrics["train_ids"] = train_ids
        metrics["test_ids"] = test_ids
        metrics["model_path"] = str(state_path)
        metrics["model_reload_ok"] = bool(reload_ok)
        summary[label] = metrics
        preds[label] = pred

    summary["resolution_comparison"] = lf_resolution_comparison(
        cfg, hf, terrain, shape_hf, event_ids, real_status
    )

    from lsg import evaluation
    from lsg.spatial import interpolate_lf_to_hf

    max_test_idx = test_idx_by_variant["lsg_max"]
    lf_max_up = np.nanmax(lf[max_test_idx], axis=1)
    hf_max = np.nanmax(hf[max_test_idx], axis=1)
    lf_up = interpolate_lf_to_hf(
        lf_max_up,
        shape_lf,
        shape_hf,
        terrain,
        xy_hf=mesh.get("xy_hf"),
        xy_lf=mesh.get("xy_lf"),
        dry_threshold_m=float(cfg["hydrodynamic"]["depth_threshold_m"]),
        terrain_lf=mesh.get("terrain_lf"),
    )
    thresh = float(cfg["hydrodynamic"]["depth_threshold_m"])
    wet_idx = None
    max_state_path = models_dir / "lsg_max_state.npz"
    if max_state_path.is_file():
        wet_idx = np.load(max_state_path)["wet_idx"]

    summary["lf_only_max"] = evaluation.extent_metrics(lf_up, hf_max, thresh)
    summary["score_protocol"] = {
        "threshold_m": thresh,
        "lsg_field": field_mode(cfg),
        "notes": (
            "all_cells = full HF mesh; wet_train = Fraehr Categories wet_idx "
            "(CSI unchanged vs all_cells when FAs lie inside the mask; RMSE rises). "
            "With lsg.field=wse_ext the official LSG prediction is trained EXT+WSE. "
            "lf_extent_gated remains a diagnostic only (not the model)."
        ),
        "lf_only": evaluation.dual_score_max_surface(
            lf_up, hf_max, wet_idx, thresh
        ),
    }
    for label, key in (("lsg_max", "lsg_max"), ("lsg_ts", "lsg_ts")):
        if key not in preds:
            continue
        pred_max = preds[key] if label == "lsg_max" else _max_surface(preds[key])
        summary["score_protocol"][label] = evaluation.dual_score_max_surface(
            pred_max, hf_max, wet_idx, thresh, extent_gate=lf_up
        )

    # Predictions for maps: use LSG-Max hold-out events; LSG-TS if same test IDs.
    ts_test_idx = test_idx_by_variant["lsg_ts"]
    example_path = out_dir / "pred_examples.npz"
    payload = {
        "terrain_hf": terrain,
        "shape_hf": np.array(shape_hf),
        "shape_lf": np.array(shape_lf),
        "test_ids": np.array(test_ids_by_variant["lsg_max"]),
        "hf_max": hf_max,
        "pred_lsg_max": preds["lsg_max"],
        "lf_upsampled_max": lf_up,
        "data_mode": np.array(summary["data_mode"]),
    }
    if wet_idx is not None:
        payload["wet_idx"] = wet_idx
    if np.array_equal(max_test_idx, ts_test_idx):
        payload["pred_lsg_ts_max"] = _max_surface(preds["lsg_ts"])
    np.savez_compressed(example_path, **payload)
    summary["pred_examples"] = str(example_path)

    out_file = out_dir / "workflow_summary.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(_to_jsonable(summary), f, indent=2)
    print(json.dumps(_to_jsonable(summary), indent=2))
    print(f"Results written to {out_file}")


if __name__ == "__main__":
    main()
