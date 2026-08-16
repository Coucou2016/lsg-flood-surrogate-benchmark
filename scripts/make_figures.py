#!/usr/bin/env python
"""Regenerate publication figures from saved evaluation artifacts.

Does not retrain models or re-run Carlisle/Chowilla/Burnett workflows.
Missing artifacts are skipped and reported as 未运行/缺数据.

Usage (project root):
  .\\.venv\\Scripts\\python.exe scripts/make_figures.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lsg.figstyle import (  # noqa: E402
    PALETTE,
    add_panel_label,
    apply_lsg_style,
    figsize_double,
    save_pub,
)

# ---------------------------------------------------------------------------
# Artifact registry (real paths only)
# ---------------------------------------------------------------------------

ARTIFACTS = {
    "carlisle_sgpr": _ROOT
    / "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json",
    "carlisle_global": _ROOT
    / "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext.json",
    "carlisle_hlsg": _ROOT
    / "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_residual_kmeans.json",
    "carlisle_budget": _ROOT
    / "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_budget.json",
    "carlisle_uq": _ROOT
    / "outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix_uq_calibrated.json",
    "chowilla_hlsg": _ROOT
    / "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max.json",
    "chowilla_global": _ROOT
    / "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_max.json",
    "chowilla_uq": _ROOT
    / "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max_uq_calibrated.json",
    "burnett_hlsg": _ROOT
    / "outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max.json",
    "burnett_global": _ROOT
    / "outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_global_max.json",
    "burnett_uq": _ROOT
    / "outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max_uq_calibrated.json",
    "chowilla_wet_corr": _ROOT
    / "outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_wet_correlation_max.json",
    "pred_carlisle": _ROOT / "outputs/evaluation/carlisle/pred_examples.npz",
    "pred_chowilla": _ROOT / "outputs/evaluation/chowilla/pred_examples.npz",
    "pred_burnett": _ROOT / "outputs/evaluation/burnett/pred_examples.npz",
    "geom_carlisle": _ROOT
    / "data/external/carlisle/Geometry_data/Lisflood_Geometry_data.npz",
    "geom_chowilla": _ROOT
    / "data/external/chowilla/Geometry_data/Geometry_data_HF.npz",
    "geom_burnett": _ROOT
    / "data/external/burnett/Geometry_data/Tuflow_Geometry_data.npz",
}

MASK_LABEL = "Fraehr wet_train (Categories wet_idx)"
DEPTH_TAU_M = 0.03


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def wet_train_metrics(summary: dict, variant: str) -> dict[str, float] | None:
    """Extract CSI/RMSE under the Fraehr wet_train protocol."""
    protocol = summary.get("score_protocol") or {}
    block = protocol.get(variant)
    if isinstance(block, dict) and isinstance(block.get("wet_train"), dict):
        wt = block["wet_train"]
        if "csi" in wt and "rmse" in wt:
            return {"csi": float(wt["csi"]), "rmse": float(wt["rmse"])}
    return None


def error_budget_rows(summary: dict, variant: str) -> list[dict] | None:
    block = summary.get(variant) or {}
    rows = block.get("error_budget")
    if isinstance(rows, list) and rows:
        return rows
    return None


def _bar_values(ax, x, heights, *, width, color, label=None, hatch=None):
    return ax.bar(
        x,
        heights,
        width=width,
        color=color,
        label=label,
        edgecolor="black",
        linewidth=0.4,
        hatch=hatch,
    )


# ---------------------------------------------------------------------------
# Figure 1 — cross-case CSI / RMSE
# ---------------------------------------------------------------------------

def fig_cross_case(out_dir: Path, skips: list[str]) -> list[Path]:
    import matplotlib.pyplot as plt

    cases = [
        ("Carlisle", "carlisle_sgpr"),
        ("Chowilla", "chowilla_hlsg"),
        ("Burnett", "burnett_hlsg"),
    ]
    variants = ("lf_only", "lsg_max", "lsg_ts")
    colors = {
        "lf_only": PALETTE["lf"],
        "lsg_max": PALETTE["lsg_max"],
        "lsg_ts": PALETTE["lsg_ts"],
    }
    display = {"lf_only": "LF-only", "lsg_max": "LSG-Max", "lsg_ts": "LSG-TS"}

    csi = {v: [] for v in variants}
    rmse = {v: [] for v in variants}
    case_labels: list[str] = []

    for label, key in cases:
        summary = load_json(ARTIFACTS[key])
        if summary is None:
            skips.append(f"fig01: {key} 未运行/缺数据")
            continue
        case_labels.append(label)
        for v in variants:
            proto_key = "lf_only" if v == "lf_only" else v
            m = wet_train_metrics(summary, proto_key)
            if m is None:
                skips.append(f"fig01: {label}/{proto_key} wet_train 缺数据")
                csi[v].append(np.nan)
                rmse[v].append(np.nan)
            else:
                csi[v].append(m["csi"])
                rmse[v].append(m["rmse"])

    if not case_labels:
        skips.append("fig01: no case summaries available")
        return []

    x = np.arange(len(case_labels), dtype=float)
    width = 0.25
    fig, axes = plt.subplots(1, 2, figsize=figsize_double(3.0))

    for ax, metric, ylab, ylim in (
        (axes[0], csi, "CSI (−)", (0.7, 1.02)),
        (axes[1], rmse, "RMSE (m)", None),
    ):
        for i, v in enumerate(variants):
            vals = np.asarray(metric[v], dtype=float)
            _bar_values(
                ax,
                x + (i - 1) * width,
                np.nan_to_num(vals, nan=0.0),
                width=width,
                color=colors[v],
                label=display[v],
            )
            for xi, val in zip(x + (i - 1) * width, vals):
                if not np.isfinite(val):
                    ax.text(xi, ax.get_ylim()[0] if ylim is None else ylim[0] + 0.01, "—", ha="center", fontsize=7)
        ax.set_xticks(x, case_labels)
        ax.set_ylabel(ylab)
        if ylim is not None:
            ax.set_ylim(*ylim)
        ax.set_xlabel("Case")

    axes[0].legend(loc="lower right", ncol=1)
    add_panel_label(axes[0], "(a)")
    add_panel_label(axes[1], "(b)")
    fig.suptitle(f"Cross-case skill on {MASK_LABEL}", y=1.02)
    fig.tight_layout()
    paths = save_pub(fig, out_dir / "fig01_cross_case_csi_rmse_wet_train")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------------
# Figure 2 — O1–O4 error budget
# ---------------------------------------------------------------------------

def fig_error_budget(out_dir: Path, skips: list[str]) -> list[Path]:
    import matplotlib.pyplot as plt

    # Prefer production Carlisle (sgpr_fix) budget; fall back to dedicated budget file.
    sources = [
        ("Carlisle", "LSG-Max", ARTIFACTS["carlisle_sgpr"], "lsg_max"),
        ("Carlisle", "LSG-TS", ARTIFACTS["carlisle_sgpr"], "lsg_ts"),
        ("Chowilla", "LSG-Max", ARTIFACTS["chowilla_hlsg"], "lsg_max"),
        ("Burnett", "LSG-Max", ARTIFACTS["burnett_hlsg"], "lsg_max"),
    ]
    # If Carlisle sgpr lacks budget, use budget artifact.
    probe = load_json(ARTIFACTS["carlisle_sgpr"])
    if probe is None or error_budget_rows(probe, "lsg_max") is None:
        sources[0] = ("Carlisle", "LSG-Max", ARTIFACTS["carlisle_budget"], "lsg_max")
        sources[1] = ("Carlisle", "LSG-TS", ARTIFACTS["carlisle_budget"], "lsg_ts")

    panels: list[tuple[str, str, list[dict]]] = []
    for case, variant, path, key in sources:
        summary = load_json(path)
        if summary is None:
            skips.append(f"fig02: {path.name} 未运行/缺数据")
            continue
        rows = error_budget_rows(summary, key)
        if not rows:
            skips.append(f"fig02: {case}/{variant} error_budget 缺数据")
            continue
        panels.append((case, variant, rows))

    if not panels:
        return []

    n = len(panels)
    fig, axes = plt.subplots(1, n, figsize=figsize_double(2.8 + 0.2 * n), squeeze=False)
    axes = axes[0]
    oracle_keys = ["o1_rmse", "o2_rmse", "o3_rmse", "o4_rmse"]
    oracle_labels = ["O1", "O2", "O3", "O4"]
    oracle_colors = [PALETTE["o1"], PALETTE["o2"], PALETTE["o3"], PALETTE["o4"]]

    for ax, (case, variant, rows), tag in zip(
        axes, panels, [f"({chr(97 + i)})" for i in range(n)]
    ):
        by_split = {r.get("split"): r for r in rows if isinstance(r, dict)}
        splits = [s for s in ("train", "test") if s in by_split]
        x = np.arange(len(splits), dtype=float)
        width = 0.18
        for i, (ok, ol, oc) in enumerate(zip(oracle_keys, oracle_labels, oracle_colors)):
            vals = [float(by_split[s][ok]) for s in splits]
            _bar_values(
                ax,
                x + (i - 1.5) * width,
                vals,
                width=width,
                color=oc,
                label=ol if ax is axes[0] else None,
            )
        ax.set_xticks(x, [s.capitalize() for s in splits])
        ax.set_ylabel("Depth RMSE (m)")
        ax.set_title(f"{case} · {variant}")
        add_panel_label(ax, tag)

    axes[0].legend(loc="upper left", ncol=2, fontsize=7)
    fig.suptitle("O1–O4 error budget (clipped-depth RMSE on wet_idx)", y=1.03)
    fig.tight_layout()
    paths = save_pub(fig, out_dir / "fig02_error_budget_o1o4")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------------
# Figure 3 — Global vs H-LSG A/B (+ SGPR fix on Carlisle)
# ---------------------------------------------------------------------------

def fig_global_vs_hlsg(out_dir: Path, skips: list[str]) -> list[Path]:
    import matplotlib.pyplot as plt

    rows = [
        ("Carlisle", "Global", ARTIFACTS["carlisle_global"]),
        ("Carlisle", "H-LSG", ARTIFACTS["carlisle_hlsg"]),
        ("Carlisle", "H-LSG+SGPR", ARTIFACTS["carlisle_sgpr"]),
        ("Chowilla", "Global", ARTIFACTS["chowilla_global"]),
        ("Chowilla", "H-LSG", ARTIFACTS["chowilla_hlsg"]),
        ("Burnett", "Global", ARTIFACTS["burnett_global"]),
        ("Burnett", "H-LSG", ARTIFACTS["burnett_hlsg"]),
    ]

    records: list[tuple[str, str, float, float]] = []
    for case, label, path in rows:
        summary = load_json(path)
        if summary is None:
            skips.append(f"fig03: {case}/{label} ({path.name}) 未运行/缺数据")
            continue
        m = wet_train_metrics(summary, "lsg_max")
        if m is None:
            skips.append(f"fig03: {case}/{label} wet_train 缺数据")
            continue
        records.append((case, label, m["csi"], m["rmse"]))

    if not records:
        return []

    cases = []
    for c, _, _, _ in records:
        if c not in cases:
            cases.append(c)

    fig, axes = plt.subplots(1, 2, figsize=figsize_double(3.0))
    color_map = {
        "Global": PALETTE["global"],
        "H-LSG": PALETTE["hlsg"],
        "H-LSG+SGPR": PALETTE["sgpr"],
    }

    for ax, metric_idx, ylab, ylim in (
        (axes[0], 2, "CSI (−)", (0.9, 1.01)),
        (axes[1], 3, "RMSE (m)", None),
    ):
        x = np.arange(len(cases), dtype=float)
        # group labels present per case
        labels_order = ["Global", "H-LSG", "H-LSG+SGPR"]
        width = 0.25
        for i, lab in enumerate(labels_order):
            vals = []
            for case in cases:
                hit = [r for r in records if r[0] == case and r[1] == lab]
                vals.append(hit[0][metric_idx] if hit else np.nan)
            vals_a = np.asarray(vals, dtype=float)
            finite_mask = np.isfinite(vals_a)
            if not finite_mask.any():
                continue
            _bar_values(
                ax,
                x + (i - 1) * width,
                np.where(finite_mask, vals_a, 0.0),
                width=width,
                color=color_map[lab],
                label=lab,
            )
            for xi, val, ok in zip(x + (i - 1) * width, vals_a, finite_mask):
                if not ok:
                    ax.plot(xi, 0.0, marker="x", color="0.5", markersize=5)
        ax.set_xticks(x, cases)
        ax.set_ylabel(ylab)
        if ylim is not None:
            ax.set_ylim(*ylim)
        ax.set_xlabel("Case")

    axes[0].legend(loc="lower right")
    add_panel_label(axes[0], "(a)")
    add_panel_label(axes[1], "(b)")
    fig.suptitle(
        f"Global vs H-LSG (residual_kmeans) LSG-Max · {MASK_LABEL}",
        y=1.02,
    )
    fig.tight_layout()
    paths = save_pub(fig, out_dir / "fig03_global_vs_hlsg_ab")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------------
# Figure 4 — UQ calibration
# ---------------------------------------------------------------------------

def _uq_pair(summary: dict, variant: str) -> tuple[dict | None, dict | None]:
    block = summary.get(variant) or {}
    calibrated = block.get("uq") if isinstance(block.get("uq"), dict) else None
    raw = block.get("uq_uncalibrated") if isinstance(block.get("uq_uncalibrated"), dict) else None
    return raw, calibrated


def _reliability_xy(uq: dict) -> tuple[np.ndarray, np.ndarray] | None:
    rel = uq.get("reliability")
    if not isinstance(rel, dict):
        return None
    pred = np.asarray(rel.get("predicted"), dtype=float)
    obs = np.asarray(rel.get("observed"), dtype=float)
    if pred.size == 0 or obs.size == 0:
        return None
    mask = np.isfinite(pred) & np.isfinite(obs)
    if not mask.any():
        return None
    return pred[mask], obs[mask]


def fig_uq_calibration(out_dir: Path, skips: list[str]) -> list[Path]:
    import matplotlib.pyplot as plt

    summary = load_json(ARTIFACTS["carlisle_uq"])
    if summary is None:
        skips.append("fig04: Carlisle UQ calibrated summary 未运行/缺数据")
        return []

    raw, cal = _uq_pair(summary, "lsg_max")
    if cal is None:
        skips.append("fig04: lsg_max.uq 缺数据")
        return []
    if raw is None:
        skips.append("fig04: lsg_max.uq_uncalibrated 缺数据 (before curve)")

    fig, axes = plt.subplots(1, 3, figsize=figsize_double(2.9))

    # (a) reliability
    ax = axes[0]
    ax.plot([0, 1], [0, 1], ls="--", color="0.5", lw=0.8, label="Ideal")
    if raw is not None:
        xy = _reliability_xy(raw)
        if xy is not None:
            ax.plot(xy[0], xy[1], "o-", color=PALETTE["global"], ms=4, label="Before")
    xy = _reliability_xy(cal)
    if xy is not None:
        ax.plot(xy[0], xy[1], "s-", color=PALETTE["sgpr"], ms=4, label="After crps_scale")
    ax.set_xlabel("Predicted inundation probability")
    ax.set_ylabel("Observed frequency")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="lower right", fontsize=7)
    ax.set_title("Carlisle LSG-Max reliability")
    add_panel_label(ax, "(a)")

    # (b) coverage
    ax = axes[1]
    metrics = ["coverage_90", "coverage_90_active"]
    labels = ["90% all cells", "90% active"]
    x = np.arange(len(metrics), dtype=float)
    width = 0.35
    before_vals = [
        float(raw[m]) if raw and m in raw else np.nan for m in metrics
    ]
    after_vals = [float(cal[m]) if m in cal else np.nan for m in metrics]
    if np.isfinite(before_vals).any():
        _bar_values(
            ax,
            x - width / 2,
            np.nan_to_num(before_vals, nan=0.0),
            width=width,
            color=PALETTE["global"],
            label="Before",
        )
    _bar_values(
        ax,
        x + width / 2,
        np.nan_to_num(after_vals, nan=0.0),
        width=width,
        color=PALETTE["sgpr"],
        label="After",
    )
    ax.axhline(0.9, color="0.4", ls=":", lw=0.8)
    ax.set_xticks(x, labels, rotation=15)
    ax.set_ylabel("Empirical coverage (−)")
    ax.set_ylim(0.8, 1.02)
    ax.legend(loc="lower right", fontsize=7)
    ax.set_title("Coverage")
    add_panel_label(ax, "(b)")

    # (c) CRPS before/after + other cases after-only
    ax = axes[2]
    names: list[str] = []
    before_c: list[float] = []
    after_c: list[float] = []

    def _append(case_label: str, path: Path, variant: str = "lsg_max"):
        s = load_json(path)
        if s is None:
            skips.append(f"fig04: {case_label} 未运行/缺数据")
            return
        r, c = _uq_pair(s, variant)
        if c is None or "crps" not in c:
            skips.append(f"fig04: {case_label} CRPS 缺数据")
            return
        names.append(case_label)
        before_c.append(float(r["crps"]) if r and "crps" in r else np.nan)
        after_c.append(float(c["crps"]))

    _append("Carlisle", ARTIFACTS["carlisle_uq"])
    for label, key in (
        ("Chowilla", "chowilla_uq"),
        ("Burnett", "burnett_uq"),
    ):
        path = ARTIFACTS[key]
        s = load_json(path)
        if s is None:
            # Fall back to H-LSG workflow summary (may lack before curve)
            fallback = ARTIFACTS["chowilla_hlsg" if label == "Chowilla" else "burnett_hlsg"]
            s = load_json(fallback)
            if s is None:
                skips.append(f"fig04: {label} 未运行/缺数据")
                continue
            skips.append(
                f"fig04: {label} UQ calibrated pair missing; using workflow summary"
            )
        r, c = _uq_pair(s, "lsg_max")
        if c is None or "crps" not in c:
            skips.append(f"fig04: {label} CRPS 缺数据")
            continue
        if r is None:
            skips.append(f"fig04: {label} UQ before (uncalibrated) 缺数据")
        names.append(label)
        before_c.append(float(r["crps"]) if r and "crps" in r else np.nan)
        after_c.append(float(c["crps"]))

    x = np.arange(len(names), dtype=float)
    width = 0.35
    before_a = np.asarray(before_c, dtype=float)
    after_a = np.asarray(after_c, dtype=float)
    if np.isfinite(before_a).any():
        mask = np.isfinite(before_a)
        _bar_values(
            ax,
            x[mask] - width / 2,
            before_a[mask],
            width=width,
            color=PALETTE["global"],
            label="Before",
        )
        for xi, ok in zip(x - width / 2, mask):
            if not ok:
                ax.plot(xi, 0.0, marker="x", color="0.5", markersize=5, zorder=5)
    _bar_values(
        ax,
        x + width / 2,
        after_a,
        width=width,
        color=PALETTE["sgpr"],
        label="After",
    )
    ax.set_xticks(x, names)
    ax.set_ylabel("CRPS (m)")
    ax.legend(loc="upper right", fontsize=7)
    ax.set_title("CRPS")
    add_panel_label(ax, "(c)")

    fig.suptitle("UQ calibration via global CRPS variance scale", y=1.03)
    fig.tight_layout()
    paths = save_pub(fig, out_dir / "fig04_uq_calibration_crps_scale")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------------
# Figure 5 — spatial maps
# ---------------------------------------------------------------------------

def _load_xy(geom_path: Path, n_cells: int) -> np.ndarray | None:
    if not geom_path.is_file():
        return None
    raw = np.load(geom_path, allow_pickle=True)
    if "XY_coor" not in raw.files:
        return None
    xy = np.asarray(raw["XY_coor"], dtype=np.float64)
    if xy.shape[0] != n_cells:
        # Try finite-Z keep mask as in load_geometry_npz
        z = np.asarray(raw["Z_coor"], dtype=np.float64).reshape(-1)
        keep = np.isfinite(z) & np.isfinite(xy).all(axis=1)
        xy_k = xy[keep]
        if xy_k.shape[0] == n_cells:
            return xy_k
        return None
    return xy


def _scatter_field(ax, xy, values, *, cmap, vmin=None, vmax=None, s=0.4):
    sc = ax.scatter(
        xy[:, 0],
        xy[:, 1],
        c=values,
        s=s,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        marker="s",
        linewidths=0,
        rasterized=True,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.tick_params(labelsize=7)
    return sc


def fig_spatial_maps(out_dir: Path, skips: list[str]) -> list[Path]:
    import matplotlib.pyplot as plt

    written: list[Path] = []
    specs = [
        (
            "Carlisle",
            ARTIFACTS["pred_carlisle"],
            ARTIFACTS["geom_carlisle"],
            "fig05_spatial_maps_carlisle_E1",
        ),
        (
            "Chowilla",
            ARTIFACTS["pred_chowilla"],
            ARTIFACTS["geom_chowilla"],
            "fig05_spatial_maps_chowilla_E1",
        ),
        (
            "Burnett",
            ARTIFACTS["pred_burnett"],
            ARTIFACTS["geom_burnett"],
            "fig05_spatial_maps_burnett",
        ),
    ]

    for case, pred_path, geom_path, stem in specs:
        if not pred_path.is_file():
            skips.append(f"fig05: {case} pred_examples.npz 未运行/缺数据")
            continue
        raw = np.load(pred_path, allow_pickle=True)
        test_ids = [str(x) for x in np.asarray(raw["test_ids"]).tolist()]
        idx = 0
        eid = test_ids[idx] if test_ids else "?"
        hf = np.asarray(raw["hf_max"][idx], dtype=float)
        pred = np.asarray(raw["pred_lsg_max"][idx], dtype=float)
        lf = (
            np.asarray(raw["lf_upsampled_max"][idx], dtype=float)
            if "lf_upsampled_max" in raw.files
            else None
        )
        n = hf.size
        xy = _load_xy(geom_path, n)
        if xy is None:
            skips.append(f"fig05: {case} XY geometry mismatch/缺数据")
            continue

        err = pred - hf
        wet_bin = (pred >= DEPTH_TAU_M).astype(float)

        if "inundation_prob_lsg_max" in raw.files:
            inund_vals = np.asarray(raw["inundation_prob_lsg_max"][idx], dtype=float)
            inund_title = "P(wet)"
            inund_cbar = "P(wet) (−)"
        else:
            skips.append(
                f"fig05: {case} cell-wise inundation probability field 缺数据 "
                f"(showing binary depth≥{DEPTH_TAU_M:g} m instead)"
            )
            inund_vals = wet_bin
            inund_title = f"Inundation (τ={DEPTH_TAU_M:g} m)"
            inund_cbar = "wet (−)"

        panels = [
            ("HF reference", hf, PALETTE["depth"], 0.0, None),
            ("LF upsampled", lf if lf is not None else np.full_like(hf, np.nan), PALETTE["depth"], 0.0, None),
            ("LSG-Max", pred, PALETTE["depth"], 0.0, None),
            ("Error (LSG−HF)", err, PALETTE["error"], None, None),
            (inund_title, inund_vals, PALETTE["inundation"], 0.0, 1.0),
        ]
        if lf is None:
            skips.append(f"fig05: {case} lf_upsampled_max 缺数据")

        depth_vmax = float(
            np.nanpercentile(
                np.concatenate(
                    [hf[np.isfinite(hf)], pred[np.isfinite(pred)]]
                    + ([lf[np.isfinite(lf)]] if lf is not None else [])
                ),
                99,
            )
        )
        if not np.isfinite(depth_vmax) or depth_vmax <= 0:
            depth_vmax = 1.0
        err_lim = float(np.nanpercentile(np.abs(err[np.isfinite(err)]), 99)) or 1.0

        fig, axes = plt.subplots(
            1, 5, figsize=figsize_double(3.1), constrained_layout=True
        )
        for ax, (title, vals, cmap, vmin, vmax), tag in zip(
            axes,
            panels,
            ["(a)", "(b)", "(c)", "(d)", "(e)"],
        ):
            if title.startswith("HF") or title.startswith("LF") or title.startswith("LSG"):
                vmin_i, vmax_i = 0.0, depth_vmax
            elif title.startswith("Error"):
                vmin_i, vmax_i = -err_lim, err_lim
            else:
                vmin_i, vmax_i = vmin, vmax
            sc = _scatter_field(
                ax,
                xy,
                vals,
                cmap=cmap,
                vmin=vmin_i,
                vmax=vmax_i,
                s=0.25 if n > 400_000 else 0.6,
            )
            cbar = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02, shrink=0.85)
            cbar.ax.tick_params(labelsize=6)
            if title.startswith("Error"):
                cbar.set_label("m", fontsize=7)
            elif title.startswith("P(wet)") or title.startswith("Inundation"):
                cbar.set_label(inund_cbar, fontsize=7)
            else:
                cbar.set_label("depth (m)", fontsize=7)
            ax.set_title(title, fontsize=8)
            add_panel_label(ax, tag, x=-0.05, y=1.06)
            if ax is not axes[0]:
                ax.set_ylabel("")
                ax.tick_params(labelleft=False)

        fig.suptitle(f"{case} · event {eid} · max-depth fields", y=1.02)
        # constrained_layout already applied; avoid tight_layout collision
        out_stem = stem if case != "Burnett" else f"{stem}_{eid}"
        written.extend(save_pub(fig, out_dir / out_stem))
        plt.close(fig)

    return written


# ---------------------------------------------------------------------------
# Figure 6 — zoning-method sensitivity (residual_kmeans vs wet_correlation)
# ---------------------------------------------------------------------------

def fig_zoning_sensitivity(out_dir: Path, skips: list[str]) -> list[Path]:
    import matplotlib.pyplot as plt

    rows = [
        ("residual_kmeans", ARTIFACTS["chowilla_hlsg"], PALETTE["hlsg"]),
        ("wet_correlation", ARTIFACTS["chowilla_wet_corr"], PALETTE["sgpr"]),
        ("global (none)", ARTIFACTS["chowilla_global"], PALETTE["global"]),
    ]
    labels: list[str] = []
    csi_vals: list[float] = []
    rmse_vals: list[float] = []
    colors: list[str] = []
    for lab, path, color in rows:
        summary = load_json(path)
        if summary is None:
            skips.append(f"fig06: Chowilla {lab} 未运行/缺数据")
            continue
        m = wet_train_metrics(summary, "lsg_max")
        if m is None:
            skips.append(f"fig06: Chowilla {lab} wet_train 缺数据")
            continue
        labels.append(lab)
        csi_vals.append(m["csi"])
        rmse_vals.append(m["rmse"])
        colors.append(color)

    if len(labels) < 2:
        if not any("fig06" in s for s in skips):
            skips.append("fig06: wet_correlation zoning A/B 未运行/缺数据")
        return []

    fig, axes = plt.subplots(1, 2, figsize=figsize_double(2.6))
    x = np.arange(len(labels), dtype=float)
    for xi, c, v in zip(x, colors, csi_vals):
        axes[0].bar(xi, v, width=0.55, color=c)
    axes[0].set_xticks(x, labels, rotation=15)
    axes[0].set_ylabel("CSI (−)")
    axes[0].set_ylim(0.9, 1.01)
    axes[0].set_title("Chowilla LSG-Max CSI")
    add_panel_label(axes[0], "(a)")

    for xi, c, v in zip(x, colors, rmse_vals):
        axes[1].bar(xi, v, width=0.55, color=c)
    axes[1].set_xticks(x, labels, rotation=15)
    axes[1].set_ylabel("RMSE (m)")
    axes[1].set_title("Chowilla LSG-Max RMSE")
    add_panel_label(axes[1], "(b)")

    fig.suptitle(f"Zoning-method sensitivity · {MASK_LABEL}", y=1.03)
    fig.tight_layout()
    paths = save_pub(fig, out_dir / "fig06_zoning_wet_correlation_ab")
    plt.close(fig)
    return paths


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def make_all(out_dir: Path) -> dict[str, Any]:
    meta = apply_lsg_style(force=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    skips: list[str] = []
    written: list[Path] = []
    written += fig_cross_case(out_dir, skips)
    written += fig_error_budget(out_dir, skips)
    written += fig_global_vs_hlsg(out_dir, skips)
    written += fig_uq_calibration(out_dir, skips)
    written += fig_spatial_maps(out_dir, skips)
    written += fig_zoning_sensitivity(out_dir, skips)

    # Deduplicate skip notes while preserving order
    seen: set[str] = set()
    uniq_skips: list[str] = []
    for s in skips:
        if s not in seen:
            seen.add(s)
            uniq_skips.append(s)

    report = {
        "style": meta,
        "out_dir": str(out_dir),
        "n_files": len(written),
        "files": [str(p) for p in written],
        "skips": uniq_skips,
    }
    report_path = out_dir / "figure_manifest.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=_ROOT / "outputs" / "figures",
    )
    args = parser.parse_args()
    report = make_all(args.out_dir)
    print(f"SciencePlots style applied; font={report['style']['serif_family']} "
          f"(Times New Roman={report['style']['times_new_roman']})")
    print(f"Wrote {report['n_files']} files under {report['out_dir']}")
    for p in report["files"]:
        print(f"  {p}")
    if report["skips"]:
        print("Skipped / 缺数据:")
        for s in report["skips"]:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
