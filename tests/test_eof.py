import numpy as np

from lsg import eof


def test_eof_roundtrip():
    rng = np.random.default_rng(0)
    data = rng.normal(size=(20, 50))
    pca, mean = eof.fit_eof(data, weights=None, n_components=50)
    modes = pca.components_
    ecs = eof.project_pseudo_ecs(data, modes, None, mean)
    recon = eof.reconstruct_from_ecs(ecs, modes, mean, None)
    assert recon.shape == data.shape
    assert np.allclose(recon, data, atol=1e-4)


def test_norths_rule_positive():
    rng = np.random.default_rng(1)
    data = rng.normal(size=(30, 40))
    pca, _ = eof.fit_eof(data, n_components=15)
    n = eof.select_n_modes(pca, 30)
    assert 1 <= n <= 15
