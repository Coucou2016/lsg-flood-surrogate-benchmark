# Progress review — LSG public-data benchmark

**Date:** 2026-08-16 (updated after gap closure)  
**nature-writing axes:** `task=manuscript`, `paper_type=methods`, `language=en`, `journal=generic` (target WRR / JoH / EMS)  
**Repo baseline:** **no `.git`** (verified). Python: `.\.venv\Scripts\python.exe`.  
**Test gate (from `03_new_results.md`):** `.\.venv\Scripts\python.exe -m pytest tests -q` → **80 passed, 1 skipped**.  
**Figures:** `outputs/figures/figure_manifest.json` — `n_files` 24, **`skips=[]`**.

## One-sentence argument (working)

In multi-fidelity flood inundation surrogates, we show that an LSG stack with EXT+WSE dual fields, residual hierarchical zoning, CRPS-calibrated GP map uncertainty, and staged O1–O4 oracle attribution is reproducible on public Carlisle/Chowilla/Burnett cubes, with the main skill lift coming from multi-fidelity LSG rather than zoning, and with Chowilla acting as a strong-LF anti-case for all-cell scoring.

## What is implemented

| Capability | Status | Evidence |
|---|---|---|
| Fraehr ingest (Carlisle / Chowilla / Burnett) | Done | `config/{carlisle,chowilla,burnett}.yaml`, `data/DATA_INVENTORY.md` |
| `lsg.field: wse_ext` (EXT + WSE → depth) | Done | configs; workflow summaries |
| H-LSG `residual_kmeans` (WSE residuals; EXT global) | Done | default zoning in case YAMLs |
| Global A/B (`zoning: none`) | Done Chowilla **and Burnett** | `..._global_max.json` for both |
| `wet_correlation` zoning | Done Chowilla Grp1 | `..._wet_correlation_max.json` + Fig. 6 |
| SGPR inducing-point floor | Done | `lsg.min_inducing_points`; post-fix Carlisle summary |
| CRPS-scale UQ before/after | Done three cases | Carlisle workflow + Chowilla/Burnett `*_uq_calibrated.json` rescores |
| Cell-wise `inundation_prob` / P(wet) | Done three cases | `pred_examples.npz`; Fig. 5 panel (e) |
| O1–O4 error budgets | Done | `error_budget` in summaries |
| Pytest gate | Pass | 80 passed, 1 skipped (`03_new_results.md`) |

## Verified metrics (from JSON; Grp1 / protocol masks)

Sources: as in `docs/paper/03_new_results.md` and manuscript Tables 2–5.

### Point skill / zoning (headline)

| Case | Variant | Mask | CSI | RMSE (m) | Notes |
|---|---|---|---:|---:|---|
| Burnett | LF only | wet_train | 0.853 | 0.989 | Weak LF |
| Burnett | LSG-Max H-LSG | wet_train | 0.975 | 0.387 | Clear LSG lift |
| Burnett | LSG-Max global | wet_train | 0.975 | 0.179 | CSI flat vs H-LSG; O2−O1 0.049 |
| Chowilla | LSG-Max H-LSG | wet_train | 0.976 | 0.093 | Anti-case if scored all-cells (CSI 0.390) |
| Chowilla | LSG-Max global | wet_train | 0.974 | 0.088 | O2−O1 0.057 |
| Chowilla | LSG-Max wet_correlation | wet_train | 0.978 | 0.094 | O2−O1 0.010 |

### UQ calibration (`crps_scale`) before → after

| Case | `var_scale` | CRPS | cov90_active | Notes |
|---|---:|---|---|---|
| Carlisle Max | 0.417 | 0.039 → 0.028 | improves toward nominal | Headline win |
| Chowilla H-LSG (rescore) | 0.419 | 2.155 → 2.155 | 0.334 → 0.287 | **Flat CRPS; coverage worse** — report honestly |
| Burnett H-LSG (rescore) | 0.604 | 0.133 → 0.127 | 0.943 → 0.890 | Improves |

## Done vs open

**Done (newly closed)**

- Burnett global A/B; Chowilla/Burnett UQ before/after; cell-wise P(wet); Chowilla `wet_correlation` A/B; Fig. 3–6 regenerated (manifest skips empty).

**Open / 未运行**

- Chowilla / Burnett **full-TS** Grp1 folds (memory; Burnett HF stack ≈199 GB vs ~128 GB RAM) — **未运行**.
- Brisbane licensed TUFLOW/URBS appendix — **未运行**.
- FloodCastBench — deferred / **未运行**.
- Equal-capacity global vs H-LSG; nested CV for *s*; zone contiguity maps — **未运行 / 待补充**.

## Open science questions (for Discussion)

1. Why are O2−O1 zoning gains modest once SGPR is correct?
2. How should scoring protocols handle strong-LF anti-cases (Chowilla all-cells vs wet_train)?
3. Does CRPS-scale calibration transfer across events/sites without retuning? (Chowilla flat CRPS warns no.)
4. Where does residual hierarchical LSG sit relative to REOF-SGP (Wang et al. 2025) and regionalized LSG (Tan et al. 2025)?
