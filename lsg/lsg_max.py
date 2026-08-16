"""LSG-Max: train directly on maximum flood surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from lsg import base, evaluation, wse_ext


class LSGMaxModel:
    """Maximum-surface LSG variant (Wang et al. 2026)."""

    variant = "lsg_max"

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
                time_series=False,
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
            time_series=False,
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
        lf_max = np.nanmax(lf_depth, axis=1)
        if isinstance(self.state, wse_ext.DualLSGState):
            return wse_ext.predict_dual_depth(
                lf_max,
                terrain_hf,
                shape_hf,
                shape_lf,
                self.state,
                xy_hf=xy_hf,
                xy_lf=xy_lf,
                terrain_lf=terrain_lf,
            )
        return base.predict_matrix(
            lf_max,
            terrain_hf,
            shape_hf,
            shape_lf,
            self.state,
            xy_hf=xy_hf,
            xy_lf=xy_lf,
            terrain_lf=terrain_lf,
        )

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
        lf_max = np.nanmax(lf_depth, axis=1)
        if isinstance(self.state, wse_ext.DualLSGState):
            return wse_ext.predict_dual_uq(
                lf_max,
                terrain_hf,
                shape_hf,
                shape_lf,
                self.state,
                xy_hf=xy_hf,
                xy_lf=xy_lf,
                terrain_lf=terrain_lf,
            )
        return base.predict_matrix_uq(
            lf_max,
            terrain_hf,
            shape_hf,
            shape_lf,
            self.state,
            xy_hf=xy_hf,
            xy_lf=xy_lf,
            terrain_lf=terrain_lf,
        )

    def evaluate(
        self,
        pred_max: np.ndarray,
        hf_depth: np.ndarray,
    ) -> dict[str, float]:
        hf_max = np.nanmax(hf_depth, axis=1)
        thresh = self.cfg["hydrodynamic"]["depth_threshold_m"]
        return evaluation.extent_metrics(pred_max, hf_max, thresh)

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
    def load_from(cls, path: Path, cfg: dict[str, Any]) -> "LSGMaxModel":
        model = cls(cfg)
        model.load(path)
        return model
