# Progress review — LSG public-data benchmark

**Date:** 2026-08-16  
**nature-writing axes:** `task=manuscript`, `paper_type=methods`, `language=en`, `journal=generic` (target WRR / JoH / EMS)  
**Repo baseline:** **no `.git`** (verified). Python: `.\.venv\Scripts\python.exe`.  
**Test gate:** `.\.venv\Scripts\python.exe -m pytest tests -q` → **74 passed, 1 skipped** (128 s).

## One-sentence argument (working)

In multi-fidelity flood inundation surrogates, we show that an LSG stack with EXT+WSE dual fields, residual hierarchical zoning, CRPS-calibrated GP map uncertainty, and staged O1–O4 oracle attribution is reproducible on public Carlisle/Chowilla/Burnett cubes, with the main skill lift coming from multi-fidelity LSG rather than zoning, and with Chowilla acting as a strong-LF anti-case for all-cell scoring.

## What is implemented

| Capability | Status | Evidence |
|---|---|---|
| Fraehr ingest (Carlisle / Chowilla / Burnett) | Done | `config/{carlisle,chowilla,burnett}.yaml`, `data/DATA_INVENTORY.md` |
| `lsg.field: wse_ext` (EXT + WSE → depth) | Done | configs; workflow summaries |
| H-LSG `residual_kmeans` (WSE residuals; EXT global) | Done | default zoning in case YAMLs |
| Global A/B (`zoning: none`) | Done for Chowilla | `workflow_summary_grp1_wse_ext_global_max.json` |
| SGPR inducing-point floor | Done | `lsg.min_inducing_points`; post-fix Carlisle summary |
| CRPS-scale UQ calibration | Done | Carlisle `*_uq_calibrated.json`; Chowilla/Burnett `uq_calibration` blocks |
| O1–O4 error budgets | Done | `error_budget` in summaries |
| Pytest gate | Pass | 74 passed, 1 skipped |

## Verified metrics (from JSON; Grp1 / protocol masks)

Sources:

- Carlisle: `outputs/evaluation/carlisle/workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json` (+ `*_uq_calibrated.json`)
- Chowilla H-LSG: `outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_max.json`
- Chowilla global: `outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_max.json`
- Burnett: `outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max.json`

### Point skill (CSI / RMSE)

| Case | Variant | Mask | CSI | RMSE (m) | Notes |
|---|---|---|---:|---:|---|
| Carlisle | LF only | all_cells | 0.960 | 0.074 | |
| Carlisle | LF only | wet_train | 0.966 | 0.101 | |
| Carlisle | LSG-TS (max surface) | all / wet_train | 0.970 / 0.970 | 0.099 / 0.154 | H-LSG + SGPR fix |
| Carlisle | LSG-Max | all / wet_train | 0.976 / 0.976 | 0.061 / 0.094 | Headline Max |
| Chowilla | LF only | all / wet_train | 0.930 / 0.925 | 0.690 / 0.690 | Strong LF extent |
| Chowilla | LSG-Max H-LSG | all / wet_train | **0.390** / **0.976** | **3.789** / **0.093** | Anti-case if scored all-cells |
| Chowilla | LSG-Max global | all / wet_train | 0.390 / 0.974 | 3.789 / 0.088 | Zoning ≠ CSI driver |
| Burnett | LF only | all / wet_train | 0.853 / 0.853 | 0.983 / 0.989 | Weak LF |
| Burnett | LSG-Max H-LSG | all / wet_train | 0.975 / 0.975 | 0.384 / 0.387 | Clear LSG lift |

### O1–O4 test budgets (depth RMSE on protocol wet index)

| Case | Variant | O1 | O2 | O3 | O4 | O2−O1 |
|---|---|---:|---:|---:|---:|---:|
| Carlisle | LSG-TS H-LSG | 0.018 | 0.033 | 0.240 | 0.102 | 0.015 |
| Carlisle | LSG-Max H-LSG | 0.048 | 0.052 | 0.068 | 0.094 | **0.005** |
| Chowilla | LSG-Max H-LSG | 0.020 | 0.034 | 0.701 | 0.093 | **0.013** |
| Chowilla | LSG-Max global | 0.020 | 0.078 | 0.666 | 0.088 | **0.057** |
| Burnett | LSG-Max H-LSG | 0.074 | 0.083 | 0.668 | 0.387 | **0.009** |

Interpretation locked for paper drafting: residual zoning shrinks the truncation gap (O2−O1) on Max-style paths, but CSI/RMSE lifts vs LF are dominated by multi-fidelity LSG. Do not lead with “zoning beats global by large CSI”.

### UQ calibration (`crps_scale`)

| Case | Surface | `var_scale` | Notes |
|---|---|---:|---|
| Carlisle Max | calibrated | **0.417** | CRPS 0.039 → 0.028; CSI/RMSE unchanged |
| Carlisle TS | calibrated | 0.900 | Near-calibrated already |
| Chowilla H-LSG | Max path | **0.309** | Prefer `coverage_*_active` |
| Chowilla global | Max path | 0.419 | |
| Burnett H-LSG | Max path | 0.606 | |

## Done vs open

**Done**

- Three-case public-data EXT+WSE stack with residual zoning + SGPR floor + CRPS UQ + O1–O4.
- Carlisle Grp1 full TS/Max after SGPR fix; Chowilla/Burnett Grp1 max-surface folds.
- Chowilla global A/B for zoning contrast.

**Open / 未运行**

- Chowilla / Burnett **full-TS** Grp1 folds (memory) — **未运行**.
- Burnett global A/B polish — config exists (`burnett_global.yaml`); full Grp1 global summary not used as headline here — treat comparative global Burnett as **未运行** unless a matching summary is added.
- `wet_correlation` zoning sweep — **未运行** as paper default.
- Brisbane licensed TUFLOW/URBS appendix — **未运行** (licence-gated).
- FloodCastBench — deferred / **未运行**.
- Paper figures: another agent regenerating SciencePlots figures — reference by intended name only; do not treat regenerated assets as verified here.

## Open science questions (for Discussion)

1. Why are O2−O1 zoning gains modest once SGPR is correct?
2. How should scoring protocols handle strong-LF anti-cases (Chowilla all-cells vs wet_train)?
3. Does CRPS-scale calibration transfer across events/sites without retuning?
4. Where does residual hierarchical LSG sit relative to REOF-SGP (Wang et al. 2025) and regionalized LSG (Tan et al. 2025)?
