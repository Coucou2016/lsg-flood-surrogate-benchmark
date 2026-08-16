# Carlisle equal-capacity control (Grp1 Max)

Numbers read from on-disk JSON only. Host: Dell Precision 7920 Tower, 2× Intel Xeon Gold 6133, ~128 GB RAM. Workspace has **no `.git`**.

## Design

Mirror of Chowilla Exp 1 (`04_capacity_controls.md`):

| Run | Config | Summary artifact |
|-----|--------|------------------|
| Global native | `config/carlisle_global.yaml` | `outputs/evaluation/carlisle/workflow_summary_grp1_wse_ext_global_max_capacity.json` |
| Global matched (`force_n_modes: 13`) | `config/carlisle_global_matched13.yaml` | `.../workflow_summary_grp1_wse_ext_global_matched13_max.json` |
| H-LSG residual_modes=0 | `config/carlisle_hlsg_budget1.yaml` | `.../workflow_summary_grp1_wse_ext_hlsg_budget1_max.json` |
| H-LSG baseline (prior) | `config/carlisle.yaml` | `.../workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json` |

H-LSG WSE GP input dim on Carlisle Max = 1 global + 4×3 residual = **13**. LSG-Max train *N* = 8 events, so a global-only EOF cannot realise 13 modes: `force_n_modes: 13` is capped by `pca.n_components_` to **8** (full train rank).

## Wet_train metrics (Grp1 Max)

| Model | Requested / realised WSE dim | CSI | RMSE (m) | test O2−O1 (m) |
|-------|------------------------------|----:|---------:|---------------:|
| Global native | auto / **1** | 0.9757 | 0.1122 | 0.0640 |
| H-LSG `residual_kmeans` | — / **13** | 0.9757 | **0.0945** | 0.0047 |
| Global `force_n_modes: 13` | 13 / **8** (rank cap) | 0.9750 | 0.2021 | **0.0000** |
| H-LSG `residual_eof_modes: 0` | — / **1** | 0.9757 | 0.1122 | 0.0640 |

## Interpretation

1. Disabling residual modes collapses H-LSG onto the native global baseline (identical CSI/RMSE/O2−O1).
2. Exact equal-dimension matching at 13 is **infeasible** for global-only Max with 8 training events.
3. Maxing global capacity to train rank (8) drives O2−O1 → 0 but **worsens** wet RMSE (0.202 m) relative to both native global and H-LSG.
4. Unlike Chowilla/Burnett, Carlisle Max therefore does **not** show a matched-global win over H-LSG. Residual EC stacking improves depth RMSE here while pure global capacity does not. Report this as **site heterogeneity**, not as a rescue of a general localisation claim: Chowilla/Burnett remain the capacity-controlled anti-cases.

## Related cheap diagnostics (this session)

- Nested CRPS *s* LOO on Carlisle Max: `outputs/evaluation/carlisle/nested_crps_scale_cv.json` — *s*_full = 0.417; fold mean 0.418 ± 0.031 (8 folds).
- Zone spatial coherence: `outputs/evaluation/carlisle/zone_contiguity_diagnostic.json` — mean 8-NN same-zone fraction ≈ 0.952 when XY is included; method still does not enforce contiguity.
