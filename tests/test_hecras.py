"""HEC-RAS HDF adapter and event-library protocol."""

from pathlib import Path

import numpy as np
import pytest

from lsg.config import load_config, resolve_path
from lsg.events import (
    generate_event_library,
    load_base_hydrograph,
    resample_hydrograph,
    write_event_hydrographs,
    write_event_table,
)
from lsg.hecras import (
    active_cell_mask,
    detect_hecras_install,
    hdf_has_geometry,
    hdf_has_results,
    list_2d_flow_areas,
    read_cell_centers,
    read_unsteady_2d,
    summarize_hdf,
    walk_hdf,
)

h5py = pytest.importorskip("h5py")

_AREA = "Yosemite Valley"


def _write_min_ras_hdf(path: Path, with_results: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    xy = np.array([[0.0, 0.0], [100.0, 0.0], [0.0, 100.0], [100.0, 100.0]])
    z = np.array([10.0, 11.0, 12.0, 13.0], dtype=np.float32)
    with h5py.File(path, "w") as f:
        geom = f.create_group(f"Geometry/2D Flow Areas/{_AREA}")
        geom.create_dataset("Cells Center Coordinate", data=xy)
        geom.create_dataset("Cells Minimum Elevation", data=z)
        if with_results:
            ts = f.create_group(
                "Results/Unsteady/Output/Output Blocks/Base Output/Unsteady Time Series"
            )
            ts.create_dataset(
                "Time",
                data=np.array([b"01JAN1997 00:00:00", b"01JAN1997 00:15:00"]),
            )
            area = ts.create_group(f"2D Flow Areas/{_AREA}")
            depth = np.array(
                [[0.1, 0.2, 0.0, 0.3], [0.4, 0.5, 0.1, 0.8]], dtype=np.float32
            )
            area.create_dataset("Depth", data=depth)
            area.create_dataset("Water Surface", data=depth + 10.0)
    return path


def test_read_geometry_only_hdf(tmp_path):
    hdf = _write_min_ras_hdf(tmp_path / "geom_only.g01.hdf", with_results=False)
    assert hdf_has_geometry(hdf)
    assert not hdf_has_results(hdf)
    centres = read_cell_centers(hdf)
    assert centres["n_cells"] == 4
    assert centres["area"] == _AREA
    assert centres["xy"].shape == (4, 2)
    with pytest.raises(KeyError, match="no 2D unsteady results"):
        read_unsteady_2d(hdf)


def test_read_depth_and_wse(tmp_path):
    hdf = _write_min_ras_hdf(tmp_path / "plan.p01.hdf", with_results=True)
    depth = read_unsteady_2d(hdf, "depth")
    wse = read_unsteady_2d(hdf, "wse")
    assert depth["values"].shape == (2, 4)
    assert wse["values"].shape == (2, 4)
    np.testing.assert_allclose(wse["values"] - depth["values"], 10.0)
    assert depth["times"] is not None
    assert list_2d_flow_areas(hdf) == [_AREA]
    rows = walk_hdf(hdf)
    assert any(r["path"].endswith("Depth") for r in rows)
    summary = summarize_hdf(hdf)
    assert summary["has_results"] is True
    assert summary["n_times"] == 2


def _write_ghost_cell_hdf(path: Path) -> Path:
    """Carlisle-shaped LF plan: WSE only, ghost cells, sibling compound datasets."""
    path.parent.mkdir(parents=True, exist_ok=True)
    xy = np.array(
        [[0.0, 0.0], [100.0, 0.0], [0.0, 100.0], [100.0, 100.0], [999.0, 999.0]]
    )
    z = np.array([10.0, 11.0, 12.0, 13.0, np.nan], dtype=np.float32)
    wse = np.array(
        [
            [10.5, 11.0, 12.4, 13.9, 0.0],
            [11.5, 12.0, 12.0, 14.9, 0.0],
            [12.5, 13.0, 12.6, 15.9, 0.0],
        ],
        dtype=np.float32,
    )
    with h5py.File(path, "w") as f:
        areas = f.create_group("Geometry/2D Flow Areas")
        # HEC-RAS stores compound datasets alongside the per-area groups.
        areas.create_dataset(
            "Cell Info", data=np.array([(0, 4)], dtype=[("start", "i4"), ("count", "i4")])
        )
        geom = areas.create_group(_AREA)
        geom.create_dataset("Cells Center Coordinate", data=xy)
        geom.create_dataset("Cells Minimum Elevation", data=z)
        ts = f.create_group(
            "Results/Unsteady/Output/Output Blocks/Base Output/Unsteady Time Series"
        )
        area = ts.create_group(f"2D Flow Areas/{_AREA}")
        area.create_dataset("Water Surface", data=wse)
    return path


def test_area_group_skips_compound_siblings(tmp_path):
    hdf = _write_ghost_cell_hdf(tmp_path / "ghost.p01.hdf")
    centres = read_cell_centers(hdf)
    assert centres["area"] == _AREA
    assert centres["n_cells"] == 5
    assert centres["n_active"] == 4
    assert list_2d_flow_areas(hdf) == [_AREA]


def test_drop_ghost_cells_matches_geometry_export(tmp_path):
    hdf = _write_ghost_cell_hdf(tmp_path / "ghost.p01.hdf")
    np.testing.assert_array_equal(
        active_cell_mask(hdf), [True, True, True, True, False]
    )
    full = read_unsteady_2d(hdf, "wse")
    trimmed = read_unsteady_2d(hdf, "wse", drop_ghost_cells=True)
    assert full["n_cells"] == 5
    assert trimmed["n_cells"] == 4
    np.testing.assert_allclose(trimmed["values"], full["values"][:, :4])


def test_summarize_hdf_handles_wse_only_plan(tmp_path):
    hdf = _write_ghost_cell_hdf(tmp_path / "ghost.p01.hdf")
    summary = summarize_hdf(hdf)
    assert summary["variables"] == ["wse"]
    assert summary["n_cells"] == 5
    assert summary["n_active_cells"] == 4
    assert summary["n_times"] == 3


def test_real_merced_hdf_if_present():
    root = Path(__file__).resolve().parents[1]
    hdf_files = list((root / "data" / "external" / "hecras_merced").rglob("*.hdf"))
    hdf_files += list((root / "data" / "external" / "hecras_merced").rglob("*.HDF"))
    if not hdf_files:
        pytest.skip("No official HEC-RAS HDF in the Merced case folder yet")
    summary = summarize_hdf(hdf_files[0])
    assert summary["exists"]
    assert summary["has_geometry"] or summary["has_results"]


def test_detect_hecras_install_does_not_raise():
    install = detect_hecras_install()
    assert install is None or install.ras_exe.name.lower() == "ras.exe"


def test_event_library_40_splits():
    specs = generate_event_library(n_events=40, seed=20260814, id_prefix="ME")
    assert len(specs) == 40
    counts = {k: 0 for k in ("train", "val", "test")}
    for e in specs:
        counts[e.split] += 1
        assert 0.6 - 1e-9 <= e.a <= 1.6 + 1e-9
        assert 0.8 - 1e-9 <= e.s <= 1.2 + 1e-9
        assert -3.0 - 1e-9 <= e.tau_hours <= 3.0 + 1e-9
        assert e.drives == ("hf_100ft", "lf_400ft", "lf_800ft")
    assert counts == {"train": 24, "val": 6, "test": 10}
    test = [e for e in specs if e.split == "test"]
    n_interp = sum(1 for e in test if e.test_kind == "interpolation")
    n_extrap = sum(1 for e in test if e.test_kind.startswith("extrap"))
    assert n_interp == 6
    assert n_extrap == 4


def test_event_library_10_pilot_and_tributaries(tmp_path):
    specs = generate_event_library(
        n_events=10,
        seed=20260814,
        id_prefix="BE",
        drives=("hf_200ft", "lf_500ft", "lf_1000ft"),
        tributaries=("sayers_dam", "marsh_creek"),
    )
    assert len(specs) == 10
    assert sum(e.split == "train" for e in specs) == 6
    assert sum(e.split == "test" for e in specs) == 2
    for e in specs:
        assert set(e.tributary_eps) == {"sayers_dam", "marsh_creek"}
        for eps in e.tributary_eps.values():
            assert -0.15 - 1e-9 <= eps <= 0.15 + 1e-9
    t = np.linspace(0, 10, 21)
    q0 = np.exp(-((t - 4.0) ** 2) / 2.0)
    written = write_event_hydrographs(tmp_path, specs[:3], t, q0, tributaries=("sayers_dam",))
    assert len(written) == 3
    text = written[0].read_text(encoding="utf-8")
    assert "q_sayers_dam" in text
    write_event_table(tmp_path / "event_parameters.csv", specs)
    rows = (tmp_path / "event_parameters.csv").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 11


def test_resample_hydrograph_scales_peak():
    t = np.linspace(0, 10, 101)
    q0 = np.exp(-((t - 5.0) ** 2) / 0.5)
    _, q = resample_hydrograph(t, q0, a=1.5, s=1.0, tau_hours=0.0)
    assert q.max() == pytest.approx(1.5 * q0.max(), rel=1e-6)


def test_merced_and_bald_eagle_configs_load():
    root = Path(__file__).resolve().parents[1]
    merced = load_config(root / "config" / "merced.yaml")
    bald = load_config(root / "config" / "bald_eagle.yaml")
    cases = load_config(root / "config" / "cases.yaml")
    assert merced["_project_root"] == root.resolve()
    assert merced["study_area"]["id"] == "merced"
    assert resolve_path(merced, "case_root") == (root / "data" / "external" / "hecras_merced").resolve()
    assert bald["study_area"]["id"] == "bald_eagle"
    assert "sayers_dam" in bald["events"]["tributaries"]
    assert cases["existing_published"]["carlisle"]["status"] == "primary"
    assert cases["deferred_generator_only"]["merced"]["status"] == "not_required"


def test_load_usgs_rdb_if_present():
    root = Path(__file__).resolve().parents[1]
    rdb = root / "data" / "external" / "hecras_merced" / "boundary" / "usgs_11264500_happy_isles_1997_iv.txt"
    if not rdb.is_file() or rdb.stat().st_size < 100:
        pytest.skip("USGS Happy Isles RDB not downloaded")
    t, q = load_base_hydrograph(rdb)
    assert t.size >= 10
    assert q.max() > 0
