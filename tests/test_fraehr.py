"""Published Fraehr-layout ingest and unstructured LF→HF interpolation."""

from pathlib import Path

import numpy as np
import pytest

from lsg.config import load_config
from lsg.data import detect_real_event_data
from lsg.fraehr import (
    align_lf_to_hf_time,
    discover_layout,
    event_sort_key,
    ingest_fraehr_case,
    load_geometry_npz,
    wse_to_depth,
)
from lsg.lsg_max import LSGMaxModel
from lsg.spatial import interpolate_lf_to_hf_xy, nearest_cell_indices


def test_nearest_cell_indices_identity():
    xy = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    np.testing.assert_array_equal(nearest_cell_indices(xy, xy), [0, 1, 2])


def test_interpolate_lf_to_hf_xy_copies_nearest():
    xy_hf = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [10.0, 10.0]])
    xy_lf = np.array([[0.0, 0.0], [10.0, 10.0]])
    depth_lf = np.array([[1.0, 4.0], [2.0, 8.0]])
    out = interpolate_lf_to_hf_xy(depth_lf, xy_lf, xy_hf)
    assert out.shape == (2, 4)
    np.testing.assert_allclose(out[0], [1.0, 1.0, 1.0, 4.0])


def test_interpolate_lf_to_hf_xy_wse_clips_to_hf_dem():
    """Fraehr path: LF depth → WSE → nearest HF → clip to HF DEM → depth.

    A coarse LF cell with 1 m depth over low ground must not flood a much
    higher neighbouring HF cell (the depth-only bug that drove RFA ≈ 0.25).
    """
    xy_lf = np.array([[0.0, 0.0]])
    xy_hf = np.array([[0.0, 0.0], [1.0, 0.0]])
    terrain_lf = np.array([0.0])
    terrain_hf = np.array([0.0, 5.0])
    depth_lf = np.array([[1.0]])

    depth_only = interpolate_lf_to_hf_xy(depth_lf, xy_lf, xy_hf)
    np.testing.assert_allclose(depth_only[0], [1.0, 1.0])

    out = interpolate_lf_to_hf_xy(
        depth_lf,
        xy_lf,
        xy_hf,
        terrain_hf=terrain_hf,
        terrain_lf=terrain_lf,
        dry_threshold_m=0.03,
    )
    np.testing.assert_allclose(out[0], [1.0, 0.0])


def test_interpolate_lf_to_hf_xy_wse_preserves_nan_pad_rows():
    xy_lf = np.array([[0.0, 0.0], [2.0, 0.0]])
    xy_hf = np.array([[0.0, 0.0], [2.0, 0.0]])
    terrain_lf = np.array([10.0, 10.0])
    terrain_hf = np.array([10.0, 10.5])
    depth_lf = np.array([[0.5, 0.0], [np.nan, np.nan]])
    out = interpolate_lf_to_hf_xy(
        depth_lf,
        xy_lf,
        xy_hf,
        terrain_hf=terrain_hf,
        terrain_lf=terrain_lf,
    )
    np.testing.assert_allclose(out[0], [0.5, 0.0])
    assert np.isnan(out[1]).all()


def test_wse_to_depth_drops_ghost_and_dry():
    elev = np.array([10.0, np.nan, 12.0])
    wse = np.array([[10.5, 0.0, 12.01], [11.0, 1.0, 12.2]])
    depth, keep, elev_kept = wse_to_depth(wse, elev, threshold_m=0.03)
    np.testing.assert_array_equal(keep, [True, False, True])
    assert depth.shape == (2, 2)
    np.testing.assert_allclose(depth[0], [0.5, 0.0])
    np.testing.assert_allclose(elev_kept, [10.0, 12.0])


def test_ingest_fraehr_mini_case(tmp_path):
    geom = tmp_path / "Geometry_data"
    hd_hf = tmp_path / "HD_model_data" / "HF"
    hd_lf = tmp_path / "HD_model_data" / "LF"
    geom.mkdir()
    hd_hf.mkdir(parents=True)
    hd_lf.mkdir(parents=True)

    xy_hf = np.array([[0.0, 0.0], [5.0, 0.0], [0.0, 5.0], [5.0, 5.0]])
    z_hf = np.array([1.0, 1.0, 1.0, 1.0])
    xy_lf = np.array([[0.0, 0.0], [5.0, 5.0]])
    z_lf = np.array([1.0, 1.0])
    np.savez(geom / "HF_geom.npz", XY_coor=xy_hf, Z_coor=z_hf, Area=np.full(4, 25.0))
    np.savez(geom / "LF_geom.npz", XY_coor=xy_lf, Z_coor=z_lf, Area=np.full(2, 100.0))

    for i in range(1, 5):
        hf = np.array(
            [
                [0.20 * i, 0.00, 0.10 * i, 0.30 * i],
                [0.25 * i, 0.05, 0.12 * i, 0.35 * i],
            ],
            dtype=np.float64,
        )
        lf = np.array(
            [
                [0.15 * i, 0.28 * i],
                [0.18 * i, 0.32 * i],
            ],
            dtype=np.float64,
        )
        np.savez(hd_hf / f"HF.p0{i}.npz", depth=hf)
        np.savez(hd_lf / f"LF.p0{i}.npz", depth=lf)

    loaded = load_geometry_npz(geom / "HF_geom.npz")
    assert loaded["xy"].shape == (4, 2)

    data = ingest_fraehr_case(tmp_path, threshold_m=0.03)
    assert data["event_ids"] == ["E1", "E2", "E3", "E4"]
    assert data["hf_depth"].shape == (4, 2, 4)
    assert data["lf_depth"].shape == (4, 2, 2)
    assert data["xy_hf"].shape == (4, 2)
    assert data["terrain_lf"].shape == (2,)
    np.testing.assert_allclose(data["terrain_lf"], z_lf)

    cfg = {
        "hydrodynamic": {"depth_threshold_m": 0.03, "hf_cell_size_m": 5},
        "lsg": {
            "weight_by_cell_area": True,
            "max_eof_modes": 4,
            "inducing_point_fraction": 0.5,
            "train_test_split": 0.5,
            "random_seed": 0,
        },
    }
    model = LSGMaxModel(cfg)
    model.fit(
        data["hf_depth"][:3],
        data["lf_depth"][:3],
        data["terrain_hf"],
        data["shape_hf"],
        data["shape_lf"],
        xy_hf=data["xy_hf"],
        xy_lf=data["xy_lf"],
        area_hf=data["area_hf"],
        terrain_lf=data["terrain_lf"],
    )
    pred = model.predict(
        data["lf_depth"][3:],
        data["terrain_hf"],
        data["shape_hf"],
        data["shape_lf"],
        xy_hf=data["xy_hf"],
        xy_lf=data["xy_lf"],
        terrain_lf=data["terrain_lf"],
    )
    assert pred.shape == (1, 4)
    assert model.state is not None
    assert model.state.terrain_lf is not None
    np.testing.assert_allclose(model.state.terrain_lf, z_lf)


def test_align_lf_to_hf_time_keeps_trailing_steps():
    lf = np.arange(6).reshape(6, 1).astype(float)
    np.testing.assert_allclose(align_lf_to_hf_time(lf, 4), [[2.0], [3.0], [4.0], [5.0]])
    np.testing.assert_allclose(align_lf_to_hf_time(lf, 9), lf)


def test_ingest_fraehr_lf_hdf_ghost_cells_and_warmup(tmp_path):
    """Carlisle shape: LF plan HDF has ghost cells and extra leading timesteps."""
    h5py = pytest.importorskip("h5py")

    geom = tmp_path / "Geometry_data"
    hd_hf = tmp_path / "HD_model_data" / "High-fidelity"
    hd_lf = tmp_path / "HD_model_data" / "Low-fidelity"
    geom.mkdir()
    hd_hf.mkdir(parents=True)
    hd_lf.mkdir(parents=True)

    xy_hf = np.array([[0.0, 0.0], [5.0, 0.0], [0.0, 5.0], [5.0, 5.0]])
    z_hf = np.full(4, 10.0)
    # Two real LF cells plus one perimeter ghost cell, as HEC-RAS writes them.
    xy_lf_all = np.array([[0.0, 0.0], [5.0, 5.0], [99.0, 99.0]])
    z_lf_all = np.array([10.0, 10.0, np.nan], dtype=np.float32)
    np.savez(geom / "Lisflood_Geometry_data.npz", XY_coor=xy_hf, Z_coor=z_hf,
             Area=np.full(4, 25.0))
    np.savez(geom / "LF_Geometry_data.npz", XY_coor=xy_lf_all[:2],
             Z_coor=z_lf_all[:2], Area=np.full(2, 100.0))

    n_warmup = 3
    for i in range(1, 5):
        n_t = 2 + i
        hf_wse = 10.0 + 0.1 * i * np.arange(1, n_t + 1)[:, None] * np.ones((1, 4))
        np.savez(hd_hf / f"Run{i}_alltimesteps.npz", wse_data=hf_wse)

        lf_wse = np.zeros((n_warmup + n_t, 3), dtype=np.float32)
        lf_wse[n_warmup:, :2] = 10.0 + 0.1 * i * np.arange(1, n_t + 1)[:, None]
        with h5py.File(hd_lf / f"Carlisle_LFmodelA.p0{i}.hdf", "w") as f:
            g = f.create_group("Geometry/2D Flow Areas/Carlisle")
            g.create_dataset("Cells Center Coordinate", data=xy_lf_all)
            g.create_dataset("Cells Minimum Elevation", data=z_lf_all)
            res = f.create_group(
                "Results/Unsteady/Output/Output Blocks/Base Output/"
                "Unsteady Time Series/2D Flow Areas/Carlisle"
            )
            res.create_dataset("Water Surface", data=lf_wse)

    data = ingest_fraehr_case(tmp_path, threshold_m=0.03, event_ids=["E2"])
    assert data["event_ids"] == ["E2"]
    # Ghost cell dropped, so LF matches the published LF geometry export.
    assert data["lf_depth"].shape == (1, 4, 2)
    assert data["hf_depth"].shape == (1, 4, 4)
    # Warm-up rows dropped, so LF and HF describe the same instants.
    np.testing.assert_allclose(
        data["lf_depth"][0, :, 0], data["hf_depth"][0, :, 0], atol=1e-6
    )


def test_carlisle_config_not_available_until_unzip():
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "config" / "carlisle.yaml")
    status = detect_real_event_data(cfg)
    assert status["kind"] == "fraehr"
    layout = discover_layout(status["case_root"])
    assert layout["case_root"].exists()
    if not (root / "data" / "external" / "carlisle" / "HD_model_data").exists():
        assert status["available"] is False


def test_event_sort_key_natural_order():
    ids = ["E10", "E2", "E1", "E29"]
    assert sorted(ids, key=event_sort_key) == ["E1", "E2", "E10", "E29"]


def test_ingest_fraehr_time_reduction_max(tmp_path):
    geom = tmp_path / "Geometry_data"
    hd_hf = tmp_path / "HD_model_data" / "HF"
    hd_lf = tmp_path / "HD_model_data" / "LF"
    geom.mkdir()
    hd_hf.mkdir(parents=True)
    hd_lf.mkdir(parents=True)

    xy_hf = np.array([[0.0, 0.0], [5.0, 0.0], [0.0, 5.0], [5.0, 5.0]])
    z_hf = np.array([1.0, 1.0, 1.0, 1.0])
    xy_lf = np.array([[0.0, 0.0], [5.0, 5.0]])
    z_lf = np.array([1.0, 1.0])
    np.savez(geom / "HF_geom.npz", XY_coor=xy_hf, Z_coor=z_hf, Area=np.full(4, 25.0))
    np.savez(geom / "LF_geom.npz", XY_coor=xy_lf, Z_coor=z_lf, Area=np.full(2, 100.0))

    for i in range(1, 4):
        hf = np.array(
            [
                [0.10 * i, 0.00, 0.05 * i, 0.20 * i],
                [0.40 * i, 0.05, 0.12 * i, 0.50 * i],
                [0.25 * i, 0.02, 0.08 * i, 0.30 * i],
            ],
            dtype=np.float64,
        )
        lf = np.array(
            [
                [0.15 * i, 0.28 * i],
                [0.35 * i, 0.45 * i],
                [0.18 * i, 0.32 * i],
            ],
            dtype=np.float64,
        )
        np.savez(hd_hf / f"HF.p0{i}.npz", depth=hf)
        np.savez(hd_lf / f"LF.p0{i}.npz", depth=lf)

    data = ingest_fraehr_case(tmp_path, threshold_m=0.03, time_reduction="max")
    assert data["event_ids"] == ["E1", "E2", "E3"]
    assert data["hf_depth"].shape == (3, 1, 4)
    assert data["lf_depth"].shape == (3, 1, 2)
    assert data["meta"]["time_reduction"] == "max"
    np.testing.assert_allclose(data["hf_depth"][0, 0], [0.40, 0.05, 0.12, 0.50])


def test_chowilla_config_and_layout_when_present():
    root = Path(__file__).resolve().parents[1]
    cfg_path = root / "config" / "chowilla.yaml"
    assert cfg_path.is_file()
    cfg = load_config(cfg_path)
    assert cfg["study_area"]["id"] == "chowilla"
    assert cfg["lsg"]["field"] == "wse_ext"
    assert cfg["lsg"]["zoning"] == "residual_kmeans"
    assert cfg["lsg"]["min_inducing_points"] == 16
    assert cfg["evaluation"]["uq_calibration"] == "crps_scale"
    assert (cfg.get("ingest") or {}).get("time_reduction") == "max"
    status = detect_real_event_data(cfg)
    assert status["kind"] == "fraehr"
    layout = discover_layout(status["case_root"])
    hd = root / "data" / "external" / "chowilla" / "HD_model_data"
    geom = root / "data" / "external" / "chowilla" / "Geometry_data"
    if hd.is_dir() and geom.is_dir():
        assert status["available"] is True
        assert status["paired_event_ids"][:3] == ["E1", "E2", "E3"]
        assert "E10" in status["paired_event_ids"]
        # Natural order: E2 before E10.
        assert status["paired_event_ids"].index("E2") < status["paired_event_ids"].index(
            "E10"
        )
        assert (geom / "Geometry_data_HF.npz").is_file()
        assert (geom / "Geometry_data_LF.npz").is_file()
    else:
        assert status["available"] is False


def test_burnett_config_and_layout_when_present():
    root = Path(__file__).resolve().parents[1]
    cfg_path = root / "config" / "burnett.yaml"
    assert cfg_path.is_file()
    cfg = load_config(cfg_path)
    assert cfg["study_area"]["id"] == "burnett"
    assert cfg["lsg"]["field"] == "wse_ext"
    assert cfg["lsg"]["zoning"] == "residual_kmeans"
    assert cfg["lsg"]["min_inducing_points"] == 16
    assert cfg["evaluation"]["uq_calibration"] == "crps_scale"
    assert cfg["evaluation"]["cell_mask"] == "wet_train"
    assert (cfg.get("ingest") or {}).get("time_reduction") == "max"
    assert "E12" in cfg["events"]["splits"]["validation"]
    assert len(cfg["events"]["splits"]["validation"]) == 18
    assert len(cfg["events"]["splits"]["lsg_max_train"]) == 56
    status = detect_real_event_data(cfg)
    assert status["kind"] == "fraehr"
    hd = root / "data" / "external" / "burnett" / "HD_model_data"
    geom = root / "data" / "external" / "burnett" / "Geometry_data"
    summary = root / "data" / "external" / "burnett" / "BurnettRV_event_summary.csv"
    if hd.is_dir() and geom.is_dir() and summary.is_file():
        assert status["available"] is True
        assert len(status["paired_event_ids"]) == 74
        assert "E12" in status["paired_event_ids"]
        assert "E1" in status["paired_event_ids"]
        # Plan-based ids: E1 before E12 (natural order).
        assert status["paired_event_ids"].index("E1") < status["paired_event_ids"].index(
            "E12"
        )
        assert (geom / "Tuflow_Geometry_data.npz").is_file()
        assert (geom / "HECRAS_Geometry_data.npz").is_file()
    else:
        assert status["available"] is False


def test_ingest_burnett_style_wl_data_warmup_and_csv_pair(tmp_path):
    """Burnett: TUFLOW wl_data + CSV plan pairing + 48-step pad skip."""
    import csv

    geom = tmp_path / "Geometry_data"
    hd_hf = tmp_path / "HD_model_data" / "High-fidelity"
    hd_lf = tmp_path / "HD_model_data" / "Low-fidelity"
    geom.mkdir()
    hd_hf.mkdir(parents=True)
    hd_lf.mkdir(parents=True)

    xy_hf = np.array([[0.0, 0.0], [5.0, 0.0], [0.0, 5.0], [5.0, 5.0]])
    z_hf = np.array([1.0, 1.0, 1.0, 1.0])
    xy_lf = np.array([[0.0, 0.0], [5.0, 5.0]])
    z_lf = np.array([1.0, 1.0])
    np.savez(
        geom / "Tuflow_Geometry_data.npz",
        XY_coor=xy_hf,
        Z_coor=z_hf,
        Area=np.full(4, 25.0),
    )
    np.savez(
        geom / "HECRAS_Geometry_data.npz",
        XY_coor=xy_lf,
        Z_coor=z_lf,
        Area=np.full(2, 100.0),
    )

    with (tmp_path / "BurnettRV_event_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "No",
                "tuflow_evt_name_old",
                "tuflow_evt_name_new",
                "HEC_RAS_plan",
                "Group",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "No": 1,
                "tuflow_evt_name_old": "e_demo_a",
                "tuflow_evt_name_new": "e_demo_a",
                "HEC_RAS_plan": "p12",
                "Group": 1,
            }
        )
        writer.writerow(
            {
                "No": 2,
                "tuflow_evt_name_old": "e_demo_b",
                "tuflow_evt_name_new": "e_demo_b",
                "HEC_RAS_plan": "p30",
                "Group": 2,
            }
        )

    warmup = 48
    for stem, plan, peak in (("e_demo_a", "p12", 0.8), ("e_demo_b", "p30", 1.2)):
        wl = np.ones((warmup + 3, 4), dtype=np.float64)
        wl[:warmup] = 1.0  # dry pad (WSE == Z)
        wl[warmup:] = 1.0 + peak
        np.savez(hd_hf / f"Paradise_{stem}_002.npz", wl_data=wl, time_data=np.arange(warmup + 3))
        lf = np.array([[0.5 * peak, 0.6 * peak]], dtype=np.float64)
        np.savez(hd_lf / f"BurnettRV_LFmodelB.{plan}.npz", depth=lf)

    data = ingest_fraehr_case(tmp_path, threshold_m=0.03, time_reduction="max")
    assert data["event_ids"] == ["E12", "E30"]
    assert data["hf_depth"].shape == (2, 1, 4)
    assert data["lf_depth"].shape == (2, 1, 2)
    # Max after warmup skip → peak depths.
    np.testing.assert_allclose(data["hf_depth"][0, 0], [0.8, 0.8, 0.8, 0.8])
    np.testing.assert_allclose(data["hf_depth"][1, 0], [1.2, 1.2, 1.2, 1.2])
