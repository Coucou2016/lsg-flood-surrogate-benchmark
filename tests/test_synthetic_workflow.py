"""Smoke test: synthetic data + LSG-TS vs LSG-Max pipeline."""

from lsg.data import generate_synthetic_floodplain
from lsg.lsg_max import LSGMaxModel
from lsg.lsg_ts import LSGTSModel


def test_lsg_variants_run_and_improve_over_random():
    cfg = {
        "hydrodynamic": {"depth_threshold_m": 0.03, "hf_cell_size_m": 25},
        "lsg": {
            "weight_by_cell_area": False,
            "max_eof_modes": 20,
            "inducing_point_fraction": 0.1,
            "train_test_split": 0.75,
            "random_seed": 0,
        },
    }
    data = generate_synthetic_floodplain(
        n_events=8, n_timesteps=24, shape_hf=(20, 25), lf_factor=4, seed=0
    )
    hf, lf = data["hf_depth"], data["lf_depth"]
    n_train = 6
    terrain = data["terrain_hf"]
    shape_hf, shape_lf = data["shape_hf"], data["shape_lf"]

    ts = LSGTSModel(cfg)
    ts.fit(hf[:n_train], lf[:n_train], terrain, shape_hf, shape_lf)
    pred_ts = ts.predict(lf[n_train:], terrain, shape_hf, shape_lf)
    m_ts = ts.evaluate(pred_ts, hf[n_train:])

    mx = LSGMaxModel(cfg)
    mx.fit(hf[:n_train], lf[:n_train], terrain, shape_hf, shape_lf)
    pred_mx = mx.predict(lf[n_train:], terrain, shape_hf, shape_lf)
    m_mx = mx.evaluate(pred_mx, hf[n_train:])

    assert m_ts["max_csi"] > 0.5
    assert m_mx["csi"] > 0.5
