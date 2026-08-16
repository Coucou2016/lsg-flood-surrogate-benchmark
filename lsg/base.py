"""Shared LSG training/prediction workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from lsg import eof, gp, spatial, uq, zoning


@dataclass
class LSGState:
    wet_idx: np.ndarray
    hf_mean: np.ndarray
    eof_modes: np.ndarray
    weights: np.ndarray | None
    n_modes: int
    gp_modes: list = field(default_factory=list)
    shape_hf: tuple[int, int] = (0, 0)
    use_sklearn_fallback: bool = False
    gp_backend: str = "numpy"
    variant: str = ""
    xy_hf: np.ndarray | None = None
    xy_lf: np.ndarray | None = None
    area_hf: np.ndarray | None = None
    terrain_lf: np.ndarray | None = None
    residual_var: np.ndarray | None = None
    eof_modes_full: np.ndarray | None = None
    zone_ids: np.ndarray | None = None
    zone_method: str = "none"
    residual_eof_modes: list = field(default_factory=list)
    residual_eof_mean: list = field(default_factory=list)
    depth_threshold_m: float = 0.03
    # Global multiplicative scale on predictive variance (UQ calibration).
    uq_var_scale: float = 1.0
    # depth (default) | extent | wse — dual path stores two states + DualLSGState
    field: str = "depth"


def _zoning_method(cfg: dict[str, Any]) -> str:
    return zoning.normalize_zoning((cfg.get("lsg") or {}).get("zoning"))


def capacity_snapshot(state: Any) -> dict[str, Any]:
    """Report retained EC / GP input dimensionality for capacity-matched A/B.

    For dual EXT+WSE states, residual zones attach to WSE only; EXT stays global.
    """
    # DualLSGState: prefer WSE branch (where H-LSG residual capacity lives).
    wse = getattr(state, "wse", None)
    ext = getattr(state, "ext", None)
    if wse is not None:
        snap_wse = capacity_snapshot(wse)
        snap_ext = capacity_snapshot(ext) if ext is not None else {}
        return {
            "field": "wse_ext",
            "wse": snap_wse,
            "ext": snap_ext,
            "gp_input_dim_wse": snap_wse.get("gp_input_dim"),
            "gp_input_dim_ext": snap_ext.get("gp_input_dim"),
            "n_modes_global_wse": snap_wse.get("n_modes_global"),
            "n_residual_ec_wse": snap_wse.get("n_residual_ec"),
        }
    n_global = int(getattr(state, "n_modes", 0) or 0)
    res_modes = list(getattr(state, "residual_eof_modes", None) or [])
    n_per = [int(np.asarray(m).shape[0]) for m in res_modes]
    n_res_ec = int(sum(n_per))
    return {
        "field": str(getattr(state, "field", "depth") or "depth"),
        "zone_method": str(getattr(state, "zone_method", "none") or "none"),
        "n_modes_global": n_global,
        "n_zones": int(len(n_per)),
        "residual_n_modes": n_per,
        "n_residual_ec": n_res_ec,
        "gp_input_dim": int(n_global + n_res_ec),
        "force_n_modes": None,  # filled by caller from cfg when known
    }



def _hier_from_state(state: LSGState) -> zoning.HierarchicalEOF | None:
    return zoning.hier_from_state(state)


def _project_ecs(wet: np.ndarray, state: LSGState) -> np.ndarray:
    hier = _hier_from_state(state)
    if hier is None:
        return eof.project_pseudo_ecs(
            wet, state.eof_modes, state.weights, state.hf_mean
        )
    ecs_g, ecs_z = zoning.project_hierarchical(
        wet, state.eof_modes, state.hf_mean, state.weights, hier
    )
    return zoning.stack_ecs(ecs_g, ecs_z)


def _reconstruct_moments(
    ecs_mean: np.ndarray,
    ecs_var: np.ndarray | None,
    state: LSGState,
) -> tuple[np.ndarray, np.ndarray | None]:
    hier = _hier_from_state(state)
    if hier is None:
        recon = eof.reconstruct_from_ecs(
            ecs_mean, state.eof_modes, state.hf_mean, state.weights
        )
        var = None
        if ecs_var is not None:
            var = eof.reconstruct_variance(
                ecs_var, state.eof_modes, state.weights, state.residual_var
            )
        return recon, var
    n_per = hier.residual_n_modes
    mean_g, mean_z = zoning.unstack_ecs(ecs_mean, state.n_modes, n_per)
    recon = zoning.reconstruct_hierarchical(
        mean_g, state.eof_modes, state.hf_mean, state.weights, mean_z, hier
    )
    var = None
    if ecs_var is not None:
        var_g, var_z = zoning.unstack_ecs(ecs_var, state.n_modes, n_per)
        var = zoning.reconstruct_hierarchical_variance(
            var_g,
            state.eof_modes,
            var_z,
            state.weights,
            hier,
            residual_var=state.residual_var,
        )
    return recon, var


def prepare_training_matrix(
    hf_cube: np.ndarray,
    lf_cube: np.ndarray,
    terrain_hf: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    cfg: dict[str, Any],
    time_series: bool,
    xy_hf: np.ndarray | None = None,
    xy_lf: np.ndarray | None = None,
    area_hf: np.ndarray | None = None,
    terrain_lf: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, LSGState]:
    """
    Build HF/LF training matrices and EOF+GP state.

    time_series=True: stack all timesteps (LSG-TS)
    time_series=False: use per-event max depth (LSG-Max)
    """
    thresh = float(cfg["hydrodynamic"]["depth_threshold_m"])
    if time_series:
        n_ev, n_t, _ = hf_cube.shape
        hf_mat = hf_cube.reshape(n_ev * n_t, -1)
        lf_mat = lf_cube.reshape(n_ev * n_t, -1)
        real = spatial.unpadded_rows(hf_mat)
        if not real.all():
            hf_mat = hf_mat[real]
            lf_mat = lf_mat[real]
    else:
        hf_mat = np.nanmax(hf_cube, axis=1)
        lf_mat = np.nanmax(lf_cube, axis=1)

    wet = spatial.wet_cell_mask(hf_mat, thresh)
    hf_wet = hf_mat[:, wet]
    lf_interp = spatial.interpolate_lf_to_hf(
        lf_mat,
        shape_lf,
        shape_hf,
        terrain_hf,
        xy_hf=xy_hf,
        xy_lf=xy_lf,
        dry_threshold_m=thresh,
        terrain_lf=terrain_lf,
    )
    lf_wet = lf_interp[:, wet]

    if area_hf is not None and np.asarray(area_hf).size == hf_mat.shape[1]:
        areas = np.asarray(area_hf, dtype=np.float64).reshape(-1)
    else:
        areas = spatial.cell_areas_uniform(
            shape_hf, cfg["hydrodynamic"]["hf_cell_size_m"]
        )
    w = (
        spatial.sqrt_area_weights(areas[wet])
        if cfg["lsg"]["weight_by_cell_area"]
        else None
    )

    pca, hf_mean = eof.fit_eof(
        hf_wet,
        weights=w,
        n_components=cfg["lsg"]["max_eof_modes"],
    )
    n_modes = eof.resolve_n_modes(pca, hf_wet.shape[0], cfg)
    modes = pca.components_[:n_modes]
    modes_full = pca.components_

    zone_method = _zoning_method(cfg)
    residual_modes: list[np.ndarray] = []
    residual_mean: list[np.ndarray] = []
    zone_ids: np.ndarray | None = None
    hier: zoning.HierarchicalEOF | None = None

    if zone_method != "none":
        hf_ecs_g = eof.project_pseudo_ecs(hf_wet, modes, w, hf_mean)
        recon_g = eof.reconstruct_from_ecs(hf_ecs_g, modes, hf_mean, w)
        resid = hf_wet - recon_g
        xy_wet = None
        if xy_hf is not None:
            xy_wet = np.asarray(xy_hf, dtype=np.float64).reshape(-1, 2)[wet]
        n_zones = int((cfg.get("lsg") or {}).get("n_zones", 4))
        n_res = int((cfg.get("lsg") or {}).get("residual_eof_modes", 3))
        seed = int((cfg.get("lsg") or {}).get("random_seed", 0))
        zone_ids = zoning.build_zones(
            resid, zone_method, n_zones, xy=xy_wet, seed=seed
        )
        hier = zoning.fit_residual_eofs(resid, zone_ids, w, n_res)
        zone_ids = hier.zone_ids
        residual_modes = hier.residual_modes
        residual_mean = hier.residual_mean
        hf_ecs_g, hf_ecs_z = zoning.project_hierarchical(
            hf_wet, modes, hf_mean, w, hier
        )
        lf_ecs_g, lf_ecs_z = zoning.project_hierarchical(
            lf_wet, modes, hf_mean, w, hier
        )
        hf_ecs = zoning.stack_ecs(hf_ecs_g, hf_ecs_z)
        lf_ecs = zoning.stack_ecs(lf_ecs_g, lf_ecs_z)
        recon_train = zoning.reconstruct_hierarchical(
            hf_ecs_g, modes, hf_mean, w, hf_ecs_z, hier
        )
    else:
        hf_ecs = eof.project_pseudo_ecs(hf_wet, modes, w, hf_mean)
        lf_ecs = eof.project_pseudo_ecs(lf_wet, modes, w, hf_mean)
        recon_train = eof.reconstruct_from_ecs(hf_ecs, modes, hf_mean, w)

    resid_var = np.mean((hf_wet - recon_train) ** 2, axis=0)

    state = LSGState(
        wet_idx=np.where(wet)[0],
        hf_mean=hf_mean,
        eof_modes=modes,
        weights=w,
        n_modes=n_modes,
        shape_hf=shape_hf,
        xy_hf=None if xy_hf is None else np.asarray(xy_hf, dtype=np.float64),
        xy_lf=None if xy_lf is None else np.asarray(xy_lf, dtype=np.float64),
        area_hf=None if area_hf is None else np.asarray(area_hf, dtype=np.float64),
        terrain_lf=(
            None if terrain_lf is None else np.asarray(terrain_lf, dtype=np.float64)
        ),
        residual_var=resid_var,
        eof_modes_full=np.asarray(modes_full, dtype=np.float64),
        zone_ids=zone_ids,
        zone_method=zone_method,
        residual_eof_modes=residual_modes,
        residual_eof_mean=residual_mean,
        depth_threshold_m=thresh,
        field="depth",
    )

    state.gp_modes = gp.train_ec_emulator(
        lf_ecs,
        hf_ecs,
        inducing_fraction=cfg["lsg"]["inducing_point_fraction"],
        min_inducing=gp.min_inducing_from_cfg(cfg),
    )
    state.use_sklearn_fallback = not gp.gpflow_available()
    state.gp_backend = "gpflow" if gp.gpflow_available() else "numpy"

    return hf_wet, lf_wet, state


def _lf_wet_from_state(
    lf_mat: np.ndarray,
    terrain_hf: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    state: LSGState,
    xy_hf: np.ndarray | None = None,
    xy_lf: np.ndarray | None = None,
    terrain_lf: np.ndarray | None = None,
) -> tuple[np.ndarray, float]:
    thresh = float(state.depth_threshold_m or 0.03)
    xy_h = xy_hf if xy_hf is not None else state.xy_hf
    xy_l = xy_lf if xy_lf is not None else state.xy_lf
    z_lf = terrain_lf if terrain_lf is not None else state.terrain_lf
    lf_interp = spatial.interpolate_lf_to_hf(
        lf_mat,
        shape_lf,
        shape_hf,
        terrain_hf,
        xy_hf=xy_h,
        xy_lf=xy_l,
        dry_threshold_m=thresh,
        terrain_lf=z_lf,
    )
    return lf_interp[:, state.wet_idx], thresh


def predict_matrix(
    lf_mat: np.ndarray,
    terrain_hf: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    state: LSGState,
    xy_hf: np.ndarray | None = None,
    xy_lf: np.ndarray | None = None,
    terrain_lf: np.ndarray | None = None,
) -> np.ndarray:
    real = spatial.unpadded_rows(lf_mat)
    if not real.all():
        out = np.full((lf_mat.shape[0], terrain_hf.size), np.nan)
        out[real] = predict_matrix(
            lf_mat[real],
            terrain_hf,
            shape_hf,
            shape_lf,
            state,
            xy_hf,
            xy_lf,
            terrain_lf,
        )
        return out
    lf_wet, thresh = _lf_wet_from_state(
        lf_mat, terrain_hf, shape_hf, shape_lf, state, xy_hf, xy_lf, terrain_lf
    )
    lf_ecs = _project_ecs(lf_wet, state)
    hf_ecs = gp.predict_ec_emulator(state.gp_modes, lf_ecs, return_var=False)
    recon_wet, _ = _reconstruct_moments(hf_ecs, None, state)
    recon_wet = uq.threshold_latent_mean(recon_wet, thresh)
    full = np.zeros((lf_mat.shape[0], terrain_hf.size), dtype=np.float64)
    full[:, state.wet_idx] = recon_wet
    return full


def predict_matrix_uq(
    lf_mat: np.ndarray,
    terrain_hf: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    state: LSGState,
    xy_hf: np.ndarray | None = None,
    xy_lf: np.ndarray | None = None,
    terrain_lf: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Latent Gaussian maps plus Tobit inundation probability and expected depth."""
    real = spatial.unpadded_rows(lf_mat)
    if not real.all():
        sub = predict_matrix_uq(
            lf_mat[real],
            terrain_hf,
            shape_hf,
            shape_lf,
            state,
            xy_hf,
            xy_lf,
            terrain_lf,
        )
        out = {}
        for key, arr in sub.items():
            padded = np.full((lf_mat.shape[0], arr.shape[1]), np.nan)
            padded[real] = arr
            out[key] = padded
        return out
    lf_wet, thresh = _lf_wet_from_state(
        lf_mat, terrain_hf, shape_hf, shape_lf, state, xy_hf, xy_lf, terrain_lf
    )
    lf_ecs = _project_ecs(lf_wet, state)
    ecs_mean, ecs_var = gp.predict_ec_emulator(
        state.gp_modes, lf_ecs, return_var=True
    )
    latent_wet, var_wet = _reconstruct_moments(ecs_mean, ecs_var, state)
    assert var_wet is not None
    n = lf_mat.shape[0]
    n_full = int(terrain_hf.size)
    latent_mean = np.zeros((n, n_full), dtype=np.float64)
    latent_var = np.zeros((n, n_full), dtype=np.float64)
    latent_mean[:, state.wet_idx] = latent_wet
    latent_var[:, state.wet_idx] = var_wet
    scale = float(getattr(state, "uq_var_scale", 1.0) or 1.0)
    if scale != 1.0:
        latent_var = uq.apply_variance_scale(latent_var, scale)
    fmap = uq.probabilistic_flood_map(latent_mean, latent_var, thresh)
    return fmap


def save_state(path: Path, state: LSGState, variant: str, cfg: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "wet_idx": state.wet_idx,
        "hf_mean": state.hf_mean,
        "eof_modes": state.eof_modes,
        "weights": state.weights if state.weights is not None else np.array([]),
        "n_modes": state.n_modes,
        "shape_hf": np.array(state.shape_hf),
        "variant": np.array(variant),
        "use_sklearn_fallback": state.use_sklearn_fallback,
        "gp_backend": np.array(state.gp_backend),
        "inducing_point_fraction": np.array(
            float(cfg.get("lsg", {}).get("inducing_point_fraction", 0.02))
        ),
        "xy_hf": state.xy_hf if state.xy_hf is not None else np.array([]),
        "xy_lf": state.xy_lf if state.xy_lf is not None else np.array([]),
        "area_hf": state.area_hf if state.area_hf is not None else np.array([]),
        "terrain_lf": (
            state.terrain_lf if state.terrain_lf is not None else np.array([])
        ),
        "residual_var": (
            state.residual_var if state.residual_var is not None else np.array([])
        ),
        "eof_modes_full": (
            state.eof_modes_full
            if state.eof_modes_full is not None
            else np.array([])
        ),
        "zone_ids": (
            state.zone_ids if state.zone_ids is not None else np.array([], dtype=np.int32)
        ),
        "zone_method": np.array(state.zone_method),
        "depth_threshold_m": np.array(float(state.depth_threshold_m)),
        "uq_var_scale": np.array(float(getattr(state, "uq_var_scale", 1.0) or 1.0)),
        "n_residual_groups": np.array(len(state.residual_eof_modes), dtype=np.int32),
        "field": np.array(str(getattr(state, "field", "depth") or "depth")),
    }
    for i, modes in enumerate(state.residual_eof_modes):
        payload[f"res_{i}_modes"] = np.asarray(modes, dtype=np.float64)
        mean_z = (
            state.residual_eof_mean[i]
            if i < len(state.residual_eof_mean)
            else np.zeros(modes.shape[1])
        )
        payload[f"res_{i}_mean"] = np.asarray(mean_z, dtype=np.float64)
    payload.update(gp.dump_gp_modes(state.gp_modes))
    np.savez_compressed(path, **payload)


def load_state(path: Path) -> LSGState:
    raw = np.load(path, allow_pickle=True)
    w = raw["weights"]
    weights = w if w.size else None
    backend = (
        str(np.asarray(raw["gp_backend"]))
        if "gp_backend" in raw.files
        else ("numpy" if bool(raw["use_sklearn_fallback"]) else "gpflow")
    )
    variant = str(np.asarray(raw["variant"])) if "variant" in raw.files else ""

    def _opt(name: str) -> np.ndarray | None:
        if name not in raw.files:
            return None
        arr = np.asarray(raw[name])
        return None if arr.size == 0 else arr

    residual_modes: list[np.ndarray] = []
    residual_mean: list[np.ndarray] = []
    n_res = 0
    if "n_residual_groups" in raw.files:
        n_res = int(np.asarray(raw["n_residual_groups"]).reshape(-1)[0])
    for i in range(n_res):
        residual_modes.append(np.asarray(raw[f"res_{i}_modes"], dtype=np.float64))
        residual_mean.append(np.asarray(raw[f"res_{i}_mean"], dtype=np.float64))

    zone_method = "none"
    if "zone_method" in raw.files:
        zone_method = str(np.asarray(raw["zone_method"]))

    depth_thr = 0.03
    if "depth_threshold_m" in raw.files:
        depth_thr = float(np.asarray(raw["depth_threshold_m"]).reshape(-1)[0])

    uq_scale = 1.0
    if "uq_var_scale" in raw.files:
        uq_scale = float(np.asarray(raw["uq_var_scale"]).reshape(-1)[0])

    field_kind = "depth"
    if "field" in raw.files:
        field_kind = str(np.asarray(raw["field"]))

    zid = _opt("zone_ids")
    return LSGState(
        wet_idx=raw["wet_idx"],
        hf_mean=raw["hf_mean"],
        eof_modes=raw["eof_modes"],
        weights=weights,
        n_modes=int(raw["n_modes"]),
        gp_modes=gp.load_gp_modes(raw),
        shape_hf=tuple(raw["shape_hf"].tolist()),
        use_sklearn_fallback=bool(raw["use_sklearn_fallback"]),
        gp_backend=backend,
        variant=variant,
        xy_hf=_opt("xy_hf"),
        xy_lf=_opt("xy_lf"),
        area_hf=_opt("area_hf"),
        terrain_lf=_opt("terrain_lf"),
        residual_var=_opt("residual_var"),
        eof_modes_full=_opt("eof_modes_full"),
        zone_ids=None if zid is None else np.asarray(zid, dtype=np.int32),
        zone_method=zone_method,
        residual_eof_modes=residual_modes,
        residual_eof_mean=residual_mean,
        depth_threshold_m=depth_thr,
        uq_var_scale=uq_scale,
        field=field_kind,
    )
