"""Evaluation metrics (RMSE, CSI, POD, RFA) per Fraehr et al. (2022).

Scoring notes
-------------
* Threshold is water depth ≥ ``threshold_m`` (default 0.03 m), equivalent to
  Fraehr ``convertWSE2binary`` / ``ws2wd`` with the same tolerance.
* CSI / POD / RFA ignore correct negatives, so restricting to the training
  wet-cell mask (``wet_idx``) does **not** change CSI if all hits/misses/FAs
  already lie inside that mask. RMSE **does** change because dry zeros dilute
  the domain-wide mean.
* Fraehr ``Evaluation.py`` scores max flood-extent CSI and time-series WSE RMSE
  on ``wet_idx`` only, after combining a separate EXT model with WSE. This
  module scores depth fields; use ``gate_by_extent`` only as a diagnostic that
  mimics EXT gating with an external extent map (e.g. upsampled LF).
"""

from __future__ import annotations

import numpy as np


def rmse(pred: np.ndarray, ref: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - ref) ** 2)))


def contingency_table(
    pred_depth: np.ndarray,
    ref_depth: np.ndarray,
    threshold_m: float = 0.03,
) -> dict[str, int]:
    pred_wet = pred_depth >= threshold_m
    ref_wet = ref_depth >= threshold_m
    hits = int(np.sum(pred_wet & ref_wet))
    misses = int(np.sum(~pred_wet & ref_wet))
    false_alarms = int(np.sum(pred_wet & ~ref_wet))
    correct_neg = int(np.sum(~pred_wet & ~ref_wet))
    return {
        "hits": hits,
        "misses": misses,
        "false_alarms": false_alarms,
        "correct_negatives": correct_neg,
    }


def pod(ct: dict[str, int]) -> float:
    denom = ct["hits"] + ct["misses"]
    return ct["hits"] / denom if denom else 0.0


def rfa(ct: dict[str, int]) -> float:
    denom = ct["hits"] + ct["false_alarms"]
    return ct["false_alarms"] / denom if denom else 0.0


def csi(ct: dict[str, int]) -> float:
    denom = ct["hits"] + ct["misses"] + ct["false_alarms"]
    return ct["hits"] / denom if denom else 0.0


def _select_cells(
    pred_depth: np.ndarray,
    ref_depth: np.ndarray,
    cell_mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    if cell_mask is None:
        return pred_depth, ref_depth
    mask = np.asarray(cell_mask)
    if mask.dtype != bool:
        # Index array (Fraehr wet_idx) — apply on the last axis.
        if pred_depth.ndim == 1:
            return pred_depth[mask], ref_depth[mask]
        return pred_depth[..., mask], ref_depth[..., mask]
    if pred_depth.shape != mask.shape and mask.ndim == 1 and pred_depth.shape[-1] == mask.shape[0]:
        return pred_depth[..., mask], ref_depth[..., mask]
    return pred_depth[mask], ref_depth[mask]


def extent_metrics(
    pred_depth: np.ndarray,
    ref_depth: np.ndarray,
    threshold_m: float = 0.03,
    cell_mask: np.ndarray | None = None,
) -> dict[str, float]:
    """CSI / POD / RFA / RMSE on depth fields (optionally masked to wet cells)."""
    pred_depth, ref_depth = _select_cells(pred_depth, ref_depth, cell_mask)
    ct = contingency_table(pred_depth, ref_depth, threshold_m)
    return {
        "pod": pod(ct),
        "rfa": rfa(ct),
        "csi": csi(ct),
        "rmse": rmse(pred_depth, ref_depth),
        **{f"ct_{k}": v for k, v in ct.items()},
    }


def max_surface_metrics(
    pred_ts: np.ndarray,
    ref_ts: np.ndarray,
    threshold_m: float = 0.03,
    cell_mask: np.ndarray | None = None,
) -> dict[str, float]:
    """Compare maximum flood surfaces derived from time series."""
    if pred_ts.ndim == 3:
        pred_max = np.nanmax(pred_ts, axis=1)
        ref_max = np.nanmax(ref_ts, axis=1)
    else:
        pred_max = np.nanmax(pred_ts, axis=0)
        ref_max = np.nanmax(ref_ts, axis=0)
    return extent_metrics(pred_max, ref_max, threshold_m, cell_mask=cell_mask)


def gate_by_extent(
    depth: np.ndarray,
    extent_depth: np.ndarray,
    threshold_m: float = 0.03,
) -> np.ndarray:
    """Zero depth where ``extent_depth`` is dry (diagnostic EXT-style gate)."""
    depth = np.asarray(depth, dtype=np.float64)
    extent_depth = np.asarray(extent_depth, dtype=np.float64)
    return np.where(extent_depth >= threshold_m, depth, 0.0)


def dual_score_max_surface(
    pred_max: np.ndarray,
    ref_max: np.ndarray,
    wet_idx: np.ndarray | None,
    threshold_m: float = 0.03,
    extent_gate: np.ndarray | None = None,
) -> dict[str, dict[str, float]]:
    """Paper-facing scores: domain-wide, Fraehr wet_idx, optional extent gate."""
    out: dict[str, dict[str, float]] = {
        "all_cells": extent_metrics(pred_max, ref_max, threshold_m),
    }
    if wet_idx is not None:
        out["wet_train"] = extent_metrics(
            pred_max, ref_max, threshold_m, cell_mask=wet_idx
        )
    if extent_gate is not None:
        gated = gate_by_extent(pred_max, extent_gate, threshold_m)
        out["lf_extent_gated"] = extent_metrics(gated, ref_max, threshold_m)
        if wet_idx is not None:
            out["lf_extent_gated_wet_train"] = extent_metrics(
                gated, ref_max, threshold_m, cell_mask=wet_idx
            )
    return out
