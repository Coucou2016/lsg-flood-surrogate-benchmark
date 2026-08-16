"""O1–O4 oracle error budget for LSG.



Oracle reconstructions on a wet-cell matrix:



- **O1** HF true ECs, all training-rank modes → numerical SVD floor

- **O2** HF true ECs, truncated to k modes → EOF truncation

- **O3** LF pseudo-ECs reconstructed without GP → LF expressibility

- **O4** full LSG (GP + k modes) → total error



With ``lsg.field: wse_ext``, the same hierarchy is applied *synchronously* to

the EXT and WSE branches, then combined with production gating into depth

before scoring (matched dual-path budget). O4 must match

``predict_dual_depth``.



Wang et al. (2026) LSG-Max retained 47 ECs = 47 training events (full rank).

In-sample truncation is then identically zero; O2−O1 on *held-out* events is

out-of-subspace energy, not the in-sample truncation that a full-rank train

fit cannot show. Report train and test rows separately.

"""



from __future__ import annotations



from typing import Any



import numpy as np



from lsg import eof, evaluation, gp, spatial, zoning

from lsg.lsg_max import LSGMaxModel





WANG2026_NOTE = (

    "Wang 2026 LSG-Max retained 47 ECs = 47 training events (full rank, "

    "zero in-sample truncation). O2-O1 on train ≈ 0 in that regime; "

    "O2-O1 on held-out events is out-of-subspace expressibility, not "

    "in-sample truncation."

)



DUAL_BUDGET_NOTE = (

    "dual-path wse_ext oracle; matched EXT+WSE O1–O4; "

    "metric is clipped-depth RMSE on DualLSGState.wet_idx; "

    "AF forced wet; production EXT threshold; "

    "O4 mirrors predict_dual_depth. " + WANG2026_NOTE

)





def _clip(depth: np.ndarray, threshold_m: float) -> np.ndarray:

    d = np.asarray(depth, dtype=np.float64)

    return np.where(d < threshold_m, 0.0, d)





def _rmse(a: np.ndarray, b: np.ndarray) -> float:

    return evaluation.rmse(np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64))





def _event_matrix(cube: np.ndarray, time_series: bool) -> np.ndarray:

    arr = np.asarray(cube, dtype=np.float64)

    if time_series:

        return arr.reshape(-1, arr.shape[-1])

    if arr.ndim == 3:

        return np.nanmax(arr, axis=1)

    return arr





def _oracle_stage_reconstructions(

    hf_field: np.ndarray,

    lf_field: np.ndarray,

    eof_modes_full: np.ndarray,

    n_modes: int,

    hf_mean: np.ndarray,

    weights: np.ndarray | None = None,

    gp_modes: list | None = None,

    hier: zoning.HierarchicalEOF | None = None,

) -> dict[str, np.ndarray | None]:

    """Field-space O1–O4 reconstructions (no depth conversion / RMSE)."""

    hf_field = np.asarray(hf_field, dtype=np.float64)

    lf_field = np.asarray(lf_field, dtype=np.float64)

    modes_full = np.asarray(eof_modes_full, dtype=np.float64)

    k = max(1, min(int(n_modes), modes_full.shape[0]))

    modes_k = modes_full[:k]



    ecs1 = eof.project_pseudo_ecs(hf_field, modes_full, weights, hf_mean)

    o1 = eof.reconstruct_from_ecs(ecs1, modes_full, hf_mean, weights)



    ecs2 = eof.project_pseudo_ecs(hf_field, modes_k, weights, hf_mean)

    if hier is None:

        o2 = eof.reconstruct_from_ecs(ecs2, modes_k, hf_mean, weights)

    else:

        ecs2_g, ecs2_z = zoning.project_hierarchical(

            hf_field, modes_k, hf_mean, weights, hier

        )

        o2 = zoning.reconstruct_hierarchical(

            ecs2_g, modes_k, hf_mean, weights, ecs2_z, hier

        )



    if hier is None:

        ecs3 = eof.project_pseudo_ecs(lf_field, modes_k, weights, hf_mean)

        o3 = eof.reconstruct_from_ecs(ecs3, modes_k, hf_mean, weights)

        lf_ecs_for_gp = ecs3

    else:

        ecs3_g, ecs3_z = zoning.project_hierarchical(

            lf_field, modes_k, hf_mean, weights, hier

        )

        o3 = zoning.reconstruct_hierarchical(

            ecs3_g, modes_k, hf_mean, weights, ecs3_z, hier

        )

        lf_ecs_for_gp = zoning.stack_ecs(ecs3_g, ecs3_z)



    o4 = None

    if gp_modes:

        pred = gp.predict_ec_emulator(gp_modes, lf_ecs_for_gp, return_var=False)

        if hier is None:

            o4 = eof.reconstruct_from_ecs(pred, modes_k, hf_mean, weights)

        else:

            pred_g, pred_z = zoning.unstack_ecs(pred, k, hier.residual_n_modes)

            o4 = zoning.reconstruct_hierarchical(

                pred_g, modes_k, hf_mean, weights, pred_z, hier

            )



    return {"o1": o1, "o2": o2, "o3": o3, "o4": o4, "n_modes": k}





def _score_oracle_depth_stages(

    stages: dict[str, np.ndarray | None],

    truth_field: np.ndarray,

    *,

    n_modes: int,

    n_modes_full: int,

    split: str,

    threshold_m: float,

    notes: str,

) -> dict[str, Any]:

    """Clip + RMSE for O1–O4 depth (or depth-like) fields."""

    truth = _clip(truth_field, threshold_m)

    o1 = _clip(stages["o1"], threshold_m)

    o2 = _clip(stages["o2"], threshold_m)

    o3 = _clip(stages["o3"], threshold_m)

    o4_raw = stages.get("o4")

    o4 = None if o4_raw is None else _clip(o4_raw, threshold_m)

    return {

        "split": split,

        "n_samples": int(truth.shape[0]),

        "n_cells": int(truth.shape[1]),

        "n_modes": int(n_modes),

        "n_modes_full": int(n_modes_full),

        "in_sample_full_rank": bool(n_modes >= truth.shape[0] and split == "train"),

        "o1_rmse": _rmse(o1, truth),

        "o2_rmse": _rmse(o2, truth),

        "o3_rmse": _rmse(o3, truth),

        "o4_rmse": None if o4 is None else _rmse(o4, truth),

        "o2_minus_o1": _rmse(o2, truth) - _rmse(o1, truth),

        "notes": notes,

    }





def oracle_error_budget(

    hf_wet: np.ndarray,

    lf_wet: np.ndarray,

    eof_modes_full: np.ndarray,

    n_modes: int,

    hf_mean: np.ndarray,

    weights: np.ndarray | None = None,

    gp_modes: list | None = None,

    threshold_m: float = 0.03,

    split: str = "test",

    hier: zoning.HierarchicalEOF | None = None,

) -> dict[str, Any]:

    """Score O1–O4 on already-aligned wet-cell matrices ``(n, n_wet)``."""

    stages = _oracle_stage_reconstructions(

        hf_wet,

        lf_wet,

        eof_modes_full=eof_modes_full,

        n_modes=n_modes,

        hf_mean=hf_mean,

        weights=weights,

        gp_modes=gp_modes,

        hier=hier,

    )

    k = int(stages.pop("n_modes"))  # type: ignore[arg-type]

    modes_full = np.asarray(eof_modes_full, dtype=np.float64)

    return _score_oracle_depth_stages(

        stages,

        hf_wet,

        n_modes=k,

        n_modes_full=int(modes_full.shape[0]),

        split=split,

        threshold_m=threshold_m,

        notes=WANG2026_NOTE,

    )





def _branch_oracle_stages(state: Any, hf_field: np.ndarray, lf_field: np.ndarray) -> dict:

    full = getattr(state, "eof_modes_full", None)

    if full is None or np.asarray(full).size == 0:

        full = state.eof_modes

    stages = _oracle_stage_reconstructions(

        hf_field,

        lf_field,

        eof_modes_full=full,

        n_modes=int(state.n_modes),

        hf_mean=state.hf_mean,

        weights=state.weights,

        gp_modes=list(state.gp_modes) if state.gp_modes else None,

        hier=zoning.hier_from_state(state),

    )

    return stages





def combine_dual_stage_depth(
    ext_tf: np.ndarray,
    wse_wet: np.ndarray,
    dual: Any,
    terrain: np.ndarray,
    dry_threshold_m: float,
    *,
    wet_only: bool = False,
    time_chunk: int = 256,
) -> np.ndarray:
    """Gate EXT+WSE into depth (mirrors ``predict_dual_depth``).

    When ``wet_only`` is True, return ``(n, n_wet)`` on ``dual.wse.wet_idx`` only,
    avoiding full-mesh temporaries (needed for LSG-TS oracle budgets).
    """
    from lsg.wse_ext import wse_to_depth

    terrain = np.asarray(terrain, dtype=np.float64).reshape(-1)
    ext_tf = np.asarray(ext_tf, dtype=np.float64)
    wse_wet = np.asarray(wse_wet, dtype=np.float64)
    n = int(ext_tf.shape[0])
    n_cells = int(terrain.size)
    tf_idx = np.asarray(dual.ext.wet_idx, dtype=np.int64)
    wet_idx = np.asarray(dual.wse.wet_idx, dtype=np.int64)
    af = np.asarray(dual.af_idx, dtype=np.int64)
    thr = float(dual.extent_binary_threshold)
    chunk = max(1, int(time_chunk))

    if not wet_only:
        ext_full = np.zeros((n, n_cells), dtype=np.float64)
        ext_full[:, tf_idx] = ext_tf
        if af.size:
            ext_full[:, af] = 1.0
        ext_bin = ext_full >= thr
        del ext_full
        wse_full = np.broadcast_to(terrain, (n, n_cells)).copy()
        wet_z = terrain[wet_idx]
        recon = np.where(wse_wet > wet_z + dry_threshold_m, wse_wet, wet_z)
        wse_full[:, wet_idx] = recon
        wse_gated = np.where(ext_bin, wse_full, terrain)
        del ext_bin, wse_full
        return wse_to_depth(wse_gated, terrain, dry_threshold_m)

    # Wet-only path: map EXT onto WSE wet cells without (n, n_cells) buffers.
    n_wet = int(wet_idx.size)
    wet_z = terrain[wet_idx]
    wet_inv = np.full(n_cells, -1, dtype=np.int64)
    wet_inv[wet_idx] = np.arange(n_wet, dtype=np.int64)
    out = np.empty((n, n_wet), dtype=np.float64)
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        ext_wet = np.zeros((e - s, n_wet), dtype=np.float64)
        cols = wet_inv[tf_idx]
        mask = cols >= 0
        if np.any(mask):
            ext_wet[:, cols[mask]] = ext_tf[s:e, mask]
        if af.size:
            cols_af = wet_inv[af]
            mask_af = cols_af >= 0
            if np.any(mask_af):
                ext_wet[:, cols_af[mask_af]] = 1.0
        ext_bin = ext_wet >= thr
        recon = np.where(
            wse_wet[s:e] > wet_z + dry_threshold_m, wse_wet[s:e], wet_z
        )
        wse_gated = np.where(ext_bin, recon, wet_z)
        depth = wse_gated - wet_z
        out[s:e] = np.where(depth < dry_threshold_m, 0.0, depth)
    return out


def _dual_stage_wet_depth_rmse(
    ext_tf: np.ndarray,
    wse_wet: np.ndarray,
    dual: Any,
    terrain: np.ndarray,
    dry_threshold_m: float,
    truth_clipped: np.ndarray,
    *,
    time_chunk: int = 256,
) -> float:
    """Chunked wet-only gated-depth RMSE vs pre-clipped truth (low peak RAM)."""
    terrain = np.asarray(terrain, dtype=np.float64).reshape(-1)
    ext_tf = np.asarray(ext_tf, dtype=np.float64)
    wse_wet = np.asarray(wse_wet, dtype=np.float64)
    truth = np.asarray(truth_clipped, dtype=np.float64)
    n = int(ext_tf.shape[0])
    n_cells = int(terrain.size)
    tf_idx = np.asarray(dual.ext.wet_idx, dtype=np.int64)
    wet_idx = np.asarray(dual.wse.wet_idx, dtype=np.int64)
    af = np.asarray(dual.af_idx, dtype=np.int64)
    thr = float(dual.extent_binary_threshold)
    chunk = max(1, int(time_chunk))
    n_wet = int(wet_idx.size)
    wet_z = terrain[wet_idx]
    wet_inv = np.full(n_cells, -1, dtype=np.int64)
    wet_inv[wet_idx] = np.arange(n_wet, dtype=np.int64)
    cols = wet_inv[tf_idx]
    mask = cols >= 0
    cols_af = wet_inv[af] if af.size else np.array([], dtype=np.int64)
    mask_af = cols_af >= 0 if af.size else np.array([], dtype=bool)

    sse = 0.0
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        ext_wet = np.zeros((e - s, n_wet), dtype=np.float64)
        if np.any(mask):
            ext_wet[:, cols[mask]] = ext_tf[s:e, mask]
        if af.size and np.any(mask_af):
            ext_wet[:, cols_af[mask_af]] = 1.0
        recon = np.where(
            wse_wet[s:e] > wet_z + dry_threshold_m, wse_wet[s:e], wet_z
        )
        wse_gated = np.where(ext_wet >= thr, recon, wet_z)
        depth = wse_gated - wet_z
        pred = np.where(depth < dry_threshold_m, 0.0, depth)
        pred = _clip(pred, dry_threshold_m)
        diff = pred - truth[s:e]
        sse += float(np.sum(diff * diff, dtype=np.float64))
    if truth.size == 0:
        return float("nan")
    return float(np.sqrt(sse / float(truth.size)))


def dual_oracle_error_budget(
    dual: Any,
    hf_ext: np.ndarray,
    lf_ext: np.ndarray,
    hf_wse: np.ndarray,
    lf_wse: np.ndarray,
    hf_depth_full: np.ndarray,
    terrain: np.ndarray,
    *,
    split: str = "test",
    dry_threshold_m: float | None = None,
) -> dict[str, Any]:
    """Matched EXT+WSE O1–O4 scored as gated depth RMSE on ``dual.wet_idx``."""
    dry = (
        float(dry_threshold_m)
        if dry_threshold_m is not None
        else float(dual.depth_threshold_m)
    )
    terrain = np.asarray(terrain, dtype=np.float64).reshape(-1)
    wet_idx = np.asarray(dual.wet_idx, dtype=np.int64)

    ext_stages = _branch_oracle_stages(dual.ext, hf_ext, lf_ext)
    wse_stages = _branch_oracle_stages(dual.wse, hf_wse, lf_wse)
    k_ext = int(ext_stages.pop("n_modes"))
    k_wse = int(wse_stages.pop("n_modes"))

    truth = _clip(np.asarray(hf_depth_full, dtype=np.float64)[:, wet_idx], dry)
    o_rmse: dict[str, float | None] = {}
    n_samples = int(truth.shape[0])
    n_cells = int(truth.shape[1])
    for name in ("o1", "o2", "o3", "o4"):
        ext_f = ext_stages.pop(name, None)
        wse_f = wse_stages.pop(name, None)
        if ext_f is None or wse_f is None:
            o_rmse[name] = None
            continue
        o_rmse[name] = _dual_stage_wet_depth_rmse(
            ext_f, wse_f, dual, terrain, dry, truth
        )
        del ext_f, wse_f

    n_modes_full = int(dual.wse.eof_modes_full.shape[0]) if (
        getattr(dual.wse, "eof_modes_full", None) is not None
        and np.asarray(dual.wse.eof_modes_full).size
    ) else int(dual.wse.n_modes)
    o1 = o_rmse["o1"]
    o2 = o_rmse["o2"]
    return {
        "split": split,
        "n_samples": n_samples,
        "n_cells": n_cells,
        "n_modes": int(k_wse),
        "n_modes_full": n_modes_full,
        "in_sample_full_rank": bool(k_wse >= n_samples and split == "train"),
        "o1_rmse": o1,
        "o2_rmse": o2,
        "o3_rmse": o_rmse["o3"],
        "o4_rmse": o_rmse["o4"],
        "o2_minus_o1": None if o1 is None or o2 is None else float(o2 - o1),
        "notes": DUAL_BUDGET_NOTE,
        "n_modes_ext": k_ext,
        "n_modes_wse": k_wse,
    }


def interpolate_wet_pair(

    hf_mat: np.ndarray,

    lf_mat: np.ndarray,

    terrain_hf: np.ndarray,

    shape_hf: tuple[int, int],

    shape_lf: tuple[int, int],

    wet_idx: np.ndarray,

    xy_hf: np.ndarray | None = None,

    xy_lf: np.ndarray | None = None,

    threshold_m: float = 0.03,

    terrain_lf: np.ndarray | None = None,

) -> tuple[np.ndarray, np.ndarray]:

    lf_interp = spatial.interpolate_lf_to_hf(

        lf_mat,

        shape_lf,

        shape_hf,

        terrain_hf,

        xy_hf=xy_hf,

        xy_lf=xy_lf,

        dry_threshold_m=threshold_m,

        terrain_lf=terrain_lf,

    )

    return hf_mat[:, wet_idx], lf_interp[:, wet_idx]





def _dual_branch_fields(

    dual: Any,

    hf_mat: np.ndarray,

    lf_mat: np.ndarray,

    terrain_hf: np.ndarray,

    shape_hf: tuple[int, int],

    shape_lf: tuple[int, int],

    xy_hf: np.ndarray | None,

    xy_lf: np.ndarray | None,

    terrain_lf: np.ndarray | None,

    dry_threshold_m: float,

) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:

    """Build EXT/WSE branch matrices using *trained* dual masks (not re-fit)."""

    from lsg.wse_ext import depth_to_extent, depth_to_wse



    terrain = np.asarray(terrain_hf, dtype=np.float64).reshape(-1)

    lf_depth_hf = spatial.interpolate_lf_to_hf(

        lf_mat,

        shape_lf,

        shape_hf,

        terrain,

        xy_hf=xy_hf,

        xy_lf=xy_lf,

        dry_threshold_m=dry_threshold_m,

        terrain_lf=terrain_lf,

    )

    tf_idx = np.asarray(dual.ext.wet_idx, dtype=np.int64)

    wet_idx = np.asarray(dual.wse.wet_idx, dtype=np.int64)

    hf_ext = depth_to_extent(hf_mat, dry_threshold_m)[:, tf_idx]

    lf_ext = depth_to_extent(lf_depth_hf, dry_threshold_m)[:, tf_idx]

    hf_wse = depth_to_wse(hf_mat, terrain)[:, wet_idx]

    lf_wse = depth_to_wse(lf_depth_hf, terrain)[:, wet_idx]

    return hf_ext, lf_ext, hf_wse, lf_wse, np.asarray(hf_mat, dtype=np.float64)





def error_budget_from_state(

    state: Any,

    hf_cube: np.ndarray,

    lf_cube: np.ndarray,

    terrain_hf: np.ndarray,

    shape_hf: tuple[int, int],

    shape_lf: tuple[int, int],

    time_series: bool,

    split: str = "test",

    xy_hf: np.ndarray | None = None,

    xy_lf: np.ndarray | None = None,

    terrain_lf: np.ndarray | None = None,

) -> dict[str, Any]:

    """O1–O4 using a fitted ``LSGState`` / ``DualLSGState`` and an event cube split."""

    from lsg.wse_ext import DualLSGState



    hf_mat = _event_matrix(hf_cube, time_series)

    lf_mat = _event_matrix(lf_cube, time_series)

    real = spatial.unpadded_rows(hf_mat)

    if not real.all():

        hf_mat, lf_mat = hf_mat[real], lf_mat[real]



    if isinstance(state, DualLSGState):

        dry = float(state.depth_threshold_m)

        xy_h = xy_hf if xy_hf is not None else state.wse.xy_hf

        xy_l = xy_lf if xy_lf is not None else state.wse.xy_lf

        z_lf = (

            terrain_lf

            if terrain_lf is not None

            else state.wse.terrain_lf

        )

        hf_ext, lf_ext, hf_wse, lf_wse, hf_full = _dual_branch_fields(

            state,

            hf_mat,

            lf_mat,

            terrain_hf,

            shape_hf,

            shape_lf,

            xy_h,

            xy_l,

            z_lf,

            dry,

        )

        return dual_oracle_error_budget(

            state,

            hf_ext,

            lf_ext,

            hf_wse,

            lf_wse,

            hf_full,

            terrain_hf,

            split=split,

            dry_threshold_m=dry,

        )



    thresh = float(getattr(state, "depth_threshold_m", 0.03) or 0.03)

    xy_h = xy_hf if xy_hf is not None else getattr(state, "xy_hf", None)

    xy_l = xy_lf if xy_lf is not None else getattr(state, "xy_lf", None)

    z_lf = (

        terrain_lf

        if terrain_lf is not None

        else getattr(state, "terrain_lf", None)

    )

    hf_wet, lf_wet = interpolate_wet_pair(

        hf_mat,

        lf_mat,

        terrain_hf,

        shape_hf,

        shape_lf,

        state.wet_idx,

        xy_hf=xy_h,

        xy_lf=xy_l,

        threshold_m=thresh,

        terrain_lf=z_lf,

    )

    full = getattr(state, "eof_modes_full", None)

    if full is None or np.asarray(full).size == 0:

        full = state.eof_modes

    return oracle_error_budget(

        hf_wet,

        lf_wet,

        eof_modes_full=full,

        n_modes=int(state.n_modes),

        hf_mean=state.hf_mean,

        weights=state.weights,

        gp_modes=list(state.gp_modes) if state.gp_modes else None,

        threshold_m=thresh,

        split=split,

        hier=zoning.hier_from_state(state),

    )





def budget_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:

    """Stable column order for JSON / printing."""

    keys = (

        "split",

        "n_samples",

        "n_modes",

        "n_modes_full",

        "o1_rmse",

        "o2_rmse",

        "o3_rmse",

        "o4_rmse",

        "o2_minus_o1",

        "in_sample_full_rank",

    )

    return [{k: row.get(k) for k in keys} | {"notes": row.get("notes", WANG2026_NOTE)} for row in rows]





def hf_budget_curve(

    hf: np.ndarray,

    lf: np.ndarray,

    terrain_hf: np.ndarray,

    shape_hf: tuple[int, int],

    shape_lf: tuple[int, int],

    cfg: dict[str, Any],

    train_idx: np.ndarray,

    test_idx: np.ndarray,

    budgets: list[int],

    xy_hf: np.ndarray | None = None,

    xy_lf: np.ndarray | None = None,

    area_hf: np.ndarray | None = None,

    terrain_lf: np.ndarray | None = None,

) -> list[dict[str, Any]]:

    """Retrain LSG-Max on nested prefixes of ``train_idx`` (fixed HF budget)."""

    train_idx = np.asarray(train_idx, dtype=int).reshape(-1)

    rows: list[dict[str, Any]] = []

    mesh = {

        "xy_hf": xy_hf,

        "xy_lf": xy_lf,

        "area_hf": area_hf,

        "terrain_lf": terrain_lf,

    }

    for n in budgets:

        n_use = max(1, min(int(n), train_idx.size))

        sub = train_idx[:n_use]

        model = LSGMaxModel(cfg)

        model.fit(

            hf[sub],

            lf[sub],

            terrain_hf,

            shape_hf,

            shape_lf,

            **{k: v for k, v in mesh.items() if v is not None},

        )

        pred = model.predict(

            lf[test_idx],

            terrain_hf,

            shape_hf,

            shape_lf,

            xy_hf=xy_hf,

            xy_lf=xy_lf,

            terrain_lf=terrain_lf,

        )

        metrics = model.evaluate(pred, hf[test_idx])

        rows.append(

            {

                "n_hf": n_use,

                "csi": metrics.get("csi"),

                "pod": metrics.get("pod"),

                "rmse": metrics.get("rmse"),

            }

        )

    return rows


