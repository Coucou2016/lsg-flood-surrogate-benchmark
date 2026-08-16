"""Domain trimming, wet-cell masks, and LF-to-HF interpolation."""

from __future__ import annotations

import numpy as np


def unpadded_rows(depth_mat: np.ndarray) -> np.ndarray:
    """Rows that are real samples.

    Stacking events of unequal length NaN-pads the short ones; those rows are
    not simulated timesteps and must be dropped before fitting or scoring.
    """
    return ~np.isnan(depth_mat).all(axis=1)


def _nan_range(depth_cube: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-cell (min, max) ignoring the NaN pads that ragged events introduce."""
    if depth_cube.ndim == 3:
        flat = depth_cube.reshape(-1, depth_cube.shape[-1])
    else:
        flat = depth_cube
    if not np.isnan(flat).any():
        return flat.min(axis=0), flat.max(axis=0)
    return np.nanmin(flat, axis=0), np.nanmax(flat, axis=0)


def wet_cell_mask(
    depth_cube: np.ndarray,
    threshold_m: float = 0.03,
) -> np.ndarray:
    """
    Cells with varying depth across samples (time or events).

    depth_cube: (n_samples, n_cells) or (n_events, n_timesteps, n_cells)
    """
    mn, mx = _nan_range(depth_cube)
    return (mx >= threshold_m) & (mx > mn)


def always_wet_mask(depth_cube: np.ndarray, threshold_m: float = 0.03) -> np.ndarray:
    mn, _ = _nan_range(depth_cube)
    return mn >= threshold_m


def temporary_wet_mask(depth_cube: np.ndarray, threshold_m: float = 0.03) -> np.ndarray:
    mn, mx = _nan_range(depth_cube)
    return (mx >= threshold_m) & (mn < threshold_m)


def binary_extent(depth: np.ndarray, threshold_m: float = 0.03) -> np.ndarray:
    return (depth >= threshold_m).astype(np.float32)


def coarsen_grid(
    depth_hf: np.ndarray,
    shape_2d: tuple[int, int],
    factor: int,
) -> np.ndarray:
    """Block-average coarsening for synthetic structured grids."""
    ny, nx = shape_2d
    d2 = depth_hf.reshape(-1, ny, nx)
    ny_c, nx_c = ny // factor, nx // factor
    d2 = d2[:, : ny_c * factor, : nx_c * factor]
    d2 = d2.reshape(-1, ny_c, factor, nx_c, factor).mean(axis=(2, 4))
    return d2.reshape(-1, ny_c * nx_c)


def nearest_cell_indices(query_xy: np.ndarray, source_xy: np.ndarray) -> np.ndarray:
    """For each query point, index of the nearest source point (Fraehr BallTree)."""
    query = np.asarray(query_xy, dtype=np.float64)
    source = np.asarray(source_xy, dtype=np.float64)
    if query.ndim != 2 or source.ndim != 2 or query.shape[1] != 2 or source.shape[1] != 2:
        raise ValueError("xy arrays must be (n_cells, 2)")
    try:
        from scipy.spatial import cKDTree

        _, idx = cKDTree(source).query(query, k=1)
        return np.asarray(idx, dtype=int)
    except ImportError:
        delta = query[:, None, :] - source[None, :, :]
        return np.argmin(np.sum(delta * delta, axis=2), axis=1)


def interpolate_lf_to_hf_xy(
    depth_lf: np.ndarray,
    xy_lf: np.ndarray,
    xy_hf: np.ndarray,
    terrain_hf: np.ndarray | None = None,
    dry_threshold_m: float = 0.03,
    terrain_lf: np.ndarray | None = None,
) -> np.ndarray:
    """
    Map LF fields onto the HF mesh by nearest cell centre.

    Fraehr path (both terrains given): LF depth → WSE on the LF mesh → nearest
    HF cell → clip against the HF DEM → HF depth. A coarse LF cell with 1 m of
    water therefore does not flood much higher HF terrain.

    This is the ``wse_clip`` feature path (matches Fraehr
    ``interpolate_lowfidelity_data`` + ``filter_dry_areas``). Converting the
    clipped WSE back to depth is a representation choice for our depth-space EOF,
    not a second terrain subtraction: dry cells become 0 rather than staying at
    elevation as in Fraehr's WSE EOF. A future ``depth_direct`` path would skip
    the LF→WSE lift and only nearest-neighbour copy depths (legacy / synthetic).

    Without ``terrain_lf``, falls back to nearest-neighbour depth copy (legacy /
    synthetic grids that omit LF elevations).
    ``depth_lf`` is ``(n_samples, n_lf_cells)``.
    """
    idx = nearest_cell_indices(xy_hf, xy_lf)
    depth_lf = np.asarray(depth_lf, dtype=np.float64)
    z_lf = None if terrain_lf is None else np.asarray(terrain_lf, dtype=np.float64).reshape(-1)
    z_hf = None if terrain_hf is None else np.asarray(terrain_hf, dtype=np.float64).reshape(-1)

    if (
        z_lf is not None
        and z_hf is not None
        and z_lf.size == depth_lf.shape[1]
        and z_hf.size == xy_hf.shape[0]
    ):
        # Matches Fraehr interpolate_lowfidelity_data + filter_dry_areas, then
        # convert clipped WSE back to depth for our depth-space EOF pipeline.
        wse_hf = (depth_lf + z_lf)[:, idx]
        out = wse_hf - z_hf
        dry = (out < dry_threshold_m) & np.isfinite(out)
        np.putmask(out, dry, 0.0)
        return out

    out = depth_lf[:, idx]
    if z_hf is not None and z_hf.size == out.shape[1]:
        # Depth-only dry mask (no LF DEM to form a water surface).
        np.putmask(out, (out < dry_threshold_m) & np.isfinite(out), 0.0)
    return out


def interpolate_lf_to_hf(
    depth_lf: np.ndarray,
    lf_shape: tuple[int, int],
    hf_shape: tuple[int, int],
    terrain_hf: np.ndarray,
    xy_hf: np.ndarray | None = None,
    xy_lf: np.ndarray | None = None,
    dry_threshold_m: float = 0.03,
    terrain_lf: np.ndarray | None = None,
) -> np.ndarray:
    """
    Nearest-neighbor LF → HF.

    If cell-centre coordinates are given (unstructured HEC-RAS / LISFLOOD
    meshes), use XY matching. Otherwise treat both grids as regular rasters.
    """
    if xy_hf is not None and xy_lf is not None:
        return interpolate_lf_to_hf_xy(
            depth_lf,
            xy_lf,
            xy_hf,
            terrain_hf,
            dry_threshold_m,
            terrain_lf=terrain_lf,
        )

    n_samples = depth_lf.shape[0]
    ny_lf, nx_lf = lf_shape
    ny_hf, nx_hf = hf_shape
    out = np.zeros((n_samples, ny_hf * nx_hf), dtype=np.float64)
    terrain_2d = np.asarray(terrain_hf, dtype=np.float64).reshape(ny_hf, nx_hf)
    z_lf = None
    if terrain_lf is not None:
        z_lf = np.asarray(terrain_lf, dtype=np.float64).reshape(ny_lf, nx_lf)
    elif terrain_hf.size == ny_hf * nx_hf:
        # Synthetic structured case: block-average HF DEM onto the LF grid.
        z_lf = coarsen_grid(
            np.asarray(terrain_hf, dtype=np.float64).reshape(1, -1),
            hf_shape,
            max(ny_hf // ny_lf, 1) if ny_lf else 1,
        ).reshape(ny_lf, nx_lf)

    yi = (np.arange(ny_hf) * ny_lf // ny_hf).astype(int)
    xi = (np.arange(nx_hf) * nx_lf // nx_hf).astype(int)
    for s in range(n_samples):
        lf_2d = depth_lf[s].reshape(ny_lf, nx_lf)
        if z_lf is not None:
            wse_lf = lf_2d + z_lf
            wse_hf = wse_lf[np.ix_(yi, xi)]
            hf_2d = wse_hf - terrain_2d
            dry = (hf_2d < dry_threshold_m) & np.isfinite(hf_2d)
            hf_2d = np.where(dry, 0.0, hf_2d)
        else:
            hf_2d = lf_2d[np.ix_(yi, xi)]
        out[s] = hf_2d.ravel()
    return out


def cell_areas_uniform(shape_2d: tuple[int, int], cell_size_m: float) -> np.ndarray:
    ny, nx = shape_2d
    return np.full(ny * nx, cell_size_m**2, dtype=np.float64)


def sqrt_area_weights(areas: np.ndarray) -> np.ndarray:
    return np.sqrt(areas)
