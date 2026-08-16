# Current claims and evidence (repo-relative)

**Instruction to ChatGPT.** For each headline claim, check whether the manuscript wording overreaches the evidence. Flag any claim that (a) implies localisation improves holdout depth skill after capacity matching on Chowilla/Burnett, (b) invents significance tests, or (c) equates our Grp1 single-fold numbers with Fraehr et al. (2024a) pooled Table 2. Do **not** invent new numbers.

**NEGATIVE localisation result (central).** On Chowilla and Burnett, residual hierarchical zoning does **not** survive as a localisation-driven accuracy upgrade once GP-input capacity is matched. Carlisle Max shows site heterogeneity under a Max train-rank cap—not a general rescue of residual localisation.

---

## Claim ledger

### C1 — Multi-fidelity LSG (not zoning) carries primary skill where LF is weak

| Item | Detail |
| --- | --- |
| Manuscript anchors | Abstract; §6.5 Table 2; §7.2 |
| Evidence | `outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_hlsg_max.json`; LF wet_train CSI ≈ 0.853 → LSG ≈ 0.975; RMSE ≈ 0.989 → 0.387 m |
| Also | Chowilla wet_train LF RMSE ≈ 0.690 → LSG ≈ 0.093 m (`.../chowilla/..._hlsg_max.json`) |
| Overreach risk | Claiming zoning caused the CSI lift |

### C2 — Capacity-matched global beats / matches H-LSG truncation story (Chowilla)

| Item | Detail |
| --- | --- |
| Manuscript anchors | Abstract; §6.11 Table 6 |
| Evidence | `docs/paper/04_capacity_controls.md`; `outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_global_matched15_max.json`; H-LSG `..._hlsg_max_capacity_rerun.json`; budget-0 `..._hlsg_budget3_max.json` |
| Numbers (wet_train) | Matched-15 global RMSE **0.085 m**, O2−O1 **0.002 m**; H-LSG RMSE 0.093 m, O2−O1 0.013 m; residual_modes=0 collapses to native global |
| Status | **NEGATIVE for localisation as RMSE/O2−O1 explanation** |

### C3 — Burnett: residual capacity worsens depth RMSE via LF→HF GP map

| Item | Detail |
| --- | --- |
| Manuscript anchors | Abstract; §6.11 Table 7 |
| Evidence | `outputs/evaluation/burnett/workflow_summary_grp1_wse_ext_global_max.json`; `..._hlsg_max.json`; `..._global_matched18_max.json`; `outputs/evaluation/burnett/diagnose_hlsg_o2_vs_rmse.json` |
| Numbers | H-LSG wet RMSE 0.387 m vs global 0.179 m; O4−O2 0.304 vs 0.056 m; EXT agreement identical 0.986; matched-18 global RMSE 0.416 m |
| Status | **NEGATIVE**; extent gate ruled out |

### C4 — Inducing-point and zone-count confounds

| Item | Detail |
| --- | --- |
| Manuscript anchors | §6.11 Table 8 |
| Evidence | `outputs/evaluation/chowilla/workflow_summary_grp1_wse_ext_hlsg_inducing_m{2,8,28}_max.json`; `..._hlsg_nzones{2,6}_max.json` |
| Numbers | m=2 RMSE 0.244 m vs m=16 0.093 m (O2−O1 fixed); n_zones 2→6: O2−O1 shrinks, RMSE worsens 0.087→0.103 m |

### C5 — Carlisle Max equal-capacity is heterogeneous / rank-capped

| Item | Detail |
| --- | --- |
| Manuscript anchors | §6.11 Table 9 |
| Evidence | `docs/paper/05_carlisle_capacity.md`; `outputs/evaluation/carlisle/workflow_summary_grp1_wse_ext_global_max_capacity.json`; `..._global_matched13_max.json`; `..._hlsg_budget1_max.json` |
| Numbers | H-LSG dim 13 RMSE 0.094 m; matched requested-13 realised **8**, RMSE 0.202 m; residual_modes=0 = native global |
| Overreach risk | Calling this a positive proof that residual zoning “works” in general |

### C6 — CRPS-scale calibration helps some cases, null/adverse on Chowilla

| Item | Detail |
| --- | --- |
| Manuscript anchors | Abstract; §6.9 Table 4 |
| Evidence | Carlisle `..._uq_calibrated.json`; Chowilla/Burnett `..._hlsg_max_uq_calibrated.json`; nested CV `outputs/evaluation/{chowilla,carlisle}/nested_crps_scale_cv.json` |
| Numbers | Carlisle Max CRPS 0.039→0.028 at s≈0.417; Chowilla CRPS flat ≈2.155; Burnett 0.133→0.127; nested s stable on Chowilla/Carlisle |
| Overreach risk | Claiming CSI/RMSE “preserved empirically” (they are unchanged **by construction**) |

### C7 — Chowilla all-cells anti-case is protocol sensitivity

| Item | Detail |
| --- | --- |
| Manuscript anchors | §6.7; Table 2 |
| Evidence | Chowilla H-LSG / global summaries: all_cells CSI ≈ 0.390, wet_train CSI ≈ 0.976 |
| Overreach risk | “LSG fails Chowilla” without wet_train |

### C8 — O1–O4 is a path-ordered diagnostic, not additive variance shares

| Item | Detail |
| --- | --- |
| Manuscript anchors | §3.6; §8 Limitations |
| Evidence | Methods text + dual-path budgets in workflow JSON `error_budget` |
| Overreach risk | Language implying unique causal % attribution |

### C9 — Novelty boundary (what we do **not** claim)

| Item | Detail |
| --- | --- |
| Manuscript anchors | §2.4 |
| Evidence | Positioning vs Fraehr 2024a/b; Tan 2025; Wang 2025 REOF–SGP; Wang 2026 future zonal EOF |
| Must remain | Not first localized EOF; not first LSG error split; not first probabilistic flood surrogate; not “zoning improves holdout skill” on Chowilla/Burnett after capacity match |

### C10 — Closed (not open) computational / scope limits

| Item | Detail |
| --- | --- |
| Manuscript anchors | §8; Appendix C |
| Evidence | `docs/paper/03_new_results.md` Gap 5 (Burnett HF stack ≈199 GB vs ≈128 GB RAM) |
| Correct form | Closed Limitations prose; **not** 待补充 TODOs |

---

## Ask ChatGPT

1. Mark each claim **supported / overreaching / ambiguous** relative to the manuscript wording.
2. Propose safer Abstract / Conclusions sentences for C2–C5 that keep the negative result **visible**, not buried.
3. List any manuscript number that appears **without** a matching evidence path above (suspect fabrication or orphan).
