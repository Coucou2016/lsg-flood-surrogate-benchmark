# Paper framework — methods paper (WRR / JoH / EMS)

**Date:** 2026-08-16  
**nature-writing:** `paper_type=methods`; argument chain = task → limits → method → fair evaluation → reproducibility → boundary.  
**Advisor chat (architecture):** https://chatgpt.com/c/6a812e92-0734-83ea-a86d-da1f7f0b6e49 (web search ON). Literature chat: https://chatgpt.com/c/6a8129c4-e368-83ea-b448-236b427f9ae0.

## Target journal

**Primary:** *Water Resources Research* (methods / applications continuity with Fraehr/Wang LSG series).  
**Alternates:** *Journal of Hydrology* (methods + multi-site diagnostics); *Environmental Modelling & Software* (reproducible surrogate software + diagnostics).

## Title options (bounded claims)

1. Does residual hierarchical zoning improve multi-fidelity flood surrogates? A capacity-controlled negative result with oracle error budgets and CRPS-calibrated inundation uncertainty on public benchmarks  
2. Capacity confounds localization in multi-fidelity LSG: oracle error budgets and CRPS-calibrated map uncertainty across Carlisle, Chowilla, and Burnett  
3. From deterministic LSG means to calibrated posterior inundation maps: a multi-site public-data evaluation with staged error attribution and a matched-capacity localization control

Avoid titles that imply zoning CSI/RMSE gains; the localization result is negative under matched capacity.

## Research questions

1. **RQ1 (capacity-controlled localization):** Once the GP input dimension is held fixed (via `force_n_modes`, inducing-point and zone-count sweeps), does the apparent residual-zoning advantage in the truncation gap (O2−O1) survive—and does it translate into held-out depth skill? *(Answer: no.)*  
2. **RQ2 (attribution):** Using O1–O4 oracles, where is remaining error concentrated (truncation vs LF projection vs GP mapping)?  
3. **RQ3 (UQ):** Does CRPS-scale variance calibration improve probabilistic scores without changing CSI/RMSE?  
4. **RQ4 (boundary):** When does strong LF extent create an all-cells anti-case (Chowilla), and how should protocols be reported?

## Defensible novelty statement (use this)

We evaluate a residual hierarchical LSG variant (global modes + residual zonal EOFs on WSE; global EXT) against **matched-capacity controls** on three public multi-fidelity cases, together with Sparse-GP posterior propagation to inundation fields, CRPS-based variance calibration, and a staged O1–O4 oracle attribution. The central localization result is **negative**: once the GP input dimension is matched (`force_n_modes`), a global model reproduces (Burnett) or exceeds (Chowilla) H-LSG's O2−O1 reduction, the matched global attains the best wet RMSE on Chowilla, and on Burnett extra residual capacity worsens depth RMSE through a degraded LF→HF GP map (identical extent gate); inducing-point budget and zone count move RMSE more than zoning does. What stands is the defensible core: multi-fidelity LSG is the dominant skill source, the O1–O4 ladder localizes error, CRPS calibration improves reliability without changing CSI/RMSE, and residual hierarchical zoning is best used as a **truncation diagnostic**, not an accuracy upgrade—delivered as a reproducible open benchmark with an honest negative localization result.

**Boundary:** Not “first localized EOF”; not “first LSG error decomposition” (Tan 2025); not “zoning improves CSI/RMSE”; not “localization survives capacity matching”.

## Exemplar papers to imitate (structure)

| Exemplar | DOI | Why imitate | Verification |
|---|---|---|---|
| **Karimi et al. 2022 WRR** (advisor pick #1) | [10.1029/2021WR031249](https://doi.org/10.1029/2021WR031249) | Diagnostic framework as the contribution; multiple objectives; experiment-first Methods | DOI resolves (AGU) |
| **Sarrazin et al. 2016 EMS** (advisor pick) | [10.1016/j.envsoft.2016.02.005](https://doi.org/10.1016/j.envsoft.2016.02.005) | Methodological value from case-dependent behavior; evaluation procedure validated, not universal win | verified |
| **Siripatana et al. 2025 WRR** (advisor UQ structure) | [10.1029/2024WR039668](https://doi.org/10.1029/2024WR039668) | Separates surrogate construction from UQ characterization; explicit limitations | verified earlier |
| Fraehr et al. 2022 WRR | 10.1029/2022WR032248 | Domain-native LSG methods arc / protocol language | verified |
| Fraehr et al. 2024 Water Research | 10.1016/j.watres.2024.121202 | Multi-site comparison tables | verified |
| Wang et al. 2026 WRR | 10.1029/2025WR042481 | LSG-TS vs Max; zonal EOF future-work hook | verified |

**Advisor narrative ranking (accepted):** (1) diagnostic/evaluation framework → (2) public multi-site reproduction + **capacity-controlled falsification of localization** → (3) probabilistic calibration → (4) residual zoning demoted to a truncation diagnostic. Do **not** lead with zoning; lead with the diagnostics package and the negative result.

## Section-by-section outline

1. **Introduction** — Need for fast inundation maps; LSG lineage; gap = diagnostics + calibrated uncertainty + a **capacity-controlled test** of residual localization (Wang 2026 future work), not a new LF→HF idea.  
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
   - 5.2 Global vs H-LSG at native capacity (O2−O1 emphasis, sets up the confound)  
   - 5.3 **Capacity-matched controls (RQ1): the localization claim does not survive** (Tables 6–8: matched-15/18, inducing sweep, zone sweep, CRPS nested CV)  
   - 5.4 UQ calibration (CRPS, active coverage, `var_scale`)  
   - 5.5 Chowilla anti-case protocol analysis  
6. **Discussion** — Capacity-confounded zoning (negative result); skill lives in the multi-fidelity map; Burnett GP-map failure (O4−O2, identical EXT gate); reviewer risks (Tan/Wang REOF); open memory limits for full-TS.  
7. **Conclusions** — Bounded contribution; reproducibility.  
8. **Data/code availability** — Figshare DOIs; this repo’s configs/scripts (no secrets).

## Figure / table list (intended names; figures regenerated 2026-08-16)

Verified via `outputs/figures/figure_manifest.json` (`skips=[]`).

| ID | Content | Artifact source |
|---|---|---|
| Fig. 1 | Cross-case wet_train CSI/RMSE | workflow summaries |
| Fig. 2 | O1–O4 ladders | `error_budget` JSON |
| Fig. 3 | Global vs H-LSG (Chowilla **+ Burnett**) | hlsg + global summaries |
| Fig. 4 | UQ CRPS before–after (three cases) | `*_uq_calibrated.json` |
| Fig. 5 | Spatial maps + **P(wet)** | `pred_examples.npz` |
| Fig. 6 | Chowilla wet_correlation zoning A/B | wet_correlation summary |
| Table 1–5 | Inventory / CSI / O1–O4 / UQ / zoning | manuscript |

## Framing modest method gains (explicit guidance)

Lead with **diagnostic insight and the negative result**, not CSI deltas from zoning:

1. Show LSG vs LF first (large, defensible lifts where LF is weak; depth RMSE on Chowilla wet_train).  
2. Present zoning's native-capacity O2−O1 shrinkage, then **immediately** show the matched-capacity controls that reproduce/exceed it with a global model — zoning is a capacity/approximation confound, not localization.  
3. Treat Chowilla all-cells CSI collapse as a **protocol/anti-case** result, not a silent failure.  
4. Put UQ calibration and O1–O4 as first-class Results subsections.  
5. In Discussion, compare to Tan (regionalize + 2-way split) and Rukai Wang (REOF-SGP), and argue future localized-EOF surrogates must report matched-capacity baselines.

## Reviewer-risk and rebuttal plan

| Risk | Rebuttal |
|---|---|
| “Zonal EOF already suggested / done” | Cite Wang 2026 as future work; distinguish residual hierarchical simultaneous zones from REOF and Tan’s single-focus retraining |
| “Error decomposition already in Tan 2025” | Agree two-component split exists; claim staged O1–O4 counterfactual ladder + multi-site public evaluation |
| “UQ not new” | Bound claim to calibrated LSG posterior maps + CRPS-scale; cite prior probabilistic surrogates as related |
| “Zoning gains tiny → reject” | Paper is diagnostic; the capacity-controlled **negative** localization result is itself the contribution, not a bug |
| “Zoning O2−O1 win is just capacity” | Agreed — we prove it with `force_n_modes` matched controls + inducing/zone sweeps; that falsification is the point |
| “Chowilla CSI 0.39” | Report wet_train protocol; explain EXT train-mask / all-cells mismatch |
| “SGPR floor is engineering trivia” | Show Max O4 regression without floor; keep as Methods robustness, not headline novelty |
| “Not enough sites / full-TS missing” | State 未运行 items; public max-surface folds already cover three hydro settings |

## Terminology ledger (canonical)

LSG; LSG-TS; LSG-Max; LF; HF; EOF; EC; EXT; WSE; H-LSG; residual_kmeans; SGPR; CRPS; CSI; POD; RFA; O1–O4; wet_train; all_cells; `var_scale`.
