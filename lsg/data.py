"""Data ingestion, paper event splits, and synthetic Brisbane-style generator."""

from __future__ import annotations

import csv
import json
import re
import warnings
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml

# Wang et al. (2026) Appendix A / Section 3.3. IDs are unpadded (FE1, FE21).
PAPER_VALIDATION_IDS = ("FE21", "FE26", "FE50", "FE51")  # VE1–VE4
PAPER_LSG_TS_TRAIN_IDS = (
    "FE20",
    "FE22",
    "FE27",
    "FE30",
    "FE32",
    "FE34",
    "FE48",
    "FE49",
)
PAPER_LSG_TS_SYNTHETIC_TRAIN_IDS = (
    "FE20",
    "FE22",
    "FE27",
    "FE30",
    "FE32",
    "FE34",
)
PAPER_HISTORICAL_TRAIN_IDS = ("FE48", "FE49")  # 1999, 2011
PAPER_HISTORICAL_VAL_IDS = ("FE50", "FE51")  # 1996, 2013
PAPER_VE_MAP = {"FE21": "VE1", "FE26": "VE2", "FE50": "VE3", "FE51": "VE4"}

_EVENT_RE = re.compile(r"^(FE|VE)0*([0-9]+)$", re.IGNORECASE)
_DEPTH_GLOBS = ("*.npz", "*.nc")


def save_event_bundle(
    path: Path,
    hf_depth: np.ndarray,
    lf_depth: np.ndarray,
    terrain_hf: np.ndarray,
    shape_hf: tuple[int, int],
    shape_lf: tuple[int, int],
    event_ids: list[str],
    meta: dict[str, Any] | None = None,
    terrain_lf: np.ndarray | None = None,
) -> None:
    """
    Save training/prediction arrays.

    hf_depth / lf_depth: (n_events, n_timesteps, n_cells) or (n_timesteps_total, n_cells)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "hf_depth": hf_depth,
        "lf_depth": lf_depth,
        "terrain_hf": terrain_hf,
        "shape_hf": np.array(shape_hf),
        "shape_lf": np.array(shape_lf),
        "event_ids": np.array(event_ids),
        "meta": json.dumps(meta or {}),
    }
    if terrain_lf is not None:
        payload["terrain_lf"] = np.asarray(terrain_lf, dtype=np.float64)
    np.savez_compressed(path, **payload)


def load_event_bundle(path: Path) -> dict[str, Any]:
    path = Path(path)
    raw = np.load(path, allow_pickle=True)
    meta = json.loads(str(raw["meta"]))
    out = {
        "hf_depth": raw["hf_depth"],
        "lf_depth": raw["lf_depth"],
        "terrain_hf": raw["terrain_hf"],
        "shape_hf": tuple(raw["shape_hf"].tolist()),
        "shape_lf": tuple(raw["shape_lf"].tolist()),
        "event_ids": list(raw["event_ids"]),
        "meta": meta,
    }
    if "terrain_lf" in raw.files:
        out["terrain_lf"] = raw["terrain_lf"]
    return out


def stack_events(events: list[np.ndarray]) -> np.ndarray:
    """Concatenate events along time axis: list of (T, C) -> (sum_T, C)."""
    return np.vstack(events)


def default_synthetic_event_ids(n_events: int) -> list[str]:
    """Paper FE IDs so the same splits.yaml applies to the synthetic demo."""
    ordered: list[str] = []
    for group in (
        PAPER_VALIDATION_IDS,
        PAPER_LSG_TS_SYNTHETIC_TRAIN_IDS,
        [f"FE{i}" for i in range(1, 52)],
    ):
        for eid in group:
            if eid not in ordered:
                ordered.append(eid)
    if n_events <= len(ordered):
        return ordered[:n_events]
    extra = [f"synthetic_event_{i:02d}" for i in range(n_events - len(ordered))]
    return ordered + extra


def coarsen_event_cube(
    hf_depth: np.ndarray,
    shape_hf: tuple[int, int],
    factor: int,
) -> tuple[np.ndarray, tuple[int, int]]:
    """Block-average a (n_events, n_t, n_hf_cells) cube onto a coarser LF grid."""
    from lsg.spatial import coarsen_grid

    ny, nx = shape_hf
    ny_lf, nx_lf = ny // factor, nx // factor
    if ny_lf < 1 or nx_lf < 1:
        raise ValueError(f"HF grid {shape_hf} is not divisible enough for factor={factor}")
    lf_events = [coarsen_grid(hf_depth[e], shape_hf, factor) for e in range(hf_depth.shape[0])]
    return np.stack(lf_events, axis=0), (ny_lf, nx_lf)


def generate_synthetic_floodplain(
    n_events: int = 12,
    n_timesteps: int = 48,
    shape_hf: tuple[int, int] = (30, 40),
    lf_factor: int = 4,
    seed: int = 42,
    event_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Synthetic HF/LF depth time series mimicking complex floodplain dynamics.

    LF is coarsened HF plus bias/noise; used for smoke tests when real TUFLOW
    or HEC-RAS outputs are unavailable.
    """
    rng = np.random.default_rng(seed)
    ny, nx = shape_hf
    ny_lf, nx_lf = ny // lf_factor, nx // lf_factor
    if ny_lf < 1 or nx_lf < 1:
        raise ValueError(
            f"HF grid {shape_hf} is not divisible by lf_factor={lf_factor}"
        )

    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    xx, yy = np.meshgrid(x, y)
    terrain = 10.0 + 5.0 * yy + 0.5 * np.sin(4 * np.pi * xx) * np.cos(2 * np.pi * yy)
    terrain = terrain.ravel()

    ids = list(event_ids) if event_ids is not None else default_synthetic_event_ids(n_events)
    if len(ids) != n_events:
        raise ValueError(f"event_ids length {len(ids)} != n_events {n_events}")

    hf_events = []
    lf_events = []

    from lsg.spatial import coarsen_grid

    for e in range(n_events):
        amplitude = 0.5 + 1.5 * rng.random()
        peak_t = int(n_timesteps * (0.3 + 0.4 * rng.random()))
        ts = np.arange(n_timesteps)
        hydro = amplitude * np.exp(-0.5 * ((ts - peak_t) / (0.15 * n_timesteps + 1)) ** 2)
        spatial = np.exp(-((xx - 0.3 - 0.1 * e / n_events) ** 2 + (yy - 0.5) ** 2) / 0.08)
        spatial = spatial.ravel()
        depth_hf = np.outer(hydro, spatial)
        depth_hf = np.clip(depth_hf - np.maximum(terrain - 12.0, 0) * 0.1, 0, None)
        hf_events.append(depth_hf.astype(np.float64))

        lf_flat = coarsen_grid(depth_hf, (ny, nx), lf_factor)
        lf_events.append(lf_flat.astype(np.float64))

    hf = np.stack(hf_events, axis=0)
    lf = np.stack(lf_events, axis=0)
    terrain_lf = coarsen_grid(terrain.reshape(1, -1), (ny, nx), lf_factor).reshape(-1)
    return {
        "hf_depth": hf,
        "lf_depth": lf,
        "terrain_hf": terrain,
        "terrain_lf": terrain_lf,
        "shape_hf": (ny, nx),
        "shape_lf": (ny_lf, nx_lf),
        "event_ids": ids,
        "meta": {
            "source": "synthetic",
            "lf_factor": lf_factor,
            "event_id_scheme": "paper_fe",
        },
    }


def normalize_event_id(value: str) -> str:
    """FE01 / fe21 / VE1 -> FE1 / FE21 / VE1."""
    text = str(value).strip()
    match = _EVENT_RE.fullmatch(text)
    if match:
        return f"{match.group(1).upper()}{int(match.group(2))}"
    return text


def _event_sort_key(event_id: str) -> tuple[str, int]:
    match = _EVENT_RE.fullmatch(str(event_id).strip())
    if match:
        return match.group(1).upper(), int(match.group(2))
    return str(event_id), 0


def list_depth_files(directory: Path) -> dict[str, Path]:
    """Map normalized event id -> depth file (NPZ preferred over NetCDF)."""
    directory = Path(directory)
    found: dict[str, Path] = {}
    if not directory.is_dir():
        return found
    for pattern in _DEPTH_GLOBS:
        for path in sorted(directory.glob(pattern)):
            key = normalize_event_id(path.stem)
            if key in found and found[key].suffix.lower() == ".npz":
                continue
            found[key] = path
    return found


def has_paired_event_data(hf_dir: Path, lf_dir: Path) -> bool:
    hf_map = list_depth_files(hf_dir)
    lf_map = list_depth_files(lf_dir)
    return bool(set(hf_map) & set(lf_map))


def detect_real_event_data(cfg: dict[str, Any]) -> dict[str, Any]:
    """
    Inspect configured raw directories for paired HF/LF event files.

    Returns a status dict; never raises for missing folders.
    """
    kind = str((cfg.get("ingest") or {}).get("kind") or "npz_dir").lower()
    if kind == "fraehr":
        from lsg.fraehr import detect_fraehr_data

        return detect_fraehr_data(cfg)

    from lsg.config import resolve_path, resolve_path_value

    root = Path(cfg["_project_root"])
    hf_dir = resolve_path(cfg, "hf_results")
    lf_dir = resolve_path(cfg, "lf_results")
    fallback_lf = root / "data" / "raw" / "lf"
    if not list_depth_files(lf_dir) and list_depth_files(fallback_lf):
        lf_dir = fallback_lf

    lf_resolution_dirs: dict[str, Path] = {}
    for label, rel in (cfg.get("paths", {}).get("lf_resolutions") or {}).items():
        lf_resolution_dirs[str(label)] = resolve_path_value(cfg, rel)

    paired = sorted(set(list_depth_files(hf_dir)) & set(list_depth_files(lf_dir)), key=_event_sort_key)
    dem = resolve_path(cfg, "dem") if "dem" in cfg.get("paths", {}) else root / "data" / "raw" / "dem.tif"
    return {
        "available": bool(paired),
        "kind": "npz_dir",
        "hf_dir": hf_dir,
        "lf_dir": lf_dir,
        "paired_event_ids": paired,
        "lf_resolution_dirs": {
            k: v for k, v in lf_resolution_dirs.items() if has_paired_event_data(hf_dir, v)
        },
        "dem_exists": Path(dem).is_file(),
        "dem_path": Path(dem),
    }


def _load_depth_file(path: Path) -> dict[str, Any]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".npz":
        raw = np.load(path)
        if "depth" not in raw:
            raise KeyError(f"{path} is missing required array 'depth'")
        depth = np.asarray(raw["depth"], dtype=np.float64)
        terrain = np.asarray(raw["terrain"], dtype=np.float64) if "terrain" in raw else None
        shape = tuple(np.asarray(raw["shape"]).tolist()) if "shape" in raw else None
        return {"depth": depth, "terrain": terrain, "shape": shape}

    if suffix == ".nc":
        try:
            import xarray as xr
        except ImportError as exc:
            raise ImportError(
                f"Reading {path} requires xarray (optional extra). "
                "Export NPZ instead, or pip install xarray netCDF4."
            ) from exc
        ds = xr.open_dataset(path)
        try:
            if "depth" not in ds:
                raise KeyError(f"{path} is missing variable 'depth'")
            depth = np.asarray(ds["depth"].values, dtype=np.float64)
            terrain = (
                np.asarray(ds["terrain"].values, dtype=np.float64)
                if "terrain" in ds
                else None
            )
            shape = None
            if "shape" in ds:
                shape = tuple(np.asarray(ds["shape"].values).tolist())
            elif depth.ndim == 3:
                shape = tuple(int(v) for v in depth.shape[1:])
        finally:
            ds.close()
        if depth.ndim == 3:
            depth = depth.reshape(depth.shape[0], -1)
            if terrain is not None and terrain.ndim == 2:
                terrain = terrain.ravel()
        return {"depth": depth, "terrain": terrain, "shape": shape}

    raise ValueError(f"Unsupported depth file type: {path}")


def _as_time_depth(depth: np.ndarray) -> np.ndarray:
    arr = np.asarray(depth, dtype=np.float64)
    if arr.ndim == 1:
        return arr[np.newaxis, :]
    if arr.ndim == 2:
        return arr
    if arr.ndim == 3:
        return arr.reshape(arr.shape[0], -1)
    raise ValueError(f"depth must be 1D, 2D or 3D, got shape {arr.shape}")


def _stack_or_pad(arrays: list[np.ndarray]) -> np.ndarray:
    lengths = {a.shape[0] for a in arrays}
    n_cells = {a.shape[1] for a in arrays}
    if len(n_cells) != 1:
        raise ValueError(f"Inconsistent cell counts in event files: {sorted(n_cells)}")
    if len(lengths) == 1:
        return np.stack(arrays, axis=0)
    t_max = max(lengths)
    n_c = next(iter(n_cells))
    warnings.warn(
        f"Event time lengths differ {sorted(lengths)}; padding with NaN to T={t_max}. "
        "LSG-Max uses nanmax; LSG-TS should use events with a common timestep count.",
        stacklevel=2,
    )
    out = np.full((len(arrays), t_max, n_c), np.nan, dtype=np.float64)
    for i, arr in enumerate(arrays):
        out[i, : arr.shape[0]] = arr
    return out


def ingest_lf_hf_npz_dir(
    hf_dir: Path,
    lf_dir: Path,
    pattern: str = "*.npz",
    event_ids: Iterable[str] | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    """
    Load paired HF/LF simulation exports.

    Expected per-file keys: depth (T, C) or (C,), optional terrain (C,), shape [ny, nx].
    Files are paired by normalized event id (filename stem), not by sort order alone.
    ``pattern`` is kept for compatibility; ``*.nc`` files are also discovered.
    """
    del pattern  # pairing is by stem across npz/nc
    hf_dir = Path(hf_dir)
    lf_dir = Path(lf_dir)
    hf_map = list_depth_files(hf_dir)
    lf_map = list_depth_files(lf_dir)
    common = set(hf_map) & set(lf_map)
    hf_only = sorted(set(hf_map) - set(lf_map), key=_event_sort_key)
    lf_only = sorted(set(lf_map) - set(hf_map), key=_event_sort_key)

    if event_ids is not None:
        wanted = [normalize_event_id(e) for e in event_ids]
        missing = [e for e in wanted if e not in common]
        ids = [e for e in wanted if e in common]
        if missing and strict:
            raise FileNotFoundError(
                f"Requested events missing paired HF/LF files: {missing}"
            )
        if missing:
            warnings.warn(f"Skipping unpaired requested events: {missing}", stacklevel=2)
    else:
        ids = sorted(common, key=_event_sort_key)
        if (hf_only or lf_only) and strict:
            raise ValueError(
                f"HF/LF event mismatch. HF-only={hf_only} LF-only={lf_only}"
            )
        if hf_only or lf_only:
            warnings.warn(
                f"Ignoring unpaired files. HF-only={hf_only} LF-only={lf_only}",
                stacklevel=2,
            )

    if not ids:
        raise FileNotFoundError(
            f"No paired HF/LF events in {hf_dir} and {lf_dir}"
        )

    hf_list, lf_list = [], []
    terrain = None
    shape_hf = None
    shape_lf = None
    for eid in ids:
        h = _load_depth_file(hf_map[eid])
        l = _load_depth_file(lf_map[eid])
        hf_list.append(_as_time_depth(h["depth"]))
        lf_list.append(_as_time_depth(l["depth"]))
        if terrain is None and h["terrain"] is not None:
            terrain = h["terrain"].ravel()
        if shape_hf is None and h["shape"] is not None:
            shape_hf = tuple(int(v) for v in h["shape"])
        if shape_lf is None and l["shape"] is not None:
            shape_lf = tuple(int(v) for v in l["shape"])

    hf_depth = _stack_or_pad(hf_list)
    lf_depth = _stack_or_pad(lf_list)
    if terrain is None:
        n_cells = hf_depth.shape[-1]
        terrain = np.zeros(n_cells, dtype=np.float64)
        warnings.warn(
            "No terrain array in HF files; using zeros. Provide terrain in NPZ or dem.tif.",
            stacklevel=2,
        )
    if shape_hf is None:
        warnings.warn("HF files have no 'shape'; downstream interpolation needs ny, nx.", stacklevel=2)
    if shape_lf is None:
        warnings.warn("LF files have no 'shape'; downstream interpolation needs ny, nx.", stacklevel=2)

    return {
        "hf_depth": hf_depth,
        "lf_depth": lf_depth,
        "terrain_hf": terrain,
        "shape_hf": shape_hf,
        "shape_lf": shape_lf,
        "event_ids": ids,
        "meta": {
            "source": str(hf_dir),
            "lf_dir": str(lf_dir),
            "n_events": len(ids),
        },
    }


def load_event_catalog(path: Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_split_ids(cfg: dict[str, Any]) -> dict[str, list[str]]:
    """Paper (or YAML) event-id lists for train/validation."""
    events_cfg = cfg.get("events") or {}
    splits_cfg = dict(events_cfg.get("splits") or {})
    catalog_rel = events_cfg.get("catalog")
    if catalog_rel:
        from lsg.config import resolve_path_value

        catalog_path = resolve_path_value(cfg, catalog_rel)
        splits_file = events_cfg.get("splits_file")
        split_path = (
            resolve_path_value(cfg, splits_file)
            if splits_file
            else catalog_path.parent / "splits.yaml"
        )
        if split_path.is_file():
            with split_path.open(encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
            for key, value in (loaded.get("splits") or loaded).items():
                splits_cfg.setdefault(key, value)

    defaults = {
        "validation": list(PAPER_VALIDATION_IDS),
        "lsg_ts_train": list(PAPER_LSG_TS_TRAIN_IDS),
        "lsg_ts_synthetic_train": list(PAPER_LSG_TS_SYNTHETIC_TRAIN_IDS),
        "lsg_max_train": _default_lsg_max_train_ids(),
        "lsg_max_synthetic_train": [f"FE{i}" for i in range(1, 48) if f"FE{i}" not in PAPER_VALIDATION_IDS],
    }
    out: dict[str, list[str]] = {}
    for key, fallback in defaults.items():
        raw = splits_cfg.get(key, fallback)
        out[key] = [normalize_event_id(x) for x in raw]
    return out


def _default_lsg_max_train_ids() -> list[str]:
    """45 synthetic (FE1–FE47 minus VE1/VE2) + historical 1999 and 2011."""
    synthetic = [f"FE{i}" for i in range(1, 48) if f"FE{i}" not in ("FE21", "FE26")]
    return synthetic + list(PAPER_HISTORICAL_TRAIN_IDS)


def indices_for_ids(
    event_ids: list[str],
    wanted: Iterable[str],
) -> np.ndarray:
    wanted_set = {normalize_event_id(w) for w in wanted}
    idx = [
        i
        for i, eid in enumerate(event_ids)
        if normalize_event_id(str(eid)) in wanted_set
    ]
    return np.asarray(idx, dtype=int)


def split_by_event_ids(
    event_ids: list[str],
    train_ids: Iterable[str],
    val_ids: Iterable[str],
) -> tuple[np.ndarray, np.ndarray] | None:
    """Return train/test indices when paper IDs are present; else None."""
    train_idx = indices_for_ids(event_ids, train_ids)
    test_idx = indices_for_ids(event_ids, val_ids)
    if train_idx.size == 0 or test_idx.size == 0:
        return None
    return train_idx, test_idx


def random_train_test_split(
    n: int, frac: float, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    n_train = max(1, int(n * frac))
    n_train = min(n_train, n - 1) if n > 1 else n
    return idx[:n_train], idx[n_train:]


def resolve_train_test_indices(
    event_ids: list[str],
    cfg: dict[str, Any],
    variant: str,
) -> tuple[np.ndarray, np.ndarray, str]:
    """
    Prefer Wang et al. (2026) event lists; fall back to random fraction.

    variant: ``lsg_ts`` or ``lsg_max``.
    """
    splits = load_split_ids(cfg)
    train_key = "lsg_ts_train" if variant == "lsg_ts" else "lsg_max_train"
    if cfg.get("events", {}).get("synthetic_only"):
        train_key = (
            "lsg_ts_synthetic_train" if variant == "lsg_ts" else "lsg_max_synthetic_train"
        )
    paper = split_by_event_ids(event_ids, splits[train_key], splits["validation"])
    if paper is not None:
        return paper[0], paper[1], f"paper:{train_key}"
    frac = float(cfg.get("lsg", {}).get("train_test_split", 0.8))
    seed = int(cfg.get("lsg", {}).get("random_seed", 42))
    train_idx, test_idx = random_train_test_split(len(event_ids), frac, seed)
    return train_idx, test_idx, "random_fraction"
