"""LSG-TS: train on flood time series; derive max surface from predictions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from lsg import base, evaluation, spatial, wse_ext


class LSGTSModel:
    """Time-series LSG variant (Wang et al. 2026 — recommended)."""

    variant = "lsg_ts"

    def __init__(self, cfg: dict[str, Any]):
        self.cfg = cfg
        self.state: base.LSGState | wse_ext.DualLSGState | None = None

    @property
    def field(self) -> str:
        return wse_ext.field_mode(self.cfg)

    def fit(
        self,
        hf_depth: np.ndarray,
        lf_depth: np.ndarray,
        terrain_hf: np.ndarray,
        shape_hf: tuple[int, int],
        shape_lf: tuple[int, int],
        xy_hf: np.ndarray | None = None,
        xy_lf: np.ndarray | None = None,
        area_hf: np.ndarray | None = None,
        terrain_lf: np.ndarray | None = None,
    ) -> None:
        if self.field == "wse_ext":
            self.state = wse_ext.prepare_dual_training(
                hf_depth,
                lf_depth,
                terrain_hf,
                shape_hf,
                shape_lf,
                self.cfg,
                time_series=True,
                xy_hf=xy_hf,
                xy_lf=xy_lf,
                area_hf=area_hf,
                terrain_lf=terrain_lf,
            )
            self.state.variant = self.variant
            return
        _, _, self.state = base.prepare_training_matrix(
            hf_depth,
            lf_depth,
            terrain_hf,
            shape_hf,
            shape_lf,
            self.cfg,
            time_series=True,
            xy_hf=xy_hf,
            xy_lf=xy_lf,
            area_hf=area_hf,
            terrain_lf=terrain_lf,
        )

    def predict(
        self,
        lf_depth: np.ndarray,
        terrain_hf: np.ndarray,
        shape_hf: tuple[int, int],
        shape_lf: tuple[int, int],
        xy_hf: np.ndarray | None = None,
        xy_lf: np.ndarray | None = None,
        terrain_lf: np.ndarray | None = None,
    ) -> np.ndarray:
        if self.state is None:
            raise RuntimeError("Model not fitted.")
        n_ev, n_t, _ = lf_depth.shape
        lf_flat = lf_depth.reshape(n_ev * n_t, -1)
        if isinstance(self.state, wse_ext.DualLSGState):
            pred_flat = wse_ext.predict_dual_depth(
                lf_flat,
                terrain_hf,
                shape_hf,
                shape_lf,
                self.state,
                xy_hf=xy_hf,
                xy_lf=xy_lf,
                terrain_lf=terrain_lf,
            )
        else:
            pred_flat = base.predict_matrix(
                lf_flat,
                terrain_hf,
                shape_hf,
                shape_lf,
                self.state,
                xy_hf=xy_hf,
                xy_lf=xy_lf,
                terrain_lf=terrain_lf,
            )
        return pred_flat.reshape(n_ev, n_t, -1)

    def predict_uq(
        self,
        lf_depth: np.ndarray,
        terrain_hf: np.ndarray,
        shape_hf: tuple[int, int],
        shape_lf: tuple[int, int],
        xy_hf: np.ndarray | None = None,
        xy_lf: np.ndarray | None = None,
        terrain_lf: np.ndarray | None = None,
    ) -> dict[str, np.ndarray]:
        if self.state is None:
            raise RuntimeError("Model not fitted.")
        n_ev, n_t, _ = lf_depth.shape
        lf_flat = lf_depth.reshape(n_ev * n_t, -1)
        if isinstance(self.state, wse_ext.DualLSGState):
            fmap = wse_ext.predict_dual_uq(
                lf_flat,
                terrain_hf,
                shape_hf,
                shape_lf,
                self.state,
                xy_hf=xy_hf,
                xy_lf=xy_lf,
                terrain_lf=terrain_lf,
            )
        else:
            fmap = base.predict_matrix_uq(
                lf_flat,
                terrain_hf,
                shape_hf,
                shape_lf,
                self.state,
                xy_hf=xy_hf,
                xy_lf=xy_lf,
                terrain_lf=terrain_lf,
            )
        return {k: v.reshape(n_ev, n_t, -1) for k, v in fmap.items()}

    def predict_max_surface(
        self,
        lf_depth: np.ndarray,
        terrain_hf: np.ndarray,
        shape_hf: tuple[int, int],
        shape_lf: tuple[int, int],
        xy_hf: np.ndarray | None = None,
        xy_lf: np.ndarray | None = None,
        terrain_lf: np.ndarray | None = None,
    ) -> np.ndarray:
        ts = self.predict(
            lf_depth,
            terrain_hf,
            shape_hf,
            shape_lf,
            xy_hf=xy_hf,
            xy_lf=xy_lf,
            terrain_lf=terrain_lf,
        )
        return ts.max(axis=1)

    def evaluate(
        self,
        pred_ts: np.ndarray,
        hf_depth: np.ndarray,
    ) -> dict[str, float]:
        thresh = self.cfg["hydrodynamic"]["depth_threshold_m"]
        n_ev, n_t, _ = hf_depth.shape
        hf_flat = hf_depth.reshape(n_ev * n_t, -1)
        pred_flat = pred_ts.reshape(n_ev * n_t, -1)
        real = spatial.unpadded_rows(hf_flat)
        ts_metrics = evaluation.extent_metrics(
            pred_flat[real], hf_flat[real], thresh
        )
        max_metrics = evaluation.max_surface_metrics(
            pred_ts, hf_depth, thresh
        )
        return {f"ts_{k}": v for k, v in ts_metrics.items()} | {
            f"max_{k}": v for k, v in max_metrics.items()
        }

    def save(self, path: Path) -> None:
        if self.state is None:
            raise RuntimeError("Nothing to save.")
        if isinstance(self.state, wse_ext.DualLSGState):
            self.state.variant = self.variant
            wse_ext.save_dual_state(path, self.state, self.variant, self.cfg)
            return
        self.state.variant = self.variant
        base.save_state(path, self.state, self.variant, self.cfg)

    def load(self, path: Path) -> None:
        if wse_ext.is_dual_state_file(path):
            self.state = wse_ext.load_dual_state(path)
            return
        self.state = base.load_state(path)

    @classmethod
    def load_from(cls, path: Path, cfg: dict[str, Any]) -> "LSGTSModel":
        model = cls(cfg)
        model.load(path)
        return model
