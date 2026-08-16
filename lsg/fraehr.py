"""Ingest already-computed Fraehr LSG case dumps (Carlisle / Chowilla / Burnett).

These Figshare packages contain hydrodynamic *results*, not tutorials that
still need to be run. Layout (Fraehr 2024, 10.26188/24312658):

    Geometry_data/     HF/LF mesh NPZ (XY_coor, Z_coor, Area)
    HD_model_data/     paired HF and LF simulations (HDF / NPZ / NPY)

This module never invents inundation fields.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from lsg.hecras import (
    active_cell_mask,
    hdf_has_results,
    list_2d_flow_areas,
    read_cell_centers,
    read_unsteady_2d,
)

_PLAN_RE = re.compile(r"\.p(\d+)\.(hdf|npz|npy)$", re.IGNORECASE)
_DEPTH_KEYS = ("depth", "WD", "wd", "water_depth", "WaterDepth")
_WSE_KEYS = (
    "wse",
    "WSE",
    "wse_data",
    "wl_data",  # Burnett TUFLOW
    "ws",
    "Water Surface",
    "water_surface",
)
_XY_KEYS = ("XY_coor", "xy", "coordinates")
_Z_KEYS = ("Z_coor", "z", "elevation", "terrain")
_AREA_KEYS = ("Area", "area", "cell_area")
# Fraehr Burnett TUFLOW dumps pad ~48 leading timesteps before the HF series
# used for EOF/GP (see BurnettRV/EOF_analysis_HFdata_preprocessing.py).
_TUFLOW_WL_WARMUP_STEPS = 48


def wse_to_depth(
    wse: np.ndarray,
    elevation: np.ndarray,
    threshold_m: float = 0.03,
    drop_ghost: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """WSE minus cell elevation; values below threshold become 0.

    Returns depth, kept-cell mask, elevation on kept cells.
    """
    wse = np.asarray(wse, dtype=np.float64)
    elev = np.asarray(elevation, dtype=np.float64).reshape(-1)
    if wse.ndim == 1:
        wse = wse[np.newaxis, :]
    if wse.shape[1] != elev.size:
        raise ValueError(
            f"WSE cells {wse.shape[1]} != elevation cells {elev.size}"
        )
    keep = np.ones(elev.size, dtype=bool)
    if drop_ghost:
        keep &= np.isfinite(elev)
    depth = wse[:, keep] - elev[keep]
    depth = np.where(depth >= threshold_m, depth, 0.0)
    return depth, keep, elev[keep]


def _first_key(store: Any, names: Iterable[str]) -> str | None:
    keys = set(store)
    for name in names:
        if name in keys:
            return name
    lower = {str(k).lower(): k for k in keys}
    for name in names:
        hit = lower.get(str(name).lower())
        if hit is not None:
            return str(hit)
    return None


def load_geometry_npz(path: Path) -> dict[str, np.ndarray]:
    raw = np.load(path, allow_pickle=True)
    xy_key = _first_key(raw, _XY_KEYS)
    z_key = _first_key(raw, _Z_KEYS)
    if xy_key is None or z_key is None:
        raise KeyError(
            f"{path} needs XY_coor and Z_coor (got {raw.files})"
        )
    xy = np.asarray(raw[xy_key], dtype=np.float64)
    z = np.asarray(raw[z_key], dtype=np.float64).reshape(-1)
    area_key = _first_key(raw, _AREA_KEYS)
    area = (
        np.asarray(raw[area_key], dtype=np.float64).reshape(-1)
        if area_key
        else None
    )
    keep = np.isfinite(z) & np.isfinite(xy).all(axis=1)
    return {
        "xy": xy[keep],
        "elevation": z[keep],
        "area": None if area is None else area[keep],
        "keep": keep,
        "source": str(path),
    }


def _walk_named_dir(root: Path, names: tuple[str, ...], max_depth: int = 4) -> Path | None:
    root = Path(root)
    if not root.exists():
        return None
    wanted = {n.lower() for n in names}
    if root.is_dir() and root.name.lower() in wanted:
        return root
    for path in root.rglob("*"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if len(rel.parts) > max_depth:
            continue
        if path.is_dir() and path.name.lower() in wanted:
            return path
    return None


def discover_layout(case_root: Path) -> dict[str, Path | None]:
    """Locate Geometry_data and HD_model_data under a Figshare unzip."""
    case_root = Path(case_root)
    geom = _walk_named_dir(case_root, ("geometry_data",))
    hd = _walk_named_dir(case_root, ("hd_model_data", "hd_modeldata"))
    splits = _walk_named_dir(case_root, ("train_test_split_data",))
    return {
        "case_root": case_root,
        "geometry_data": geom,
        "hd_model_data": hd,
        "train_test_split_data": splits,
    }


def _pick_geom_file(geometry_dir: Path, which: str) -> Path | None:
    files = sorted(geometry_dir.glob("*.npz"))
    if not files:
        return None
    token = which.lower()
    ranked = []
    for path in files:
        name = path.name.lower()
        score = 0
        if "extrap" in name:
            score -= 10
        if token in name:
            score += 2
        if which.lower() == "hf" and "high" in name:
            score += 2
        if which.lower() == "hf" and "lisflood" in name:
            score += 3
        if which.lower() == "hf" and "tuflow" in name:
            score += 5
        if which.lower() == "hf" and name.startswith("lf"):
            score -= 4
        if which.lower() == "hf" and ("hec" in name or "hecras" in name):
            score -= 4
        if which.lower() == "lf" and "low" in name:
            score += 2
        if which.lower() == "lf" and name.startswith("lf"):
            score += 3
        if which.lower() == "lf" and ("hec" in name or "hecras" in name):
            score += 5
        if which.lower() == "lf" and "lisflood" in name:
            score -= 4
        if which.lower() == "lf" and "tuflow" in name:
            score -= 4
        ranked.append((score, path))
    ranked.sort(key=lambda item: (-item[0], item[1].name))
    return ranked[0][1] if ranked[0][0] > 0 else (files[0] if len(files) == 1 else None)


def _fidelity_of(path: Path) -> str | None:
    blob = f"{path.parent.name}/{path.name}".lower()
    if any(
        tok in blob
        for tok in ("/lf", "\\lf", "_lf.", "_lf/", "lowfid", "low-fid", "low_fid", "coarse")
    ):
        return "lf"
    if any(
        tok in blob
        for tok in ("/hf", "\\hf", "_hf.", "_hf/", "highfid", "high-fid", "high_fid", "fine")
    ):
        return "hf"
    parent = path.parent.name.lower()
    if parent in {"hf", "lf"}:
        return parent
    return None


def _event_id_from_name(name: str) -> str | None:
    match = _PLAN_RE.search(name)
    if match:
        return f"E{int(match.group(1))}"
    stem = Path(name).stem
    digits = re.search(r"(\d+)", stem)
    if digits:
        return f"E{int(digits.group(1))}"
    return stem.upper()


def event_sort_key(event_id: str) -> tuple[int, str]:
    """Natural order: E2 before E10 (lexicographic sort puts E10 first)."""
    match = re.fullmatch(r"E(\d+)", str(event_id).strip(), flags=re.IGNORECASE)
    if match:
        return (int(match.group(1)), str(event_id).upper())
    return (10**9, str(event_id).upper())


def _event_sort_key(event_id: str) -> tuple[int, str]:
    """Backward-compatible alias."""
    return event_sort_key(event_id)

def _find_event_summary_csv(case_root: Path) -> Path | None:
    """Prefer the main CV catalogue over ``*_Extrap_event_summary.csv``."""
    case_root = Path(case_root)
    if not case_root.is_dir():
        return None
    candidates = sorted(case_root.glob("*event_summary*.csv"))
    main = [
        p
        for p in candidates
        if "extrap" not in p.name.lower() and p.is_file()
    ]
    if main:
        return main[0]
    return candidates[0] if candidates else None


def _pair_from_burnett_summary(
    case_root: Path, hd_dir: Path
) -> dict[str, dict[str, Path]] | None:
    """Pair Burnett TUFLOW HF NPZs with HEC-RAS LF plans via event summary CSV.

    HF files are ``Paradise_{tuflow_evt_name_old}_002.npz`` (no ``.p##`` stem);
    LF files are ``*.{HEC_RAS_plan}.hdf``. Event ids follow the LF plan number
    (``p12`` → ``E12``), matching Fraehr's HEC-RAS naming.
    """
    import csv

    summary = _find_event_summary_csv(case_root)
    if summary is None:
        return None
    with summary.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    cols = {c.strip() for c in rows[0]}
    if "tuflow_evt_name_old" not in cols or "HEC_RAS_plan" not in cols:
        return None

    hf_dir = _walk_named_dir(hd_dir, ("high-fidelity", "high_fidelity", "hf"))
    lf_dir = _walk_named_dir(hd_dir, ("low-fidelity", "low_fidelity", "lf"))
    if hf_dir is None or lf_dir is None:
        return None

    paired: dict[str, dict[str, Path]] = {}
    for row in rows:
        plan = str(row.get("HEC_RAS_plan") or "").strip()
        evt = str(row.get("tuflow_evt_name_old") or "").strip()
        if not plan or not evt:
            continue
        plan_match = re.fullmatch(r"p(\d+)", plan, flags=re.IGNORECASE)
        if plan_match is None:
            continue
        eid = f"E{int(plan_match.group(1))}"
        hf_candidates = [
            hf_dir / f"Paradise_{evt}_002.npz",
            hf_dir / f"{evt}_002.npz",
            hf_dir / f"Paradise_{evt}.npz",
        ]
        hf_path = next((p for p in hf_candidates if p.is_file()), None)
        if hf_path is None:
            hits = sorted(hf_dir.glob(f"*{evt}*.npz"))
            hf_path = hits[0] if len(hits) == 1 else None
        lf_hits = (
            sorted(lf_dir.glob(f"*.{plan}.hdf"))
            + sorted(lf_dir.glob(f"*.{plan}.HDF"))
            + sorted(lf_dir.glob(f"*.{plan}.npz"))
            + sorted(lf_dir.glob(f"*.{plan}.NPZ"))
        )
        lf_path = lf_hits[0] if lf_hits else None
        if hf_path is None or lf_path is None:
            continue
        paired[eid] = {"hf": hf_path, "lf": lf_path}
    return paired or None


def _list_result_files(
    hd_dir: Path, case_root: Path | None = None
) -> dict[str, dict[str, Path]]:
    """event_id -> {hf: path, lf: path}."""
    hd_dir = Path(hd_dir)
    if case_root is not None:
        burnett = _pair_from_burnett_summary(Path(case_root), hd_dir)
        if burnett:
            return burnett

    paired: dict[str, dict[str, Path]] = {}
    files = [
        p
        for p in hd_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".hdf", ".npz", ".npy", ".nc"}
    ]
    for path in files:
        fid = _fidelity_of(path)
        # Prefer HEC-RAS plan ids (.p01.hdf). Skip other numbered dumps that
        # would invent unpaired extrap ids (Chowilla p38 HF vs p41 LF).
        if path.suffix.lower() == ".hdf" and _PLAN_RE.search(path.name) is None:
            continue
        eid = _event_id_from_name(path.name)
        if fid is None or eid is None:
            continue
        paired.setdefault(eid, {})[fid] = path
    return paired


def _hdf_max_wse(
    path: Path,
    elevation: np.ndarray | None,
    threshold_m: float,
) -> np.ndarray:
    """Per-cell max depth from Summary Maximum Water Surface or TS nanmax."""
    h5py = __import__("h5py")
    summary_root = (
        "Results/Unsteady/Output/Output Blocks/Base Output/Summary Output/"
        "2D Flow Areas"
    )
    with h5py.File(path, "r") as f:
        if summary_root in f:
            parent = f[summary_root]
            areas = [k for k in parent.keys() if hasattr(parent[k], "keys")]
            if not areas:
                areas = list_2d_flow_areas(path)
            area_name = areas[0] if areas else None
            grp = parent[area_name] if area_name and area_name in parent else None
            if grp is not None and "Maximum Water Surface" in grp:
                raw = np.asarray(grp["Maximum Water Surface"][()], dtype=np.float64)
                # HEC-RAS stores (2, n_cells): row 0 = max WSE, row 1 = time index.
                wse = raw[0] if raw.ndim == 2 and raw.shape[0] >= 1 else raw.reshape(-1)
                active = active_cell_mask(path, area_name)
                if active is not None and active.size == wse.size:
                    wse = wse[active]
                if elevation is None:
                    geom = read_cell_centers(path, area_name)
                    elevation = np.asarray(geom["elevation"]).reshape(-1)
                    if geom["active"] is not None:
                        elevation = elevation[geom["active"]]
                depth, _, _ = wse_to_depth(
                    wse[np.newaxis, :], elevation, threshold_m
                )
                return depth

    # Fallback: full unsteady series then nanmax (memory-heavy).
    depth = _load_result_depth(path, elevation, threshold_m, time_reduction=None)
    return np.nanmax(depth, axis=0, keepdims=True)


def _load_result_depth(
    path: Path,
    elevation: np.ndarray | None,
    threshold_m: float,
    time_reduction: str | None = None,
) -> np.ndarray:
    """Load depth cube ``(T, C)``. ``time_reduction='max'`` → ``(1, C)``."""
    reduce = (time_reduction or "").strip().lower() or None
    suffix = path.suffix.lower()
    if suffix == ".hdf":
        if not hdf_has_results(path):
            raise KeyError(f"{path} has no 2D results")
        if reduce == "max":
            return _hdf_max_wse(path, elevation, threshold_m)
        try:
            raw = read_unsteady_2d(path, variable="depth", drop_ghost_cells=True)
        except KeyError:
            raw = read_unsteady_2d(path, variable="wse", drop_ghost_cells=True)
        values = np.asarray(raw["values"], dtype=np.float64)
        if raw["variable"] == "depth":
            return np.where(values >= threshold_m, values, 0.0)
        if elevation is None:
            geom = read_cell_centers(path, raw["area"])
            elevation = np.asarray(geom["elevation"]).reshape(-1)
            active = geom["active"]
            if active is not None:
                elevation = elevation[active]
        depth, _, _ = wse_to_depth(values, elevation, threshold_m)
        return depth

    if suffix == ".npy":
        arr = np.load(path)
        depth = _as_depth(arr, elevation, threshold_m)
    elif suffix == ".npz":
        raw = np.load(path, allow_pickle=True)
        dkey = _first_key(raw, _DEPTH_KEYS)
        wkey = _first_key(raw, _WSE_KEYS)
        if dkey:
            depth = _as_depth(raw[dkey], elevation, threshold_m)
        elif wkey:
            if elevation is None:
                raise KeyError(f"{path} has WSE but no elevation was provided")
            wse = np.asarray(raw[wkey], dtype=np.float64)
            # Burnett TUFLOW: drop leading pad before Fraehr's analysis window.
            if str(wkey).lower() == "wl_data" and wse.ndim >= 2:
                n_t = int(wse.shape[0])
                if n_t > _TUFLOW_WL_WARMUP_STEPS:
                    wse = wse[_TUFLOW_WL_WARMUP_STEPS :]
            depth, _, _ = wse_to_depth(wse, elevation, threshold_m)
        else:
            raise KeyError(f"{path} has neither depth nor WSE (keys={raw.files})")
    else:
        raise ValueError(f"Unsupported result type: {path}")

    if reduce == "max":
        return np.nanmax(depth, axis=0, keepdims=True)
    return depth

def _as_depth(
    arr: np.ndarray,
    elevation: np.ndarray | None,
    threshold_m: float,
) -> np.ndarray:
    data = np.asarray(arr, dtype=np.float64)
    if data.ndim == 1:
        data = data[np.newaxis, :]
    if data.ndim == 3:
        data = data.reshape(data.shape[0], -1)
    if elevation is not None and data.shape[1] == elevation.size:
        # Heuristic: values look like WSE if they sit near terrain.
        sample = data[0]
        wet = sample > (elevation + threshold_m)
        if wet.any() and np.median(sample[wet] - elevation[wet]) > 5.0:
            depth, _, _ = wse_to_depth(data, elevation, threshold_m)
            return depth
        data = np.where(data >= threshold_m, data, 0.0)
    return data


def align_lf_to_hf_time(lf_depth: np.ndarray, n_hf_steps: int) -> np.ndarray:
    """Trim leading LF warm-up steps so LF and HF share one time axis.

    In the Fraehr dumps the LF plan starts a couple of hours before the HF
    output does, so an event has a few more LF than HF timesteps. The published
    pipeline keeps the trailing ``n_hf_steps`` LF rows.
    """
    n_lf = int(lf_depth.shape[0])
    if n_lf <= n_hf_steps:
        return lf_depth
    return lf_depth[n_lf - n_hf_steps :]


def ingest_fraehr_case(
    case_root: Path,
    threshold_m: float = 0.03,
    event_ids: Iterable[str] | None = None,
    time_reduction: str | None = None,
) -> dict[str, Any]:
    """Load paired HF/LF depth cubes from a Fraehr unzip directory.

    ``time_reduction='max'`` keeps one max-depth row per event (needed for
    Chowilla-scale HDF time series that do not fit in RAM as full cubes).
    """
    case_root = Path(case_root)
    layout = discover_layout(case_root)
    geom_dir = layout["geometry_data"]
    hd_dir = layout["hd_model_data"]
    if geom_dir is None or hd_dir is None:
        raise FileNotFoundError(
            f"No Geometry_data / HD_model_data under {case_root}. "
            "Download Carlisle.zip from 10.26188/24312658 and unzip here."
        )

    hf_geom_path = _pick_geom_file(geom_dir, "hf")
    lf_geom_path = _pick_geom_file(geom_dir, "lf")
    if hf_geom_path is None or lf_geom_path is None:
        raise FileNotFoundError(f"Missing HF/LF geometry NPZ in {geom_dir}")
    hf_geom = load_geometry_npz(hf_geom_path)
    lf_geom = load_geometry_npz(lf_geom_path)

    paired = _list_result_files(hd_dir, case_root=case_root)
    ids = sorted(
        (eid for eid, files in paired.items() if "hf" in files and "lf" in files),
        key=event_sort_key,
    )
    if event_ids is not None:
        wanted = [str(e) for e in event_ids]
        ids = [e for e in wanted if e in paired and "hf" in paired[e] and "lf" in paired[e]]
    if not ids:
        raise FileNotFoundError(
            f"No paired HF/LF result files under {hd_dir}"
        )

    reduce = (time_reduction or "").strip().lower() or None
    hf_list, lf_list = [], []
    for eid in ids:
        hf = _load_result_depth(
            paired[eid]["hf"],
            hf_geom["elevation"],
            threshold_m,
            time_reduction=reduce,
        )
        lf = _load_result_depth(
            paired[eid]["lf"],
            lf_geom["elevation"],
            threshold_m,
            time_reduction=reduce,
        )
        if reduce != "max":
            lf = align_lf_to_hf_time(lf, hf.shape[0])
        hf_list.append(hf)
        lf_list.append(lf)

    from lsg.data import _stack_or_pad

    hf_depth = _stack_or_pad(hf_list)
    lf_depth = _stack_or_pad(lf_list)
    n_hf = hf_geom["xy"].shape[0]
    n_lf = lf_geom["xy"].shape[0]
    return {
        "hf_depth": hf_depth,
        "lf_depth": lf_depth,
        "terrain_hf": hf_geom["elevation"],
        "terrain_lf": lf_geom["elevation"],
        "shape_hf": (n_hf, 1),
        "shape_lf": (n_lf, 1),
        "xy_hf": hf_geom["xy"],
        "xy_lf": lf_geom["xy"],
        "area_hf": hf_geom["area"],
        "event_ids": ids,
        "meta": {
            "source": "fraehr",
            "case_root": str(case_root),
            "hf_geom": hf_geom["source"],
            "lf_geom": lf_geom["source"],
            "n_events": len(ids),
            "time_reduction": reduce,
        },
    }


def detect_fraehr_data(cfg: dict[str, Any]) -> dict[str, Any]:
    from lsg.config import resolve_path

    root = Path(cfg["_project_root"])
    case_root = (
        resolve_path(cfg, "case_root")
        if "case_root" in cfg.get("paths", {})
        else root / "data" / "external" / "carlisle"
    )
    layout = discover_layout(case_root)
    paired_ids: list[str] = []
    if layout["hd_model_data"] is not None:
        files = _list_result_files(layout["hd_model_data"], case_root=case_root)
        paired_ids = sorted(
            (eid for eid, item in files.items() if "hf" in item and "lf" in item),
            key=event_sort_key,
        )
    geom_ok = layout["geometry_data"] is not None
    return {
        "available": bool(paired_ids) and geom_ok,
        "kind": "fraehr",
        "case_root": case_root,
        "hf_dir": layout["hd_model_data"],
        "lf_dir": layout["hd_model_data"],
        "paired_event_ids": paired_ids,
        "lf_resolution_dirs": {},
        "dem_exists": geom_ok,
        "dem_path": layout["geometry_data"],
        "layout": layout,
    }
