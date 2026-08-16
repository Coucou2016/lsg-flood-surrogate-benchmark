#!/usr/bin/env python
"""Plot CSI/POD/RMSE, LF resolution, and example inundation maps.

Reads outputs from scripts/run_lsg_workflow.py. Titles mark synthetic demos.

Usage (from project root):
  python scripts/plot_workflow_results.py
  python scripts/plot_workflow_results.py --summary outputs/evaluation/workflow_summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _load_summary(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _title_prefix(summary: dict) -> str:
    mode = str(summary.get("data_mode") or summary.get("data_source") or "")
    if mode == "synthetic":
        return "synthetic demo — "
    return ""


def _metric(block: dict | None, *keys: str) -> float | None:
    if not block:
        return None
    for key in keys:
        if key in block and isinstance(block[key], (int, float)):
            return float(block[key])
    return None


def plot_results(summary: dict, examples_path: Path | None, out_dir: Path) -> list[Path]:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required for plots. pip install matplotlib"
        ) from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = _title_prefix(summary)
    written: list[Path] = []

    ts = summary.get("lsg_ts") or {}
    mx = summary.get("lsg_max") or {}
    lf_only = summary.get("lf_only_max") or {}
    labels = ["LSG-TS (max)", "LSG-Max", "LF-only"]
    csi = [
        _metric(ts, "eval_csi", "max_csi"),
        _metric(mx, "csi"),
        _metric(lf_only, "csi"),
    ]
    pod = [
        _metric(ts, "eval_pod", "max_pod"),
        _metric(mx, "pod"),
        _metric(lf_only, "pod"),
    ]
    rmse = [
        _metric(ts, "eval_rmse", "max_rmse"),
        _metric(mx, "rmse"),
        _metric(lf_only, "rmse"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4))
    for ax, values, name, ylim in (
        (axes[0], csi, "CSI", (0, 1)),
        (axes[1], pod, "POD", (0, 1)),
        (axes[2], rmse, "RMSE (m)", None),
    ):
        ax.bar(labels, [0 if v is None else v for v in values], color=["#1f77b4", "#ff7f0e", "#7f7f7f"])
        ax.set_title(name)
        ax.tick_params(axis="x", rotation=20)
        if ylim is not None:
            ax.set_ylim(*ylim)
    fig.suptitle(f"{prefix}extent skill (hold-out)")
    fig.tight_layout()
    p1 = out_dir / "metrics_comparison.png"
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    written.append(p1)

    res = summary.get("resolution_comparison") or {}
    res_labels, res_csi, res_pod, res_rmse = [], [], [], []
    for key in ("lf120", "lf300"):
        block = res.get(key)
        if not isinstance(block, dict) or "error" in block:
            continue
        res_labels.append(key.upper())
        res_csi.append(_metric(block, "eval_csi", "max_csi", "ts_csi") or 0.0)
        res_pod.append(_metric(block, "eval_pod", "max_pod", "ts_pod") or 0.0)
        res_rmse.append(_metric(block, "eval_rmse", "max_rmse", "ts_rmse") or 0.0)
    if res_labels:
        x = np.arange(len(res_labels))
        width = 0.25
        fig, ax = plt.subplots(figsize=(6.5, 3.6))
        ax.bar(x - width, res_csi, width, label="CSI")
        ax.bar(x, res_pod, width, label="POD")
        ax.bar(x + width, res_rmse, width, label="RMSE")
        ax.set_xticks(x, res_labels)
        ax.set_ylim(0, max(1.0, max(res_rmse + [1.0])))
        ax.legend()
        ax.set_title(f"{prefix}LF120 vs LF300 (LSG-TS)")
        fig.tight_layout()
        p2 = out_dir / "resolution_comparison.png"
        fig.savefig(p2, dpi=150)
        plt.close(fig)
        written.append(p2)

    hold = (mx.get("holdout") or ts.get("holdout") or {})
    if hold:
        events = list(hold.keys())
        ve_labels = [
            hold[e].get("ve_label") or e for e in events
        ]
        ve_csi = [_metric(hold[e], "csi") or 0.0 for e in events]
        fig, ax = plt.subplots(figsize=(6.0, 3.4))
        ax.bar(ve_labels, ve_csi, color="#2ca02c")
        ax.set_ylim(0, 1)
        ax.set_ylabel("CSI")
        ax.set_title(f"{prefix}VE1–VE4 hold-out CSI (LSG-Max)")
        fig.tight_layout()
        p3 = out_dir / "holdout_ve_csi.png"
        fig.savefig(p3, dpi=150)
        plt.close(fig)
        written.append(p3)

    if examples_path and examples_path.is_file():
        raw = np.load(examples_path, allow_pickle=True)
        shape_hf = tuple(int(v) for v in raw["shape_hf"].tolist())
        ny, nx = shape_hf
        test_ids = [str(x) for x in raw["test_ids"].tolist()]
        idx = 0
        panels = [("HF (ref)", np.asarray(raw["hf_max"])[idx].reshape(ny, nx))]
        if "pred_lsg_ts_max" in raw.files:
            panels.append(("LSG-TS", np.asarray(raw["pred_lsg_ts_max"])[idx].reshape(ny, nx)))
        panels.append(("LSG-Max", np.asarray(raw["pred_lsg_max"])[idx].reshape(ny, nx)))
        if "lf_upsampled_max" in raw.files:
            panels.append(("LF upsampled", np.asarray(raw["lf_upsampled_max"])[idx].reshape(ny, nx)))
        vmax = max(float(np.nanmax(a)) for _, a in panels) or 1.0
        fig, axes = plt.subplots(
            1, len(panels), figsize=(3.2 * len(panels), 3.4), constrained_layout=True
        )
        if len(panels) == 1:
            axes = [axes]
        for ax, (title, arr) in zip(axes, panels):
            im = ax.imshow(arr, origin="lower", cmap="Blues", vmin=0, vmax=vmax)
            ax.set_title(title)
            ax.set_xticks([])
            ax.set_yticks([])
        fig.colorbar(im, ax=list(axes), fraction=0.046, pad=0.04, label="depth (m)")
        eid = test_ids[idx] if test_ids else "?"
        fig.suptitle(f"{prefix}example inundation ({eid})")
        p4 = out_dir / "example_inundation.png"
        fig.savefig(p4, dpi=150)
        plt.close(fig)
        written.append(p4)

    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        type=Path,
        default=_ROOT / "outputs" / "evaluation" / "workflow_summary.json",
    )
    parser.add_argument(
        "--examples",
        type=Path,
        default=None,
        help="pred_examples.npz (defaults to path in the summary JSON)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=_ROOT / "outputs" / "figures",
    )
    args = parser.parse_args()
    summary = _load_summary(args.summary)
    examples = args.examples
    if examples is None:
        listed = summary.get("pred_examples")
        examples = Path(listed) if listed else args.summary.parent / "pred_examples.npz"
    paths = plot_results(summary, examples, args.out_dir)
    for path in paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
