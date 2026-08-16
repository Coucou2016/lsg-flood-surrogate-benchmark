"""HEC-RAS 2D HDF / geometry adapters and local solver detection.

This module never invents inundation fields. It only:

- lists HDF groups/datasets
- reads Depth / Water Surface / cell centres / times when they exist
- reads geometry / terrain datasets when present
- detects a local HEC-RAS install and optionally launches an official plan

A tutorial ZIP that contains only GIS/terrain (no ``.p##.hdf`` results) is
expected. Python can still inspect geometry/terrain; paired HF/LF depth cubes
require running plans in HEC-RAS (GUI or ``Ras.exe -c``).
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np

_RESULTS_TS = "Results/Unsteady/Output/Output Blocks/Base Output/Unsteady Time Series"
_RESULTS_2D = f"{_RESULTS_TS}/2D Flow Areas"
_GEOM_2D = "Geometry/2D Flow Areas"

_DEPTH_NAMES = ("Depth", "Cell Depth", "Depths")
_WSE_NAMES = ("Water Surface", "Water Surface Elevation", "WSE")
_TIME_NAMES = ("Time",)
_CELL_XY_NAMES = ("Cells Center Coordinate", "Cells Centre Coordinate")
_CELL_Z_NAMES = ("Cells Minimum Elevation", "Cells Center Elevation")

_RAS_EXE_CANDIDATES = (
    Path(r"C:\Program Files (x86)\HEC\HEC-RAS"),
    Path(r"C:\Program Files\HEC\HEC-RAS"),
    Path(r"C:\Program Files (x86)\HEC"),
    Path(r"C:\Program Files\HEC"),
)


def _require_h5py():
    try:
        import h5py
    except ImportError as exc:
        raise ImportError(
            "Reading HEC-RAS HDF requires h5py. Install with: pip install h5py"
        ) from exc
    return h5py


def _as_str(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip("\x00").strip()
    if isinstance(value, np.ndarray):
        if value.shape == ():
            return _as_str(value.item())
        if value.size == 1:
            return _as_str(value.reshape(-1)[0])
    return str(value).strip()


def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p)


def walk_hdf(path: str | Path) -> list[dict[str, Any]]:
    """Return every group/dataset path with shape/dtype when applicable."""
    h5py = _require_h5py()
    path = Path(path)
    rows: list[dict[str, Any]] = []

    def _visitor(name: str, obj: Any) -> None:
        kind = "group" if isinstance(obj, h5py.Group) else "dataset"
        row: dict[str, Any] = {"path": name, "kind": kind}
        if kind == "dataset":
            row["shape"] = tuple(int(s) for s in obj.shape)
            row["dtype"] = str(obj.dtype)
        rows.append(row)

    with h5py.File(path, "r") as f:
        f.visititems(_visitor)
    return rows


def list_2d_flow_areas(path: str | Path) -> list[str]:
    """Names of 2D flow areas in Geometry and/or Results."""
    h5py = _require_h5py()
    names: list[str] = []
    seen: set[str] = set()
    with h5py.File(path, "r") as f:
        for root in (_GEOM_2D, _RESULTS_2D):
            if root not in f:
                continue
            grp = f[root]
            for key in grp.keys():
                if key not in seen and hasattr(grp[key], "keys"):
                    seen.add(key)
                    names.append(key)
    return names


def _first_dataset(grp: Any, names: Iterable[str]) -> Any | None:
    for name in names:
        if name in grp:
            return grp[name]
    return None


def _area_group(f: Any, root: str, area: str | None) -> tuple[str, Any]:
    if root not in f:
        raise KeyError(f"HDF is missing {root!r}")
    parent = f[root]
    if area is not None:
        if area not in parent:
            raise KeyError(f"2D flow area {area!r} not in {root}")
        return area, parent[area]
    # Siblings such as "Attributes" or "Cell Info" are compound datasets, not areas.
    keys = [k for k in parent.keys() if hasattr(parent[k], "keys")]
    if not keys:
        raise KeyError(f"No 2D flow areas under {root}")
    return keys[0], parent[keys[0]]


def read_cell_centers(
    path: str | Path,
    area: str | None = None,
) -> dict[str, Any]:
    """Cell-centre XY (and optional min elevation) from geometry HDF."""
    h5py = _require_h5py()
    path = Path(path)
    with h5py.File(path, "r") as f:
        name, grp = _area_group(f, _GEOM_2D, area)
        xy_ds = _first_dataset(grp, _CELL_XY_NAMES)
        if xy_ds is None:
            raise KeyError(
                f"No cell-centre dataset under Geometry/2D Flow Areas/{name}"
            )
        xy = np.asarray(xy_ds[()], dtype=np.float64)
        z_ds = _first_dataset(grp, _CELL_Z_NAMES)
        z = np.asarray(z_ds[()], dtype=np.float64) if z_ds is not None else None
    active = None if z is None else np.isfinite(z.reshape(-1))
    return {
        "area": name,
        "xy": xy,
        "elevation": z,
        "active": active,
        "n_cells": int(xy.shape[0]),
        "n_active": int(xy.shape[0]) if active is None else int(active.sum()),
        "source": str(path),
    }


def active_cell_mask(
    path: str | Path,
    area: str | None = None,
) -> np.ndarray | None:
    """
    Boolean mask of real (non-ghost) cells in a 2D flow area.

    HEC-RAS pads the perimeter of a 2D area with ghost cells whose
    ``Cells Minimum Elevation`` is NaN. Result datasets keep them, published
    geometry exports drop them (Fraehr ``remove_ghost_cells``), so a plan HDF
    reports more cells than the matching geometry NPZ. Returns ``None`` when
    the file has no geometry block to decide from.
    """
    path = Path(path)
    if not hdf_has_geometry(path):
        return None
    geom = read_cell_centers(path, area)
    return geom["active"]


def _decode_times(raw: Any) -> np.ndarray:
    arr = np.asarray(raw)
    if arr.dtype.kind in {"U", "S", "O"}:
        out = []
        for item in arr.reshape(-1):
            out.append(_as_str(item))
        return np.asarray(out)
    return arr.astype(np.float64, copy=False)


def read_unsteady_2d(
    path: str | Path,
    variable: str = "depth",
    area: str | None = None,
    drop_ghost_cells: bool = False,
) -> dict[str, Any]:
    """
    Read 2D unsteady Depth or WSE from a plan HDF (``*.p##.hdf``).

    Returns arrays with shape ``(n_times, n_cells)``. Raises ``KeyError`` if
    the file has geometry only (no Results block). With ``drop_ghost_cells``
    the perimeter ghost cells (see :func:`active_cell_mask`) are removed so the
    columns line up with a published geometry export.
    """
    h5py = _require_h5py()
    path = Path(path)
    var = variable.strip().lower()
    if var in {"depth", "depths", "h"}:
        names = _DEPTH_NAMES
        label = "depth"
    elif var in {"wse", "water surface", "water_surface", "stage"}:
        names = _WSE_NAMES
        label = "wse"
    else:
        names = (variable,)
        label = variable

    with h5py.File(path, "r") as f:
        if _RESULTS_2D not in f:
            raise KeyError(
                f"{path} has no 2D unsteady results. Run a HEC-RAS plan to "
                "produce a *.p##.hdf with Results/Unsteady/..."
            )
        name, grp = _area_group(f, _RESULTS_2D, area)
        ds = _first_dataset(grp, names)
        if ds is None:
            available = list(grp.keys())
            raise KeyError(
                f"No {label} dataset in 2D area {name!r}. Available: {available}"
            )
        values = np.asarray(ds[()], dtype=np.float64)
        time_path = _join(_RESULTS_TS, "Time")
        times = _decode_times(f[time_path][()]) if time_path in f else None
        active = None
        if drop_ghost_cells and _GEOM_2D in f:
            geom_area = name if name in f[_GEOM_2D] else None
            _, geom_grp = _area_group(f, _GEOM_2D, geom_area)
            z_ds = _first_dataset(geom_grp, _CELL_Z_NAMES)
            if z_ds is not None:
                active = np.isfinite(np.asarray(z_ds[()], dtype=np.float64).reshape(-1))

    if values.ndim == 1:
        values = values[np.newaxis, :]
    if active is not None and active.size == values.shape[1]:
        values = values[:, active]
    return {
        "area": name,
        "variable": label,
        "values": values,
        "times": times,
        "active": active,
        "n_times": int(values.shape[0]),
        "n_cells": int(values.shape[1]),
        "source": str(path),
    }


def hdf_has_results(path: str | Path) -> bool:
    h5py = _require_h5py()
    with h5py.File(path, "r") as f:
        return _RESULTS_2D in f


def hdf_has_geometry(path: str | Path) -> bool:
    h5py = _require_h5py()
    with h5py.File(path, "r") as f:
        return _GEOM_2D in f


def summarize_hdf(path: str | Path) -> dict[str, Any]:
    """Compact inventory of a RAS HDF (geometry and/or results)."""
    path = Path(path)
    summary: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "has_geometry": False,
        "has_results": False,
        "areas": [],
        "n_cells": None,
        "n_times": None,
        "variables": [],
    }
    if not path.is_file():
        return summary
    try:
        summary["has_geometry"] = hdf_has_geometry(path)
        summary["has_results"] = hdf_has_results(path)
        summary["areas"] = list_2d_flow_areas(path)
        if summary["has_geometry"]:
            centres = read_cell_centers(path)
            summary["n_cells"] = centres["n_cells"]
            summary["n_active_cells"] = centres["n_active"]
        if summary["has_results"]:
            for var in ("depth", "wse"):
                try:
                    res = read_unsteady_2d(path, var)
                except KeyError:
                    continue
                summary["variables"].append(var)
                summary["n_times"] = res["n_times"]
                summary["n_cells"] = res["n_cells"]
    except OSError as exc:
        summary["error"] = str(exc)
    return summary


def find_ras_hdf(root: str | Path) -> list[Path]:
    """Locate ``*.hdf`` / ``*.p*.hdf`` / ``*.g*.hdf`` under a case directory."""
    root = Path(root)
    if not root.exists():
        return []
    found: list[Path] = []
    for pattern in ("*.hdf", "*.HDF"):
        found.extend(root.rglob(pattern))
    uniq = []
    seen: set[Path] = set()
    for p in sorted(found):
        key = p.resolve()
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


@dataclass
class HecRasInstall:
    ras_exe: Path
    version_dir: Path
    version_name: str


def detect_hecras_install(
    extra_roots: Iterable[str | Path] | None = None,
) -> HecRasInstall | None:
    """Return the newest Ras.exe under common Program Files locations."""
    roots = list(_RAS_EXE_CANDIDATES)
    env = os.environ.get("HECRAS_HOME", "").strip()
    if env:
        roots.insert(0, Path(env))
    if extra_roots:
        roots.extend(Path(p) for p in extra_roots)

    candidates: list[HecRasInstall] = []
    for root in roots:
        if not root.exists():
            continue
        for exe in root.rglob("Ras.exe"):
            version_dir = exe.parent
            candidates.append(
                HecRasInstall(
                    ras_exe=exe,
                    version_dir=version_dir,
                    version_name=version_dir.name,
                )
            )
        for exe in root.rglob("ras.exe"):
            version_dir = exe.parent
            candidates.append(
                HecRasInstall(
                    ras_exe=exe,
                    version_dir=version_dir,
                    version_name=version_dir.name,
                )
            )
    if not candidates:
        return None
    candidates.sort(key=lambda c: str(c.version_dir), reverse=True)
    return candidates[0]


def run_hecras_plan(
    project_file: str | Path,
    plan_file: str | Path | None = None,
    timeout_s: int = 1200,
    ras_exe: str | Path | None = None,
) -> dict[str, Any]:
    """
    Compute a HEC-RAS plan via ``Ras.exe -c``.

    Default timeout is 20 minutes. Tutorial 2D unsteady runs can be slower;
    raise ``timeout_s`` if needed. This function will not wait overnight.
    """
    project_file = Path(project_file)
    if ras_exe is None:
        install = detect_hecras_install()
        if install is None:
            return {
                "ok": False,
                "reason": "HEC-RAS not found under Program Files (x86)/HEC or $HECRAS_HOME",
                "command": None,
            }
        ras_exe = install.ras_exe
    ras_exe = Path(ras_exe)
    if not project_file.is_file():
        return {
            "ok": False,
            "reason": f"Project file missing: {project_file}",
            "command": None,
        }
    cmd = [str(ras_exe), "-c", str(project_file)]
    if plan_file is not None:
        cmd.append(str(plan_file))
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "reason": f"Timed out after {timeout_s}s",
            "command": cmd,
        }
    except OSError as exc:
        return {"ok": False, "reason": str(exc), "command": cmd}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "command": cmd,
        "stdout": (proc.stdout or "")[-4000:],
        "stderr": (proc.stderr or "")[-4000:],
        "reason": None if proc.returncode == 0 else f"Ras.exe exit {proc.returncode}",
    }


@dataclass
class CaseLayout:
    """On-disk layout for an independent HEC-RAS multi-fidelity case."""

    root: Path
    original: Path = field(init=False)
    terrain: Path = field(init=False)
    gis: Path = field(init=False)
    boundary: Path = field(init=False)
    events: Path = field(init=False)
    geometries: dict[str, Path] = field(init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.original = self.root / "original"
        self.terrain = self.root / "terrain"
        self.gis = self.root / "gis"
        self.boundary = self.root / "boundary"
        self.events = self.root / "events"
        self.geometries = {}
        for child in self.root.iterdir() if self.root.is_dir() else []:
            name = child.name.lower()
            if child.is_dir() and (
                name.startswith("hf_") or name.startswith("lf_")
            ):
                self.geometries[child.name] = child

    def ensure_skeleton(self, geometry_names: Iterable[str]) -> None:
        for folder in (self.original, self.terrain, self.gis, self.boundary, self.events):
            folder.mkdir(parents=True, exist_ok=True)
        for name in geometry_names:
            dest = self.root / name
            dest.mkdir(parents=True, exist_ok=True)
            self.geometries[name] = dest
            note = dest / "README.md"
            if not note.exists():
                note.write_text(
                    f"# {name}\n\n"
                    "Skeleton only. Build this mesh in HEC-RAS Mapper from the "
                    "official terrain/GIS; do not treat this folder as a completed model.\n",
                    encoding="utf-8",
                )
