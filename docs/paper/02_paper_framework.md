# Paper framework — methods paper (WRR / JoH / EMS)

**Date:** 2026-08-16  
**nature-writing:** `paper_type=methods`; argument chain = task → limits → method → fair evaluation → reproducibility → boundary.  
**Advisor chat (architecture):** https://chatgpt.com/c/6a812e92-0734-83ea-a86d-da1f7f0b6e49 (web search ON). Literature chat: https://chatgpt.com/c/6a8129c4-e368-83ea-b448-236b427f9ae0.

## Target journal

**Primary:** *Water Resources Research* (methods / applications continuity with Fraehr/Wang LSG series).  
**Alternates:** *Journal of Hydrology* (methods + multi-site diagnostics); *Environmental Modelling & Software* (reproducible surrogate software + diagnostics).

## Title options (bounded claims)

1. Diagnostic hierarchical residual LSG with calibrated GP inundation uncertainty on public multi-fidelity flood benchmarks  
2. Where does spatial localization help LSG? Residual zoning, oracle error budgets, and CRPS-calibrated map uncertainty across Carlisle, Chowilla, and Burnett  
3. From deterministic LSG means to calibrated posterior inundation maps: a multi-site public-data evaluation with staged error attribution

Avoid titles that imply large zoning CSI gains.

## Research questions

1. **RQ1 (skill):** Relative to LF-only and global LSG, how much skill does residual hierarchical LSG add on public Carlisle/Chowilla/Burnett folds under Fraehr-style wet_train scoring?  
2. **RQ2 (attribution):** Using O1–O4 oracles, where is remaining error concentrated (truncation vs LF projection vs GP mapping)?  
3. **RQ3 (UQ):** Does CRPS-scale variance calibration improve probabilistic scores without changing CSI/RMSE?  
4. **RQ4 (boundary):** When does strong LF extent create an all-cells anti-case (Chowilla), and how should protocols be reported?

## Defensible novelty statement (use this)

We implement and evaluate a residual hierarchical LSG variant (global modes + residual zonal EOFs on WSE; global EXT), with Sparse-GP posterior propagation to inundation fields, CRPS-based variance calibration, and a staged O1–O4 oracle attribution, on three public multi-fidelity cases. We show that multi-fidelity LSG remains the dominant skill source, while residual zoning mainly reduces truncation gaps (O2−O1) and UQ calibration improves probabilistic reliability—especially where uncalibrated intervals are over-dispersed.

**Boundary:** Not “first localized EOF”; not “first LSG error decomposition” (Tan 2025); not “zoning always improves CSI”.

## Exemplar papers to imitate (structure)

| Exemplar | DOI | Why imitate | Verification |
|---|---|---|---|
| **Karimi et al. 2022 WRR** (advisor pick #1) | [10.1029/2021WR031249](https://doi.org/10.1029/2021WR031249) | Diagnostic framework as the contribution; multiple objectives; experiment-first Methods | DOI resolves (AGU) |
| **Sarrazin et al. 2016 EMS** (advisor pick) | [10.1016/j.envsoft.2016.02.005](https://doi.org/10.1016/j.envsoft.2016.02.005) | Methodological value from case-dependent behavior; evaluation procedure validated, not universal win | verified |
| **Siripatana et al. 2025 WRR** (advisor UQ structure) | [10.1029/2024WR039668](https://doi.org/10.1029/2024WR039668) | Separates surrogate construction from UQ characterization; explicit limitations | verified earlier |
| Fraehr et al. 2022 WRR | 10.1029/2022WR032248 | Domain-native LSG methods arc / protocol language | verified |
| Fraehr et al. 2024 Water Research | 10.1016/j.watres.2024.121202 | Multi-site comparison tables | verified |
| Wang et al. 2026 WRR | 10.1029/2025WR042481 | LSG-TS vs Max; zonal EOF future-work hook | verified |

**Advisor narrative ranking (accepted):** (1) diagnostic/evaluation framework → (2) public multi-site reproduction + falsification → (3) probabilistic calibration → (4) residual zoning as refinement. Do **not** lead with zoning.

## Section-by-section outline

1. **Introduction** — Need for fast inundation maps; LSG lineage; gap = diagnostics + calibrated uncertainty + explicit residual localization (Wang 2026 future work), not a new LF→HF idea.  
2. **Related work** — LSG series; REOF-SGP; Tan regionalized LSG; probabilistic flood surrogates; SFINCS–LSG. Novelty table.  
3. **Methods**  
   - 3.1 Dual-field `wse_ext` reconstruction  
   - 3.2 Residual hierarchical zoning (`residual_kmeans`)  
   - 3.3 SGPR with inducing floor (document Max-path failure mode)  
   - 3.4 Posterior depth variance + CRPS-scale calibration  
   - 3.5 O1–O4 oracle definitions  
4. **Data and experimental design** — Carlisle / Chowilla / Burnett public cubes; Grp1 folds; wet_train vs all_cells; configs in repo.  
5. **Results**  
   - 5.1 Point skill vs LF and published LSG (tables from JSON)  
   - 5.2 Global vs H-LSG (O2−O1 emphasis)  
   - 5.3 UQ calibration (CRPS, active coverage, `var_scale`)  
   - 5.4 Chowilla anti-case protocol analysis  
6. **Discussion** — Modest zoning gains; when localization helps; reviewer risks (Tan/Wang REOF); open memory limits for full-TS.  
7. **Conclusions** — Bounded contribution; reproducibility.  
8. **Data/code availability** — Figshare DOIs; this repo’s configs/scripts (no secrets).

## Figure / table list (intended names; figures regenerating elsewhere)

Do **not** claim figure files verified here.

| ID | Content | Artifact source |
|---|---|---|
| Fig. 1 | Method schematic: LF→EOF/GP→depth; residual zones on WSE | conceptual |
| Fig. 2 | Carlisle Grp1 maps: LF / LSG-TS / LSG-Max / HF | `outputs/evaluation/carlisle/*sgpr_fix*` |
| Fig. 3 | O1–O4 ladder bars (Carlisle Max/TS; Chowilla; Burnett) | `error_budget` JSON |
| Fig. 4 | Global vs H-LSG O2−O1 (Chowilla) | hlsg vs global summaries |
| Fig. 5 | UQ: CRPS / coverage_active before–after calibration | `*_uq_calibrated.json` |
| Fig. 6 | Chowilla all-cells vs wet_train CSI contrast | Chowilla score_protocol |
| Table 1 | Case/data inventory | `data/DATA_INVENTORY.md` |
| Table 2 | Headline CSI/RMSE three cases | progress review metrics |
| Table 3 | Novelty triage | `01_literature_review.md` |
| Table 4 | UQ `var_scale` summary | calibrated JSON |

## Framing modest method gains (explicit guidance)

Lead with **diagnostic insight**, not CSI deltas from zoning:

1. Show LSG vs LF first (large, defensible lifts where LF is weak; depth RMSE on Chowilla wet_train).  
2. Present zoning as an ablation that mainly closes truncation (O2−O1), sometimes with flat CSI.  
3. Treat Chowilla all-cells CSI collapse as a **protocol/anti-case** result, not a silent failure.  
4. Put UQ calibration and O1–O4 as first-class Results subsections.  
5. In Discussion, compare to Tan (regionalize + 2-way split) and Rukai Wang (REOF-SGP) with a difference table.

## Reviewer-risk and rebuttal plan

| Risk | Rebuttal |
|---|---|
| “Zonal EOF already suggested / done” | Cite Wang 2026 as future work; distinguish residual hierarchical simultaneous zones from REOF and Tan’s single-focus retraining |
| “Error decomposition already in Tan 2025” | Agree two-component split exists; claim staged O1–O4 counterfactual ladder + multi-site public evaluation |
| “UQ not new” | Bound claim to calibrated LSG posterior maps + CRPS-scale; cite prior probabilistic surrogates as related |
| “Zoning gains tiny → reject” | Paper is diagnostic; modest gain is a result, not a bug |
| “Chowilla CSI 0.39” | Report wet_train protocol; explain EXT train-mask / all-cells mismatch |
| “SGPR floor is engineering trivia” | Show Max O4 regression without floor; keep as Methods robustness, not headline novelty |
| “Not enough sites / full-TS missing” | State 未运行 items; public max-surface folds already cover three hydro settings |

## Terminology ledger (canonical)

LSG; LSG-TS; LSG-Max; LF; HF; EOF; EC; EXT; WSE; H-LSG; residual_kmeans; SGPR; CRPS; CSI; POD; RFA; O1–O4; wet_train; all_cells; `var_scale`.
