#!/usr/bin/env python
"""Re-score saved Carlisle pred_examples with Fraehr-aligned protocols (no retrain)."""

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

from lsg import evaluation


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


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--pred",
        type=Path,
        default=_ROOT / "outputs/evaluation/carlisle/pred_examples.npz",
    )
    p.add_argument(
        "--summary",
        type=Path,
        default=_ROOT / "outputs/evaluation/carlisle/workflow_summary.json",
    )
    p.add_argument(
        "--state",
        type=Path,
        default=_ROOT / "outputs/models/carlisle/lsg_max_state.npz",
        help="LSG state NPZ used for wet_idx if missing from pred_examples",
    )
    p.add_argument("--threshold-m", type=float, default=0.03)
    args = p.parse_args()

    raw = np.load(args.pred)
    hf = raw["hf_max"]
    lf = raw["lf_upsampled_max"]
    if "wet_idx" in raw.files:
        wet_idx = raw["wet_idx"]
    else:
        wet_idx = np.load(args.state)["wet_idx"]

    thr = float(args.threshold_m)
    protocol: dict[str, Any] = {
        "threshold_m": thr,
        "source": str(args.pred),
        "notes": (
            "Re-scored from pred_examples without retrain. "
            "wet_train matches Fraehr Categories wet_idx; CSI matches all_cells "
            "when false alarms already lie inside the mask. "
            "lf_extent_gated is a diagnostic for missing LSG-EXT (not paper LSG)."
        ),
        "lf_only": evaluation.dual_score_max_surface(lf, hf, wet_idx, thr),
        "lsg_max": evaluation.dual_score_max_surface(
            raw["pred_lsg_max"], hf, wet_idx, thr, extent_gate=lf
        ),
    }
    if "pred_lsg_ts_max" in raw.files:
        protocol["lsg_ts"] = evaluation.dual_score_max_surface(
            raw["pred_lsg_ts_max"], hf, wet_idx, thr, extent_gate=lf
        )

    summary: dict[str, Any] = {}
    if args.summary.is_file():
        with args.summary.open(encoding="utf-8") as f:
            summary = json.load(f)
    summary["score_protocol"] = protocol
    # Keep legacy top-level keys as all_cells for backward compatibility.
    summary["lf_only_max"] = protocol["lf_only"]["all_cells"]
    if "lsg_max" in summary and "all_cells" in protocol["lsg_max"]:
        # Do not overwrite trained metrics block; attach pointers only.
        summary["lsg_max"]["fraehr_aligned"] = protocol["lsg_max"]
    if "lsg_ts" in summary and "lsg_ts" in protocol:
        summary["lsg_ts"]["fraehr_aligned"] = protocol["lsg_ts"]

    # Persist wet_idx into pred_examples for later runs.
    payload = {k: raw[k] for k in raw.files}
    payload["wet_idx"] = wet_idx
    np.savez_compressed(args.pred, **payload)

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    with args.summary.open("w", encoding="utf-8") as f:
        json.dump(_to_jsonable(summary), f, indent=2)

    def _line(name: str, block: dict[str, float]) -> str:
        return (
            f"  {name}: CSI={block['csi']:.4f} RMSE={block['rmse']:.4f} "
            f"RFA={block['rfa']:.4f} POD={block['pod']:.4f}"
        )

    print("Fraehr-aligned re-score (no retrain)")
    for model in ("lf_only", "lsg_max", "lsg_ts"):
        if model not in protocol:
            continue
        print(model)
        for key in ("all_cells", "wet_train", "lf_extent_gated"):
            if key in protocol[model]:
                print(_line(key, protocol[model][key]))
    print(f"Updated {args.summary}")


if __name__ == "__main__":
    main()
