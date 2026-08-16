"""Fraehr-style dual LSG path: separate EXT + WSE models → gated depth.

Official Fraehr reconstruction (``Data_based_models.predict_recon_with_eof``)::

    EXT  = binary EOF+GP on temporary-flood cells (AF forced wet)
    WSE  = water-surface EOF+GP on wet cells
    WSE' = where(EXT == 1, WSE, Z)
    depth = max(WSE' - Z, 0)   # dry below threshold

This module trains two :class:`~lsg.base.LSGState` emulators and combines them.
It is **not** an LF-extent post-gate on a depth-only prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from lsg import base, eof, gp, spatial, uq, zoning


def normalize_field(raw: Any) -> str:
    """Map config ``lsg.field`` to ``depth`` or ``wse_ext``."""
    if raw is None:
        return "depth"
    s = str(raw).strip().lower().replace("-", "_").replace("+", "_")
    if s in {"", "depth", "wd", "water_depth"}:
        return "depth"
    if s in {"wse_ext", "ext_wse", "dual", "fraehr"}:
        return "wse_ext"
    raise ValueError(
        f"Unknown lsg.field={raw!r}; expected 'depth' or 'wse_ext'"
    )


def field_mode(cfg: dict[str, Any]) -> str:
    return normalize_field((cfg.get("lsg") or {}).get("field"))


def extent_binary_threshold(cfg: dict[str, Any]) -> float:
    hydro = cfg.get("hydrodynamic") or {}
    lsg = cfg.get("lsg") or {}
    return float(
        lsg.get(
            "extent_binary_threshold",
            hydro.get("extent_binary_threshold", 0.5),
        )
    )


def depth_to_wse(depth: np.ndarray, terrain: np.ndarray) -> np.ndarray:
    """Lift depth to water-surface elevation (dry cells stay at terrain)."""
    d = np.asarray(depth, dtype=np.float64)
    z = np.asarray(terrain, dtype=np.float64).reshape(-1)
    return d + z


def wse_to_depth(
    wse: np.ndarray,
    terrain: np.ndarray,
    threshold_m: float = 0.03,
) -> np.ndarray:
    """Fraehr ``ws2wd``: depth = WSE − Z, zero below threshold."""
    w = np.asarray(wse, dtype=np.float64)
    z = np.asarray(terrain, dtype=np.float64).reshape(-1)
    depth = w - z
    return np.where(depth < threshold_m, 0.0, depth)


def depth_to_extent(depth: np.ndarray, threshold_m: float = 0.03) -> np.ndarray:
    return (np.asarray(depth, dtype=np.float64) >= threshold_m).astype(np.float64)


def classify_extent_cells(
    depth_mat: np.ndarray,
    threshold_m: float = 0.03,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(wet_idx, af_idx, tf_idx)`` on the full mesh (Fraehr categories)."""
    wet = np.where(spatial.wet_cell_mask(depth_mat, threshold_m))[0]
    af = np.where(spatial.always_wet_mask(depth_mat, threshold_m))[0]
    tf = np.where(spatial.temporary_wet_mask(depth_mat, threshold_m))[0]
    if tf.size == 0:
        tf = wet
        af = np.array([], dtype=np.int64)
    return (
        np.asarray(wet, dtype=np.int64),
        np.asarray(af, dtype=np.int64),
        np.asarray(tf, dtype=np.int64),
    )


def _event_mats(
    hf_cube: np.ndarray,
    lf_cube: np.ndarray,
    time_series: bool,
) -> tuple[np.ndarray, np.ndarray]:
    if time_series:
        n_ev, n_t, _ = hf_cube.shape
        hf_mat = hf_cube.reshape(n_ev * n_t, -1)
        lf_mat = lf_cube.reshape(n_ev * n_t, -1)
        real = spatial.unpadded_rows(hf_mat)
        if not real.all():
            hf_mat = hf_mat[real]
            lf_mat = lf_mat[real]
        return hf_mat, lf_mat
    return np.nanmax(hf_cube, axis=1), np.nanmax(lf_cube, axis=1)


def _fit_branch(
    hf_field: np.ndarray,
    lf_field: np.ndarray,
    cell_idx: np.ndarray,
    cfg: dict[str, Any],
    shape_hf: tuple[int, int],
    *,
    field: str,
    xy_hf: np.ndarray | None,
    xy_lf: np.ndarray | None,
    area_hf: np.ndarray | None,
    terrain_lf: np.ndarray | None,
    depth_threshold_m: float,
    force_zoning_none: bool = False,
) -> base.LSGState:
    """EOF+GP on a pre-aligned field restricted to ``cell_idx``."""
    hf_wet = hf_field[:, cell_idx]
    lf_wet = lf_field[:, cell_idx]

    if area_hf is not None and np.asarray(area_hf).size == hf_field.shape[1]:
        areas = np.asarray(area_hf, dtype=np.float64).reshape(-1)
    else:
        areas = spatial.cell_areas_uniform(
            shape_hf, cfg["hydrodynamic"]["hf_cell_size_m"]
        )
    w = (
        spatial.sqrt_area_weights(areas[cell_idx])
        if cfg["lsg"]["weight_by_cell_area"]
        else None
    )

    pca, hf_mean = eof.fit_eof(
        hf_wet,
        weights=w,
        n_components=cfg["lsg"]["max_eof_modes"],
    )
    n_modes = eof.select_n_modes(pca, hf_wet.shape[0])
    modes = pca.components_[:n_modes]
    modes_full = pca.components_

    zone_method = "none" if force_zoning_none else base._zoning_method(cfg)
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
            xy_wet = np.asarray(xy_hf, dtype=np.float64).reshape(-1, 2)[cell_idx]
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
    state = base.LSGState(
        wet_idx=np.asarray(cell_idx, dtype=np.int64),
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
        depth_threshold_m=depth_threshold_m,
        field=field,
    )
    state.gp_modes = gp.train_ec_emulator(
        lf_ecs,
        hf_ecs,
        inducing_fraction=cfg["lsg"]["inducing_point_fraction"],
        min_inducing=gp.min_inducing_from_cfg(cfg),
    )
    state.use_sklearn_fallback = not gp.gpflow_available()
    state.gp_backend = "gpflow" if gp.gpflow_available() else "numpy"
    return state


@dataclass
class DualLSGState:
    """Paired EXT + WSE emulators with Fraehr-style combination."""

    ext: base.LSGState
    wse: base.LSGState
    af_idx: np.ndarray
    wet_idx: np.ndarray
    extent_binary_threshold: float = 0.5
    field: str = "wse_ext"
    variant: str = ""
    # Applied to WSE-branch latent variance inside predict_dual_uq.
    uq_var_scale: float = 1.0

    @property
    def gp_backend(self) -> str:
        return self.wse.gp_backend

    @property
    def depth_threshold_m(self) -> float:
        return float(self.wse.depth_threshold_m)

    @property
    def n_modes(self) -> int:
        return int(self.wse.n_modes)


def prepare_dual_training(
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
) -> DualLSGState:
    """Fit EXT (binary) and WSE branches from depth cubes.

    H-LSG residual zoning (``lsg.zoning``) applies to the **WSE** branch only.
    Binary EXT keeps a global EOF (``force_zoning_none``) so zone labels are not
    driven by 0/1 extent residuals.
    """
    thresh = float(cfg["hydrodynamic"]["depth_threshold_m"])
    ext_thr = extent_binary_threshold(cfg)
    hf_mat, lf_mat = _event_mats(hf_cube, lf_cube, time_series)
    terrain = np.asarray(terrain_hf, dtype=np.float64).reshape(-1)

    wet_idx, af_idx, tf_idx = classify_extent_cells(hf_mat, thresh)

    lf_depth_hf = spatial.interpolate_lf_to_hf(
        lf_mat,
        shape_lf,
        shape_hf,
        terrain,
        xy_hf=xy_hf,
        xy_lf=xy_lf,
        dry_threshold_m=thresh,
        terrain_lf=terrain_lf,
    )

    hf_ext = depth_to_extent(hf_mat, thresh)
    lf_ext = depth_to_extent(lf_depth_hf, thresh)
    hf_wse = depth_to_wse(hf_mat, terrain)
    lf_wse = depth_to_wse(lf_depth_hf, terrain)

    ext_state = _fit_branch(
        hf_ext,
        lf_ext,
        tf_idx,
        cfg,
        shape_hf,
        field="extent",
        xy_hf=xy_hf,
        xy_lf=xy_lf,
        area_hf=area_hf,
        terrain_lf=terrain_lf,
        depth_threshold_m=ext_thr,
        force_zoning_none=True,
    )
    wse_state = _fit_branch(
        hf_wse,
        lf_wse,
        wet_idx,
        cfg,
        shape_hf,
        field="wse",
        xy_hf=xy_hf,
        xy_lf=xy_lf,
        area_hf=area_hf,
        terrain_lf=terrain_lf,
        depth_threshold_m=thresh,
        force_zoning_none=False,
    )
    return DualLSGState(
        ext=ext_state,
        wse=wse_state,
        af_idx=af_idx,
        wet_idx=wet_idx,
        extent_binary_threshold=ext_thr,
        field="wse_ext",
    )


def _predict_extent_matrix(
    lf_mat: np.ndarray,
    terrain: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    dual: DualLSGState,
    xy_hf: np.ndarray | None,
    xy_lf: np.ndarray | None,
    terrain_lf: np.ndarray | None,
    dry_threshold_m: float,
) -> np.ndarray:
    """Full-mesh continuous EXT ratio with AF cells forced to 1."""
    state = dual.ext
    real = spatial.unpadded_rows(lf_mat)
    if not real.all():
        out = np.full((lf_mat.shape[0], terrain.size), np.nan)
        out[real] = _predict_extent_matrix(
            lf_mat[real],
            terrain,
            shape_hf,
            shape_lf,
            dual,
            xy_hf,
            xy_lf,
            terrain_lf,
            dry_threshold_m,
        )
        return out

    xy_h = xy_hf if xy_hf is not None else state.xy_hf
    xy_l = xy_lf if xy_lf is not None else state.xy_lf
    z_lf = terrain_lf if terrain_lf is not None else state.terrain_lf
    lf_depth_hf = spatial.interpolate_lf_to_hf(
        lf_mat,
        shape_lf,
        shape_hf,
        terrain,
        xy_hf=xy_h,
        xy_lf=xy_l,
        dry_threshold_m=dry_threshold_m,
        terrain_lf=z_lf,
    )
    lf_ext = depth_to_extent(lf_depth_hf, dry_threshold_m)
    lf_wet = lf_ext[:, state.wet_idx]
    lf_ecs = base._project_ecs(lf_wet, state)
    ecs = gp.predict_ec_emulator(state.gp_modes, lf_ecs, return_var=False)
    recon_tf, _ = base._reconstruct_moments(ecs, None, state)

    n = lf_mat.shape[0]
    full = np.zeros((n, terrain.size), dtype=np.float64)
    full[:, state.wet_idx] = recon_tf
    if dual.af_idx.size:
        full[:, dual.af_idx] = 1.0
    return full


def _predict_wse_matrix(
    lf_mat: np.ndarray,
    terrain: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    state: base.LSGState,
    xy_hf: np.ndarray | None,
    xy_lf: np.ndarray | None,
    terrain_lf: np.ndarray | None,
    dry_threshold_m: float,
    return_var: bool = False,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Full-mesh WSE (dry / non-wet cells at terrain)."""
    real = spatial.unpadded_rows(lf_mat)
    n_full = int(terrain.size)
    if not real.all():
        out = np.full((lf_mat.shape[0], n_full), np.nan)
        var_out = np.full((lf_mat.shape[0], n_full), np.nan) if return_var else None
        sub = _predict_wse_matrix(
            lf_mat[real],
            terrain,
            shape_hf,
            shape_lf,
            state,
            xy_hf,
            xy_lf,
            terrain_lf,
            dry_threshold_m,
            return_var=return_var,
        )
        if return_var:
            assert isinstance(sub, tuple)
            out[real], var_out[real] = sub
            return out, var_out
        out[real] = sub
        return out

    xy_h = xy_hf if xy_hf is not None else state.xy_hf
    xy_l = xy_lf if xy_lf is not None else state.xy_lf
    z_lf = terrain_lf if terrain_lf is not None else state.terrain_lf
    lf_depth_hf = spatial.interpolate_lf_to_hf(
        lf_mat,
        shape_lf,
        shape_hf,
        terrain,
        xy_hf=xy_h,
        xy_lf=xy_l,
        dry_threshold_m=dry_threshold_m,
        terrain_lf=z_lf,
    )
    lf_wse = depth_to_wse(lf_depth_hf, terrain)
    lf_wet = lf_wse[:, state.wet_idx]
    lf_ecs = base._project_ecs(lf_wet, state)
    if return_var:
        ecs_mean, ecs_var = gp.predict_ec_emulator(
            state.gp_modes, lf_ecs, return_var=True
        )
        recon_wet, var_wet = base._reconstruct_moments(ecs_mean, ecs_var, state)
        assert var_wet is not None
    else:
        ecs_mean = gp.predict_ec_emulator(state.gp_modes, lf_ecs, return_var=False)
        recon_wet, _ = base._reconstruct_moments(ecs_mean, None, state)
        var_wet = None

    n = lf_mat.shape[0]
    full = np.broadcast_to(terrain, (n, n_full)).copy()
    wet_z = terrain[state.wet_idx]
    recon_wet = np.where(recon_wet > wet_z + dry_threshold_m, recon_wet, wet_z)
    full[:, state.wet_idx] = recon_wet
    if return_var:
        var_full = np.zeros((n, n_full), dtype=np.float64)
        var_full[:, state.wet_idx] = var_wet
        return full, var_full
    return full


def predict_dual_depth(
    lf_mat: np.ndarray,
    terrain_hf: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    dual: DualLSGState,
    xy_hf: np.ndarray | None = None,
    xy_lf: np.ndarray | None = None,
    terrain_lf: np.ndarray | None = None,
    dry_threshold_m: float | None = None,
) -> np.ndarray:
    """Predict gated depth from LF depth rows ``(n, n_lf_cells)``."""
    dry = (
        float(dry_threshold_m)
        if dry_threshold_m is not None
        else float(dual.depth_threshold_m)
    )
    terrain = np.asarray(terrain_hf, dtype=np.float64).reshape(-1)
    ext_ratio = _predict_extent_matrix(
        lf_mat,
        terrain,
        shape_hf,
        shape_lf,
        dual,
        xy_hf=xy_hf,
        xy_lf=xy_lf,
        terrain_lf=terrain_lf,
        dry_threshold_m=dry,
    )
    wse = _predict_wse_matrix(
        lf_mat,
        terrain,
        shape_hf,
        shape_lf,
        dual.wse,
        xy_hf=xy_hf,
        xy_lf=xy_lf,
        terrain_lf=terrain_lf,
        dry_threshold_m=dry,
        return_var=False,
    )
    assert isinstance(wse, np.ndarray)
    ext_bin = ext_ratio >= dual.extent_binary_threshold
    wse_gated = np.where(ext_bin, wse, terrain)
    return wse_to_depth(wse_gated, terrain, dry)


def predict_dual_uq(
    lf_mat: np.ndarray,
    terrain_hf: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    dual: DualLSGState,
    xy_hf: np.ndarray | None = None,
    xy_lf: np.ndarray | None = None,
    terrain_lf: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """UQ from the WSE branch, hard-gated by predicted EXT."""
    dry = float(dual.depth_threshold_m)
    terrain = np.asarray(terrain_hf, dtype=np.float64).reshape(-1)
    ext_ratio = _predict_extent_matrix(
        lf_mat,
        terrain,
        shape_hf,
        shape_lf,
        dual,
        xy_hf,
        xy_lf,
        terrain_lf,
        dry,
    )
    ext_bin = ext_ratio >= dual.extent_binary_threshold
    wse_mean, wse_var = _predict_wse_matrix(
        lf_mat,
        terrain,
        shape_hf,
        shape_lf,
        dual.wse,
        xy_hf=xy_hf,
        xy_lf=xy_lf,
        terrain_lf=terrain_lf,
        dry_threshold_m=dry,
        return_var=True,
    )
    assert isinstance(wse_mean, np.ndarray) and isinstance(wse_var, np.ndarray)
    latent_mean = wse_mean - terrain
    latent_var = wse_var
    latent_mean = np.where(ext_bin, latent_mean, 0.0)
    latent_var = np.where(ext_bin, latent_var, 0.0)
    scale = float(getattr(dual, "uq_var_scale", 1.0) or 1.0)
    if scale != 1.0:
        latent_var = uq.apply_variance_scale(latent_var, scale)
    fmap = uq.probabilistic_flood_map(latent_mean, latent_var, dry)
    fmap["extent"] = ext_bin.astype(np.float64)
    return fmap


def save_dual_state(
    path: Path,
    dual: DualLSGState,
    variant: str,
    cfg: dict[str, Any],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stem = path.with_suffix("")
    ext_path = Path(str(stem) + "_ext.npz")
    wse_path = Path(str(stem) + "_wse.npz")
    dual.ext.field = "extent"
    dual.wse.field = "wse"
    base.save_state(ext_path, dual.ext, f"{variant}_ext", cfg)
    base.save_state(wse_path, dual.wse, f"{variant}_wse", cfg)
    np.savez_compressed(
        path,
        field=np.array("wse_ext"),
        variant=np.array(variant),
        af_idx=np.asarray(dual.af_idx, dtype=np.int64),
        wet_idx=np.asarray(dual.wet_idx, dtype=np.int64),
        extent_binary_threshold=np.array(float(dual.extent_binary_threshold)),
        depth_threshold_m=np.array(float(dual.depth_threshold_m)),
        uq_var_scale=np.array(float(getattr(dual, "uq_var_scale", 1.0) or 1.0)),
        ext_path=np.array(ext_path.name),
        wse_path=np.array(wse_path.name),
        gp_backend=np.array(dual.gp_backend),
    )


def load_dual_state(path: Path) -> DualLSGState:
    path = Path(path)
    raw = np.load(path, allow_pickle=True)
    field = str(np.asarray(raw["field"]))
    if field != "wse_ext":
        raise ValueError(f"Not a dual state file: field={field}")
    parent = path.parent
    ext_name = str(np.asarray(raw["ext_path"]))
    wse_name = str(np.asarray(raw["wse_path"]))
    ext = base.load_state(parent / ext_name)
    wse = base.load_state(parent / wse_name)
    ext.field = "extent"
    wse.field = "wse"
    variant = str(np.asarray(raw["variant"])) if "variant" in raw.files else ""
    uq_scale = 1.0
    if "uq_var_scale" in raw.files:
        uq_scale = float(np.asarray(raw["uq_var_scale"]).reshape(-1)[0])
    elif hasattr(wse, "uq_var_scale"):
        uq_scale = float(wse.uq_var_scale or 1.0)
    dual = DualLSGState(
        ext=ext,
        wse=wse,
        af_idx=np.asarray(raw["af_idx"], dtype=np.int64),
        wet_idx=np.asarray(raw["wet_idx"], dtype=np.int64),
        extent_binary_threshold=float(
            np.asarray(raw["extent_binary_threshold"]).reshape(-1)[0]
        ),
        field="wse_ext",
        variant=variant,
        uq_var_scale=uq_scale,
    )
    # Keep branch attribute in sync for single-state tooling.
    dual.wse.uq_var_scale = float(uq_scale)
    return dual


def is_dual_state_file(path: Path) -> bool:
    path = Path(path)
    if not path.is_file():
        return False
    try:
        raw = np.load(path, allow_pickle=True)
        return "field" in raw.files and str(np.asarray(raw["field"])) == "wse_ext"
    except Exception:
        return False
