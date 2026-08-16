#!/usr/bin/env python
"""Diagnose Burnett H-LSG O2−O1 improvement vs worse depth RMSE (O4).

Loads saved global + H-LSG dual states and attributes wet-train depth error by
EXT-gate agreement. Reuses published O1–O4 from existing summary JSONs (no
oracle recompute — that path is RAM-heavy on Burnett).
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

from lsg import evaluation, zoning
from lsg.base import capacity_snapshot
from lsg.config import load_config
from lsg.data import resolve_train_test_indices
from lsg.lsg_max import LSGMaxModel
from lsg.wse_ext import DualLSGState, _predict_extent_matrix, _predict_wse_matrix

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


def _rmse(a: np.ndarray, b: np.ndarray) -> float:
    d = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    return float(np.sqrt(np.mean(d * d)))


def _load_budget(summary_path: Path) -> dict:
    d = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = d.get("lsg_max", {}).get("error_budget") or []
    test = [r for r in rows if r.get("split") == "test"]
    train = [r for r in rows if r.get("split") == "train"]
    return {
        "test": test[0] if test else {},
        "train": train[0] if train else {},
        "score_wet": d.get("score_protocol", {}).get("lsg_max", {}).get("wet_train", {}),
    }


def analyze(
    name: str,
    model: LSGMaxModel,
    hf,
    lf,
    terrain,
    shape_hf,
    shape_lf,
    mesh,
    test_idx,
    budget_summary: Path,
) -> dict:
    dual = model.state
    assert isinstance(dual, DualLSGState)
    hf_test = hf[test_idx]
    lf_test = lf[test_idx]
    hf_max = _max_surface(hf_test)
    lf_max = _max_surface(lf_test)
    pred = model.predict(
        lf_test,
        terrain,
        shape_hf,
        shape_lf,
        xy_hf=mesh.get("xy_hf"),
        xy_lf=mesh.get("xy_lf"),
        terrain_lf=mesh.get("terrain_lf"),
    )
    pred_max = _max_surface(pred) if pred.ndim == 3 else pred
    thresh = float(dual.depth_threshold_m)
    wet = np.asarray(dual.wet_idx, dtype=np.int64)
    m_wet = evaluation.extent_metrics(pred_max[:, wet], hf_max[:, wet], thresh)

    ext_max = _predict_extent_matrix(
        lf_max,
        terrain,
        shape_hf,
        shape_lf,
        dual,
        mesh.get("xy_hf"),
        mesh.get("xy_lf"),
        mesh.get("terrain_lf"),
        thresh,
    )
    wse_max = _predict_wse_matrix(
        lf_max,
        terrain,
        shape_hf,
        shape_lf,
        dual.wse,
        mesh.get("xy_hf"),
        mesh.get("xy_lf"),
        mesh.get("terrain_lf"),
        thresh,
        return_var=False,
    )
    assert isinstance(wse_max, np.ndarray)
    z = np.asarray(terrain, dtype=np.float64).reshape(-1)
    # WSE floor clip: production uses where(WSE > Z+τ, WSE, Z)
    wse_wet = wse_max[:, wet]
    z_wet = z[wet]
    clipped = wse_wet <= (z_wet + thresh)
    depth_from_wse = np.maximum(wse_wet - z_wet, 0.0)
    depth_from_wse = np.where(depth_from_wse < thresh, 0.0, depth_from_wse)

    truth_ext = (hf_max >= thresh).astype(np.float64)
    pred_ext = (ext_max >= float(dual.extent_binary_threshold)).astype(np.float64)
    af = np.asarray(dual.af_idx, dtype=np.int64)
    if af.size:
        pred_ext[:, af] = 1.0

    te = truth_ext[:, wet]
    pe = pred_ext[:, wet]
    err = pred_max[:, wet] - hf_max[:, wet]
    both_wet = (te >= 0.5) & (pe >= 0.5)
    gate_miss = (te >= 0.5) & (pe < 0.5)
    gate_fa = (te < 0.5) & (pe >= 0.5)
    both_dry = (te < 0.5) & (pe < 0.5)

    def _rmse_mask(mask: np.ndarray) -> float:
        if not np.any(mask):
            return float("nan")
        d = err[mask]
        return float(np.sqrt(np.mean(d * d)))

    # Residual EC amplitude on train vs test (overfit probe)
    hier = zoning.hier_from_state(dual.wse)
    res_n = hier.residual_n_modes if hier is not None else []
    bud = _load_budget(budget_summary)
    test_b = bud["test"]
    train_b = bud["train"]

    return {
        "label": name,
        "zone_method": str(getattr(dual.wse, "zone_method", "none")),
        "capacity": capacity_snapshot(dual),
        "csi_wet": m_wet["csi"],
        "rmse_wet": m_wet["rmse"],
        "ext_cell_agree": float(np.mean(pred_ext == truth_ext)),
        "frac_wse_floor_clipped_wet": float(np.mean(clipped)),
        "rmse_wse_depth_ungated_wet": _rmse(depth_from_wse, hf_max[:, wet]),
        "rmse_both_wet": _rmse_mask(both_wet),
        "rmse_gate_miss": _rmse_mask(gate_miss),
        "rmse_gate_fa": _rmse_mask(gate_fa),
        "rmse_both_dry": _rmse_mask(both_dry),
        "frac_both_wet": float(np.mean(both_wet)),
        "frac_gate_miss": float(np.mean(gate_miss)),
        "frac_gate_fa": float(np.mean(gate_fa)),
        "residual_n_modes": list(res_n),
        "budget_from_summary": {
            "path": str(budget_summary),
            "test_o1": test_b.get("o1_rmse"),
            "test_o2": test_b.get("o2_rmse"),
            "test_o3": test_b.get("o3_rmse"),
            "test_o4": test_b.get("o4_rmse"),
            "test_o2_minus_o1": test_b.get("o2_minus_o1"),
            "train_o4": train_b.get("o4_rmse"),
            "train_o2_minus_o1": train_b.get("o2_minus_o1"),
            "o4_minus_o2_test": (
                None
                if test_b.get("o4_rmse") is None or test_b.get("o2_rmse") is None
                else float(test_b["o4_rmse"]) - float(test_b["o2_rmse"])
            ),
            "o4_minus_o3_test": (
                None
                if test_b.get("o4_rmse") is None or test_b.get("o3_rmse") is None
                else float(test_b["o4_rmse"]) - float(test_b["o3_rmse"])
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_ROOT / "config" / "burnett.yaml")
    parser.add_argument(
        "--hlsg-model",
        type=Path,
        default=_ROOT / "outputs" / "models" / "burnett" / "lsg_max_state.npz",
    )
    parser.add_argument(
        "--global-model",
        type=Path,
        default=_ROOT / "outputs" / "models" / "burnett_global" / "lsg_max_state.npz",
    )
    parser.add_argument(
        "--hlsg-summary",
        type=Path,
        default=_ROOT
        / "outputs"
        / "evaluation"
        / "burnett"
        / "workflow_summary_grp1_wse_ext_hlsg_max.json",
    )
    parser.add_argument(
        "--global-summary",
        type=Path,
        default=_ROOT
        / "outputs"
        / "evaluation"
        / "burnett"
        / "workflow_summary_grp1_wse_ext_global_max.json",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=_ROOT
        / "outputs"
        / "evaluation"
        / "burnett"
        / "diagnose_hlsg_o2_vs_rmse.json",
    )
    args = parser.parse_args()
    t0 = time.perf_counter()
    cfg = load_config(args.config)
    print("[diagnose] loading Burnett Fraehr max cubes...", flush=True)
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
    _, test_idx, split_name = resolve_train_test_indices(event_ids, cfg, "lsg_max")
    test_ids = [event_ids[i] for i in test_idx.tolist()]
    print(f"[diagnose] n_test={test_idx.size} split={split_name}", flush=True)

    rows = []
    for label, path, summary in (
        ("hlsg", args.hlsg_model, args.hlsg_summary),
        ("global", args.global_model, args.global_summary),
    ):
        print(f"[diagnose] scoring {label} from {path}", flush=True)
        model = LSGMaxModel.load_from(path, cfg)
        assert model.state is not None
        rows.append(
            analyze(
                label,
                model,
                hf,
                lf,
                terrain,
                shape_hf,
                shape_lf,
                mesh,
                test_idx,
                summary,
            )
        )
        r = rows[-1]
        print(
            f"[{label}] wet CSI={r['csi_wet']:.6f} RMSE={r['rmse_wet']:.6f} "
            f"both_wet_RMSE={r['rmse_both_wet']:.6f} "
            f"O2-O1={r['budget_from_summary']['test_o2_minus_o1']} "
            f"O4-O2={r['budget_from_summary']['o4_minus_o2_test']}",
            flush=True,
        )

    out = {
        "case": "burnett",
        "split": split_name,
        "test_ids": test_ids,
        "n_test": int(test_idx.size),
        "runtime_s": float(time.perf_counter() - t0),
        "models": {"hlsg": str(args.hlsg_model), "global": str(args.global_model)},
        "rows": rows,
        "interpretation_hooks": {
            "o2_minus_o1": "HF projection truncation gap (expressibility)",
            "o4_minus_o2": "LF projection + GP mapping + gating beyond truncated HF basis",
            "rmse_both_wet": "depth error where EXT gate and truth agree wet",
            "rmse_gate_miss": "depth error on truth-wet / pred-dry cells",
            "rmse_gate_fa": "depth error on truth-dry / pred-wet cells",
            "frac_wse_floor_clipped_wet": "share of wet cells where predicted WSE hits DEM+tau floor",
        },
    }
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"[diagnose] wrote {args.summary_out} wall_s={out['runtime_s']:.1f}", flush=True)


if __name__ == "__main__":
    main()
