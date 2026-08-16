# Where does spatial localization help LSG? Residual hierarchical zoning, oracle error budgets, and CRPS-calibrated inundation uncertainty on public multi-fidelity flood benchmarks

**Authors:** 待补充  
**Affiliations:** 待补充  
**Corresponding author:** 待补充  
**Target venues:** *Water Resources Research* / *Journal of Hydrology* / *Environmental Modelling & Software* (methods paper)

---

## Abstract

Fast, spatially resolved flood inundation maps remain difficult to produce at high-fidelity hydrodynamic resolution. Multi-fidelity Low-fidelity–Spatial analysis–Gaussian Process Learning (LSG) maps low-fidelity (LF) inundation fields onto high-fidelity (HF) Empirical Orthogonal Function (EOF) modes with Sparse Gaussian Process Regression (SGPR), yet operational use still lacks (i) simultaneous residual hierarchical localization, (ii) staged attribution of remaining error, and (iii) calibrated probabilistic map products. Here we implement and evaluate a Fraehr-compatible extent plus water-surface elevation (EXT+WSE) LSG stack with residual hierarchical zoning (H-LSG), an O1–O4 oracle error ladder, and Continuous Ranked Probability Score (CRPS)–scale variance calibration that propagates GP posterior variance to depth and inundation outputs. We evaluate the stack on three public Figshare cases (Carlisle, Chowilla, Burnett) under Fraehr-style leave-one-group-out Grp1 folds. Multi-fidelity LSG remains the dominant skill source: Burnett wet_train Critical Success Index (CSI) rises from 0.853 (LF only) to 0.975 (LSG-Max H-LSG), and Carlisle LSG-Max wet_train CSI reaches 0.976 with root-mean-square error (RMSE) 0.094 m. Residual zoning mainly shrinks the truncation gap O2−O1 (for example Chowilla Max: 0.057 global versus 0.013 H-LSG) rather than delivering large CSI gains versus a global EOF baseline. Chowilla is a strong-LF anti-case under all-cell scoring (LSG-Max CSI 0.390) while wet_train CSI remains 0.976, so scoring protocol must be reported explicitly. On Carlisle Max, CRPS-scale calibration sets variance scale *s* = 0.417, reducing CRPS from 0.039 to 0.028 without changing CSI or RMSE. The contribution is therefore diagnostic and probabilistic: a reproducible public-data methods package that clarifies when localization helps, where multi-fidelity LSG carries the skill, and how to publish calibrated inundation uncertainty.

**Keywords:** multi-fidelity surrogate; flood inundation; LSG; hierarchical EOF; Gaussian process; uncertainty quantification; error budget; Critical Success Index

---

## 1. Introduction

Flood inundation forecasting and scenario assessment require maps that resolve channels, floodplains, and temporary wet cells at resolutions that full hydrodynamic solvers can deliver only at high cost. Surrogate models trained on paired LF and HF inundation fields offer a route to near-instant prediction once HF training events exist, without re-running the HF solver for every new boundary condition.

LSG couples an LF hydrodynamic field to an HF EOF basis through SGPR on expansion coefficients (ECs), recovering HF-like depth or water-surface maps from cheap LF runs (Fraehr et al., 2022, 2023). Subsequent work compared LSG with machine-learning surrogates on public Carlisle, Chowilla, and Burnett cubes (Fraehr et al., 2024) and examined strategies for large floodplain applications, including LSG time-series (LSG-TS) versus maximum-surface (LSG-Max) training (Wang et al., 2026). Wang et al. (2026) explicitly name zonal EOF analysis as future work rather than a completed component of that study.

Three practical gaps remain for methods-oriented reuse. First, spatial localization of EOF energy has been pursued in adjacent lines—rotated EOF with Sparse GP (REOF–SGP; Wang et al., 2025), regionalized LSG focus subdomains (Tan et al., 2025), and satellite REOF forecasting (FIER and watershed mosaicking; Chang et al., 2020, 2023; Markert et al., 2026)—but a simultaneous whole-domain residual hierarchical decomposition (global modes plus residual zonal EOFs) for multi-fidelity hydrodynamic LSG is not established as a tested public-data protocol. Second, error attribution in LSG is often summarized by end-to-end CSI/RMSE; Tan et al. (2025) introduce a two-part split, yet a staged counterfactual ladder that isolates truncation, LF expressibility, and GP mapping on the same dual EXT+WSE path is still needed for diagnosis. Third, probabilistic flood surrogates exist outside LSG (Donnelly et al., 2022; López-Lopera et al., 2022; Kohanpur et al., 2023; Siripatana et al., 2025; Zanchetta and Coulibaly, 2022), but calibrated propagation of LSG GP posteriors to inundation probability and depth CRPS, with an explicit variance scale that leaves point CSI/RMSE unchanged, remains underexplored.

This paper therefore frames residual hierarchical LSG not as a universal CSI booster but as a diagnostic and probabilistic methods contribution. We ask four research questions. **RQ1:** Relative to LF-only and global LSG, how much wet_train skill does residual H-LSG add on public Grp1 folds? **RQ2:** Using O1–O4 oracles, where is remaining depth error concentrated? **RQ3:** Does CRPS-scale variance calibration improve probabilistic scores without changing CSI/RMSE? **RQ4:** When does strong LF extent create an all-cells anti-case, and how should protocols be reported?

We implement Fraehr-compatible EXT+WSE reconstruction, residual_kmeans H-LSG on the WSE branch, an SGPR inducing-point floor required for stable Max-path mapping, O1–O4 dual-path budgets, and CRPS-scale uncertainty calibration. Evaluation uses the three public Fraehr (2024) cases. Headline results show that multi-fidelity LSG carries the primary skill lift where LF is weak, residual zoning mainly reduces O2−O1, and Chowilla all-cell CSI collapse is a protocol anti-case rather than a silent failure.

---

## 2. Related work and novelty boundary

### 2.1 Multi-fidelity LSG lineage

Fraehr et al. (2022) introduced LSG for upskilling LF hydrodynamic flood models via EOF compression and Sparse GPs. Fraehr et al. (2023) developed hybrid floodplain formulations separating extent-like and water-surface information. Nature Water commentary framed LSG as a route to “supercharging” inundation models (Fraehr et al., 2023b). Fraehr et al. (2024) released multi-site comparisons and public cubes used here. Wang et al. (2026) extended LSG strategies for large complex floodplains and retained zonal EOF as future work. Lu et al. (2025) studied GP kernel choice within LSG. Public data and companion code are deposited at Figshare DOI 10.26188/24312658 (Fraehr, 2024).

### 2.2 Localization and regionalization near LSG

Tan et al. (2025) regionalize LSG training on focus subdomains and report a two-component error decomposition (downscaling versus LSG mapping). Wang et al. (2025) combine rotated EOF with Sparse GP for LF→HF hydrodynamic mapping. Satellite FIER and watershed-mosaic REOF systems partition space for extent forecasting (Chang et al., 2020, 2023; Wan et al., 2025; Markert et al., 2026). SFINCS–LSG abstracts discuss EOF compression in compound coastal settings (Eilander et al., 2025, 2026). These works constrain novelty: this paper does **not** claim the first localized EOF flood model, the first LSG error split, or the first probabilistic flood surrogate.

### 2.3 Probabilistic inundation surrogates

Gaussian-process and related probabilistic emulators for flood depth or coastal inundation appear in Donnelly et al. (2022), López-Lopera et al. (2022), Kohanpur et al. (2023), Siripatana et al. (2025), and Zanchetta and Coulibaly (2022). Our claim is narrower: CRPS-calibrated LSG GP posterior variance propagated to dual-field depth maps and inundation probabilities on public multi-fidelity LSG cases.

### 2.4 Defensible novelty statement

We implement and evaluate residual hierarchical LSG (global modes plus residual zonal EOFs on WSE; global EXT), Sparse-GP posterior propagation to inundation fields, CRPS-based variance calibration, and a staged O1–O4 oracle attribution on three public multi-fidelity cases. Multi-fidelity LSG remains the dominant skill source; residual zoning mainly reduces held-out subspace-expressibility gaps (O2−O1); UQ calibration improves probabilistic reliability where uncalibrated intervals are over-dispersed. We reject claims that zoning universally boosts CSI.

---

## 3. Methods

### 3.1 Problem formulation

Let **h**<sup>HF</sup> ∈ ℝ<sup>*n*</sup> and **h**<sup>LF→HF</sup> ∈ ℝ<sup>*n*</sup> denote HF depth and LF depth interpolated to the HF mesh for one event (or timestep). Wet cells are those with depth ≥ τ, with τ = 0.03 m throughout. Always-flooded (AF) and temporary-flooded (TF) masks follow Fraehr-style cell categories. The surrogate learns a map from LF fields to HF-like depth without calling the HF solver at prediction time.

### 3.2 Dual-field EXT+WSE reconstruction

Following Fraehr et al. (2023), the operational field mode `wse_ext` fits two emulators:

1. **EXT** — binary wet/dry on TF cells (AF forced wet), reconstructed by EOF+GP.  
2. **WSE** — water-surface elevation on wet cells, reconstructed by EOF+GP.

Combination into depth uses terrain elevation *Z*:

> **WSE′** = WSE if EXT = 1; **WSE′** = *Z* if EXT = 0;  
> *h* = max(WSE′ − *Z*, 0),

with depths below τ set to dry. This is **not** an LF-extent post-gate on a depth-only prediction; EXT is learned jointly with WSE.

### 3.3 Global LSG and residual hierarchical LSG (H-LSG)

**Global path.** HF training fields on the retained wet index are compressed by EOF. LF fields projected onto HF modes yield pseudo-ECs. One SGPR per mode maps LF pseudo-ECs to HF ECs. Reconstruction inverts the EOF expansion (plus Tobit-style thresholding for operational maps).

**Residual hierarchical path.** Hard partitions of the full water surface create boundary jumps. H-LSG keeps basin-scale global modes and lets zones model residuals only:

> **h** = Φ<sub>global</sub> **c**<sub>global</sub> + Σ<sub>*z*</sub> **1**<sub>*z*</sub> Φ<sub>*z*</sub><sup>res</sup> **c**<sub>*z*</sub>.

Zone labels use `residual_kmeans` on per-cell residual magnitude (optional XY). Residual ECs stack into the same LF→HF GP as global ECs. Under `wse_ext`, residual zones attach to the **WSE** branch only; binary EXT remains global so zone labels do not fragment the extent field.

### 3.4 Sparse GP regression and inducing-point floor

Each mode uses SGPR (GPflow) or a NumPy RBF GP fallback. For LSG-Max, *n*<sub>train</sub> can be small (Carlisle Grp1: 8 events). An inducing fraction of 0.02 then collapses to two inducing points on a per-column linspace diagonal. With H-LSG the GP input dimension grows (global + residual ECs), so a rank-2 diagonal inducing set cannot represent the LF→HF map and Max-path O4/RMSE regress. The implementation initializes inducing points from training rows and floors the budget at `lsg.min_inducing_points` (capped at *n*<sub>train</sub>). This is treated as a robustness requirement, not a novelty claim.

### 3.5 Posterior variance, inundation probability, and CRPS-scale calibration

GP predictive variance on ECs is mapped through the linear EOF reconstruction and inflated by a cell-wise residual/truncation term, yielding latent depth *Z* ∼ 𝒩(μ, σ²). Observation uses Type-I left censoring (Tobit):

> *h* = 0 if *Z* < τ; *h* = *Z* if *Z* ≥ τ.

Inundation probability is

> *P*(*h* ≥ τ) = *P*(*Z* ≥ τ) = 1 − Φ((τ − μ) / σ).

Uncalibrated intervals can be over-dispersed (Carlisle Max `coverage_90` ≈ 0.996). A single global scale is fit on train by minimising mean Gaussian CRPS:

> Var<sub>cal</sub> = *s* · Var<sub>raw</sub>,

with latent mean unchanged. Unchanged CSI/RMSE after calibration is therefore **by construction** (mean maps are untouched), not an independent empirical finding that calibration “preserves accuracy.” The scientific claim is improved probabilistic scores (CRPS, coverage) on held-out scoring of variance-rescaled maps, with *s* fit on **training** events only. We also report `coverage_*_active` on cells where observation or predictive mean ≥ τ, because all-cell coverage is inflated by EXT-dry zeros with near-zero σ. Under `wse_ext`, EXT remains a learned binary/extent field that gates continuous WSE; scalar *s* primarily recalibrates continuous depth variance on that gated path rather than a fully free inundation-probability model. Nested event-level CV for *s* is **未运行 / 待补充**.

Closed-form Gaussian CRPS follows Gneiting and Raftery (2007):

> CRPS(*N*(μ, σ²), *y*) = σ [ *z* (2Φ(*z*) − 1) + 2φ(*z*) − 1/√π ], *z* = (*y* − μ) / σ.

### 3.6 O1–O4 oracle error ladder

On the dual EXT+WSE path, matched oracles are combined with production gating into clipped depth RMSE on the protocol wet index. Because EXT gating, WSE reconstruction, clipping, and GP mapping are nonlinear, these stages are a **counterfactual attribution ladder**, not an additive variance decomposition with unique shares of total error. Differences such as O2−O1 should be read as path-ordered contrasts under the fixed production combination rule.

| Stage | Inputs | Interpretation |
|-------|--------|----------------|
| **O1** | HF true ECs, full training-rank modes | Numerical SVD floor |
| **O2** | HF true ECs, truncated to \(k\) modes | EOF truncation / out-of-subspace expressibility |
| **O3** | LF pseudo-ECs, no GP | LF expressibility in the HF subspace |
| **O4** | Full LSG (GP + \(k\) modes) | Total surrogate error (mirrors `predict_dual_depth`) |

The gap O2−O1 isolates truncation (or held-out out-of-subspace energy). O3−O2 isolates LF projection limits. O4−O3 isolates GP mapping. Train and test budgets are reported separately: for LSG-Max with full-rank training (Wang et al., 2026 retained 47 ECs for 47 events), in-sample O2−O1 can be near zero while test O2−O1 remains informative. Oracle-order factorial swaps are **未运行 / 待补充**.

### 3.7 Metrics and scoring masks

Binary inundation metrics use τ = 0.03 m: Probability of Detection (POD), Rate of False Alarms (RFA), and CSI. Depth skill uses RMSE (m). **all_cells** scores the full HF mesh; **wet_train** scores Fraehr category wet indices used in training. We distinguish **time-series** scores (`ts_*` for LSG-TS over timesteps) from **max-surface** scores (event maximum depth). Unless noted, headline CSI/RMSE for LSG-Max and for LSG-TS “max surface” refer to maximum inundation surfaces. Probabilistic scores include CRPS, Brier score, PIT mean on wet cells, and coverage at 50%/90%.

### 3.8 Statistical reporting note

This study evaluates deterministic and probabilistic scores on fixed published event splits (Grp1), not biological replicates. The independent evaluation unit is the **hold-out event** (or event set) under each case’s Fraehr/Wang-style split protocol—not the raster cell. We report effect sizes (CSI, RMSE, CRPS, O1–O4 RMSE) without inventing \(p\)-values. Cell counts enter contingency tables but are not treated as independent experimental replicates for inferential tests.

**Hold-out sizes for headline Max summaries (from workflow JSON `error_budget` test `n_samples`):** Carlisle Grp1 Max test *N*<sub>event</sub> = 1 (E1); Chowilla Grp1 Max test *N*<sub>event</sub> = 1 (E1); Burnett Grp1 Max test *N*<sub>event</sub> = 18. Carlisle LSG-TS reports many timesteps on the held-out event, but Max-surface skill for Carlisle/Chowilla remains a single-event contrast under Grp1 and must not be over-generalised. Software: Python stack in the project virtual environment; GPflow/TensorFlow optional for SGPR (待补充: exact package versions in a reproducibility table).

**Emulation target.** Metrics compare surrogate maps to **HF hydrodynamic fields** (perfect-prognosis style), not to independent remote-sensing flood observations.

---

## 4. Public datasets and case studies

Public multi-fidelity cubes are from Fraehr (2024), DOI [10.26188/24312658](https://doi.org/10.26188/24312658) (CC BY 4.0). Solver brand is irrelevant to LSG; paired HF/LF fields are ingested without re-running hydrodynamics.

**Table 1. Case inventory (public benchmarks used in this study).**

| Case | HF / LF solvers | HF scale (order) | Events / Grp1 split used | Time reduction | Config |
|------|-----------------|------------------|--------------------------|----------------|--------|
| Carlisle (primary) | LISFLOOD-FP × HEC-RAS | ~5.8×10⁵ cells | E1–E9; train E2–E9, test E1 | Full TS + Max | `config/carlisle.yaml` |
| Chowilla (secondary) | fine/coarse HEC-RAS | ~1.1×10⁵ cells | 29 events; train 28, test E1 | Max surfaces | `config/chowilla.yaml` |
| Burnett (tertiary) | TUFLOW × HEC-RAS | ~7.8×10⁵ cells | 74 events; train 56, test 18 | Max surfaces | `config/burnett.yaml` |

Chowilla and Burnett full time-series Grp1 folds are memory-limited and marked **未运行 / 待补充** as headline TS results. Brisbane TUFLOW/URBS (Wang et al., 2026) is licence-gated and not used as a public result here (**待补充 / 未运行** as appendix). FloodCastBench is deferred (**未运行**).

---

## 5. Experimental design

1. **Field mode:** `lsg.field: wse_ext` for all headline runs.  
2. **Zoning:** H-LSG `residual_kmeans` (default); global A/B with `zoning: none` on Chowilla and Burnett (`config/chowilla.yaml` twin / `config/burnett_global.yaml`); Chowilla `wet_correlation` sensitivity (`config/chowilla_wet_correlation.yaml`).  
3. **Folds:** Fraehr ValidateOnGrp_1 / Wang-style `splits.yaml` protocol as recorded in workflow summaries (`split_protocol`).  
4. **Baselines:** LF only (WSE→DEM clip on HF mesh); global LSG where available; H-LSG after SGPR inducing floor.  
5. **Diagnostics:** `evaluation.error_budget` (O1–O4); `evaluation.uq` with `uq_calibration: crps_scale` (Carlisle workflow + Chowilla/Burnett rescore from saved states).  
6. **Artifacts:** metrics from `outputs/evaluation/{carlisle,chowilla,burnett}/*.json`; figures from `outputs/figures/` (SciencePlots; Times New Roman; `figure_manifest.json` skips empty).

Primary JSON sources:

- Carlisle: `workflow_summary_full_Grp1_wse_ext_hlsg_sgpr_fix.json` and `..._uq_calibrated.json`  
- Chowilla H-LSG: `workflow_summary_grp1_wse_ext_hlsg_max.json` (+ `..._uq_calibrated.json`)  
- Chowilla global: `workflow_summary_grp1_wse_ext_global_max.json`  
- Chowilla `wet_correlation`: `workflow_summary_grp1_wse_ext_wet_correlation_max.json`  
- Burnett H-LSG: `workflow_summary_grp1_wse_ext_hlsg_max.json` (+ `..._uq_calibrated.json`)  
- Burnett global: `workflow_summary_grp1_wse_ext_global_max.json`

---

## 6. Results

### 6.1 Point skill across cases (wet_train and all_cells)

**Table 2. Headline CSI and RMSE on Grp1 folds (threshold 0.03 m).** Values rounded from workflow JSON; wet_train is the Fraehr-style protocol mask.

| Case | Model | CSI all_cells | CSI wet_train | RMSE all (m) | RMSE wet_train (m) |
|------|-------|--------------:|--------------:|-------------:|-------------------:|
| Carlisle | LF only | 0.960 | 0.966 | 0.074 | 0.101 |
| Carlisle | LSG-TS (max surface) | 0.970 | 0.970 | 0.099 | 0.154 |
| Carlisle | LSG-Max H-LSG | 0.976 | 0.976 | 0.061 | 0.094 |
| Chowilla | LF only | 0.930 | 0.925 | 0.690 | 0.690 |
| Chowilla | LSG-Max H-LSG | 0.390 | 0.976 | 3.789 | 0.093 |
| Chowilla | LSG-Max global | 0.390 | 0.974 | 3.789 | 0.088 |
| Burnett | LF only | 0.853 | 0.853 | 0.983 | 0.989 |
| Burnett | LSG-Max H-LSG | 0.975 | 0.975 | 0.384 | 0.387 |
| Burnett | LSG-Max global | 0.975 | 0.975 | 0.179 | 0.179 |

**Figure 1** (`fig01_cross_case_csi_rmse_wet_train`) summarises wet_train CSI and RMSE across cases. Burnett shows a clear multi-fidelity lift (CSI 0.853→0.975; RMSE 0.989→0.387 m). Carlisle already has strong LF extent (CSI 0.966 wet_train); LSG-Max still improves CSI to 0.976 and cuts wet_train RMSE from 0.101 m to 0.094 m. Chowilla wet_train LSG-Max CSI (0.976) exceeds LF (0.925) and collapses depth RMSE from 0.690 m to 0.093 m, even though all-cell CSI collapses (Section 6.4).

For Carlisle LSG-TS, **time-series** scores on the held-out event are CSI 0.959 and RMSE 0.065 m (`ts_*`), while the **max surface** derived from the TS model matches Table 2 (CSI 0.970; RMSE 0.099 m all_cells). These quantities must not be conflated.

### 6.2 O1–O4 error budgets

**Table 3. Test-split dual-path O1–O4 depth RMSE (m) on protocol wet index.**

| Case | Variant | O1 | O2 | O3 | O4 | O2−O1 |
|------|---------|---:|---:|---:|---:|------:|
| Carlisle | LSG-TS H-LSG | 0.018 | 0.033 | 0.240 | 0.102 | 0.015 |
| Carlisle | LSG-Max H-LSG | 0.048 | 0.052 | 0.068 | 0.094 | 0.005 |
| Chowilla | LSG-Max H-LSG | 0.020 | 0.034 | 0.701 | 0.093 | 0.013 |
| Chowilla | LSG-Max global | 0.020 | 0.078 | 0.666 | 0.088 | 0.057 |
| Burnett | LSG-Max H-LSG | 0.074 | 0.083 | 0.668 | 0.387 | 0.009 |
| Burnett | LSG-Max global | 0.074 | 0.123 | 0.708 | 0.179 | 0.049 |

**Figure 2** (`fig02_error_budget_o1o4`) shows the ladder structure. On Carlisle Max, O3 and O4 remain close (0.068 vs 0.094 m), indicating that after truncation the GP mapping is not the dominant failure. On Chowilla and Burnett Max, O3 is large (≈0.67–0.70 m) relative to O2, so LF expressibility in the HF subspace dominates before GP mapping; O4 then recovers substantially on Chowilla wet_train (0.093 m) via learned EXT+WSE mapping, while Burnett H-LSG O4 remains 0.387 m—still far below LF-only RMSE (0.989 m wet_train) but leaving residual depth error. Burnett global O4 is lower (0.179 m) with a larger truncation gap (Section 6.3).

### 6.3 Global versus residual H-LSG

**Figure 3** (`fig03_global_vs_hlsg_ab`) contrasts global (`zoning: none`) versus residual H-LSG on Chowilla and Burnett Max Grp1. On Chowilla, wet_train CSI is essentially flat (0.974 global vs 0.976 H-LSG); wet_train RMSE is slightly lower for global (0.088 m) than H-LSG (0.093 m). The diagnostic contrast is O2−O1: **0.057** (global) versus **0.013** (H-LSG). On Burnett, wet_train CSI is likewise flat (0.975 global vs 0.975 H-LSG), while O2−O1 shrinks from **0.049** (global) to **0.009** (H-LSG). Burnett global wet_train RMSE (0.179 m) is lower than H-LSG (0.387 m) on this fold, so residual zoning is not a universal RMSE win either—its reproducible role remains truncation/refinement, not a CSI headline.

### 6.4 Chowilla strong-LF anti-case (protocol sensitivity)

Under all_cells, Chowilla LSG-Max CSI is 0.390 with RMSE 3.789 m for both H-LSG and global, because many HF-wet cells outside the train wet mask are scored as misses when EXT training focuses on Fraehr wet categories. Under wet_train, CSI is 0.976 (H-LSG) with RMSE 0.093 m. LF only remains high on all_cells CSI (0.930) because the coarse LF already floods a large footprint. This anti-case is a **result about scoring protocol**, not evidence that LSG “fails” Chowilla under Fraehr wet_train reporting. **Figure 5** (middle row) visualises the spatial pattern for event E1.

### 6.5 CRPS-scale uncertainty calibration

**Table 4. Variance calibration (`crps_scale`) and selected probabilistic scores.** Carlisle values from the workflow `*_uq_calibrated.json`. Chowilla/Burnett before→after pairs from independent rescores of saved H-LSG states (`..._hlsg_max_uq_calibrated.json`); workflow-fit `var_scale` on the original Max summaries was 0.309 (Chowilla) and 0.606 (Burnett).

| Case / surface | *s* (`var_scale`) | CRPS (uncal. → cal.) | cov90_active (uncal. → cal.) | Point CSI/RMSE |
|----------------|--------------------:|----------------------|------------------------------|----------------|
| Carlisle Max | 0.417 | 0.039 → 0.028 | 0.990 → 0.966 | Unchanged (CSI 0.976; RMSE 0.061 m all_cells) |
| Carlisle TS | 0.900 | ≈0.0165 (near-calibrated) | — | Unchanged |
| Chowilla H-LSG Max (rescore) | 0.419 | 2.155 → 2.155 | 0.334 → 0.287 | Unchanged by construction (CSI 0.976; RMSE 0.093 m wet_train) |
| Burnett H-LSG Max (rescore) | 0.604 | 0.133 → 0.127 | 0.943 → 0.890 | Unchanged (CSI 0.975; RMSE 0.387 m wet_train) |

On Carlisle Max, active 90% coverage moves closer to nominal after shrinking over-wide intervals. **Figure 4** (`fig04_uq_calibration_crps_scale`) now includes Chowilla/Burnett before/after CRPS. On Burnett, CRPS falls and active coverage moves toward 0.90. On Chowilla Grp1 Max the same `crps_scale` protocol yields essentially **flat CRPS** (2.155 → 2.155) while coverage moves **away** from nominal—report this as a negative/null calibration outcome on that fold, not as a silent success. Prefer `coverage_*_active` over all-cell coverage when EXT-dry zeros dominate.

### 6.6 Spatial map panels and P(wet)

**Figure 5** shows HF reference, LF, LSG-Max H-LSG maximum-depth fields, and cell-wise inundation probability *P*(wet) = *P*(*h* ≥ 0.03 m) for event E1 on each case (`fig05_spatial_maps_*_E1`; panel e). Probabilities are exported to `pred_examples.npz` as `inundation_prob_lsg_max` (Carlisle mean ≈ 0.364; Chowilla ≈ 0.310; Burnett ≈ 0.554 over the stored events). Qualitatively, Burnett exhibits the clearest visual LF→LSG correction; Carlisle differences are subtler given strong LF; Chowilla highlights the extent/mask tension discussed in Section 6.4.

### 6.7 Chowilla `wet_correlation` zoning sensitivity

**Figure 6** (`fig06_zoning_wet_correlation_ab`) and **Table 5** compare Chowilla Max Grp1 under global, `residual_kmeans`, and `wet_correlation` zoning. Wet_train CSI rises slightly under `wet_correlation` (0.978) versus H-LSG (0.976) and global (0.974), with O2−O1 = 0.010—still a small CSI delta relative to the LF→LSG lift. This is a single-fold sensitivity, not a claim that correlation zoning dominates residual k-means.

**Table 5. Chowilla Max Grp1 wet_train zoning sensitivity (LSG-Max).**

| Zoning | CSI wet_train | RMSE wet_train (m) | test O2−O1 (m) |
|--------|--------------:|-------------------:|---------------:|
| global (`none`) | 0.974 | 0.088 | 0.057 |
| `residual_kmeans` | 0.976 | 0.093 | 0.013 |
| `wet_correlation` | 0.978 | 0.094 | 0.010 |

---

## 7. Discussion

### 7.1 Central advance

The central advance is a **diagnostic and probabilistic methods package** for multi-fidelity LSG on public data: residual hierarchical localization, O1–O4 attribution, and CRPS-calibrated map uncertainty—evaluated without claiming that zoning universally raises CSI.

### 7.2 Where multi-fidelity LSG carries the skill

Burnett and Chowilla wet_train depth RMSE show large LF→LSG lifts. Carlisle’s LF is already skillful on extent; LSG still tightens depth and slightly improves CSI. Leading with zoning CSI deltas would misrepresent the evidence.

### 7.3 Where residual zoning helps

Zoning consistently shrinks O2−O1 on Max-style paths in the Chowilla and Burnett global A/Bs and contributes small truncation gaps on Carlisle/Burnett H-LSG Max (0.005–0.009 m). That benefit is real on these public folds, but “condition-dependent” here means **observed across heterogeneous cases and scoring protocols**, not yet a training-only decision rule that predicts Δskill before seeing HF test truth (such a predictor remains **待补充**). Communicate zoning as refinement of subspace expressibility, not as a substitute for multi-fidelity mapping. Residual `kmeans` labels are residual-response classes; geographic contiguity is not enforced (**待补充**: zone maps / contiguity diagnostics). Matched total EOF/inducing budgets between global and H-LSG are **未运行 / 待补充**, so capacity-matched localization claims must stay bounded. Chowilla `wet_correlation` yields a slightly higher wet_train CSI (0.978) with O2−O1 ≈ 0.010 on Grp1 Max—still a small CSI delta, consistent with the same diagnostic framing.

### 7.4 Relation to prior art

Relative to Tan et al. (2025), we agree that regionalization and error splitting matter; we differ by using simultaneous residual multi-zone hierarchy on the whole domain and a four-stage oracle ladder on dual EXT+WSE. Relative to Wang et al. (2025) REOF–SGP, we use residual (not rotated) hierarchical EOFs inside Fraehr-style LSG with public three-case diagnostics. Relative to Wang et al. (2026), we implement the named zonal-EOF future direction on public cubes rather than licensed Brisbane events, and we add calibrated UQ and O1–O4.

### 7.5 Rival explanations and risks

Modest CSI differences between global and H-LSG could reflect fold noise, GP hyperparameter sensitivity, or mask definitions rather than zoning per se; the O2−O1 contrast is the more stable diagnostic. Chowilla all-cell CSI 0.390 could be misread as model collapse; wet_train and O4 refute that reading. SGPR inducing floors are engineering necessities for Max-path H-LSG; without them, O4 regressions obscure zoning assessment (documented in repository README).

### 7.6 Open questions

Does CRPS-scale *s* transfer across events and sites without retuning? Chowilla’s flat CRPS under the same protocol already warns against universal transfer. Do full-TS Chowilla/Burnett folds change the zoning story (**未运行 / 待补充**; Burnett full HF stack ≈199 GB vs ~128 GB host RAM)? How does residual H-LSG compare with Tan-style single-focus retraining on the same public splits?

---

## 8. Limitations

1. Chowilla/Burnett headline results are Max-surface Grp1; full-TS Grp1 is **未运行 / 待补充** (Burnett in-memory HF cube ≈199 GB ≫ ~128 GB RAM; Chowilla dual EXT+WSE+UQ similarly constrained).  
2. Equal-capacity (matched total modes / inducing points) global vs H-LSG and non-residual geographic zoning controls beyond the Chowilla `wet_correlation` sensitivity are **未运行 / 待补充**.  
3. Brisbane licensed appendix is **未运行**.  
4. Carlisle/Chowilla Max Grp1 use a single hold-out event; Burnett uses 18. We do not claim multi-fold statistical significance tests.  
5. Nested CV for CRPS scale *s* and oracle-order factorial swaps are **未运行 / 待补充**.  
6. Author metadata, funding, and exact environment pins: **待补充**.  
7. CRPS-scale can be null or adverse on some folds (Chowilla Max rescore: flat CRPS; coverage moves away from nominal)—do not generalise Carlisle’s calibration win.

---

## 9. Conclusions

We present a reproducible EXT+WSE LSG methods stack with residual hierarchical zoning, O1–O4 oracle attribution, and CRPS-calibrated GP uncertainty on three public multi-fidelity flood cases. Multi-fidelity LSG provides the primary skill gains where LF is weak. Residual zoning mainly reduces held-out O2−O1 (subspace-expressibility) gaps and should not be marketed as a universal CSI upgrade. Strong-LF settings require explicit wet_train versus all_cells reporting. Calibrated variance scaling improves probabilistic scores on over-dispersed Max-path posteriors while leaving mean maps—and therefore CSI/RMSE—unchanged by construction. These results support methods reuse at WRR / JoH / EMS: diagnose error sources, publish uncertainty, and bound localization claims to verified case conditions rather than a universal zoning CSI story.

---

## 10. Data and code availability

- Public HF/LF cubes: Fraehr (2024), DOI [10.26188/24312658](https://doi.org/10.26188/24312658).  
- Workflow configs: `config/{carlisle,chowilla,burnett}.yaml` in this repository.  
- Evaluation JSON: `outputs/evaluation/{carlisle,chowilla,burnett}/`.  
- Figures: `outputs/figures/` (manifest `figure_manifest.json`).  
- Hybrid LSG reference code (upstream): https://github.com/nfraehr/Hybrid_LSG_model  
- Brisbane licensed TUFLOW/URBS library: access upon request via Queensland BRCFS channels (Wang et al., 2026); **not redistributed here**.

---

## 11. Author contributions

待补充 (CRediT roles to be completed by the author team).

---

## 12. Competing interests

待补充. The authors declare 待补充.

---

## 13. Acknowledgements

待补充.

---

## References

Chang, C.-H., et al. (2020). Remote sensing-based flood inundation forecasting (FIER). *Remote Sensing of Environment*. https://doi.org/10.1016/j.rse.2020.111732

Chang, C.-H., et al. (2023). FIER-related environmental modelling software developments. *Environmental Modelling & Software*. https://doi.org/10.1016/j.envsoft.2023.105643

Donnelly, J., et al. (2022). Gaussian process flood emulator. *Water Research*. https://doi.org/10.1016/j.watres.2022.119100

Eilander, D., et al. (2025). SFINCS–LSG (EGU abstract). https://doi.org/10.5194/egusphere-egu25-5209

Eilander, D., et al. (2026). SFINCS–LSG (EGU abstract). https://doi.org/10.5194/egusphere-egu26-11062

Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2022). Upskilling low-fidelity hydrodynamic models of flood inundation via EOF and Sparse GP. *Water Resources Research*, 58, e2022WR032248. https://doi.org/10.1029/2022WR032248

Fraehr, N., Wang, Q. J., Wu, W., & Nathan, R. (2023). Fast and accurate hybrid floodplain LSG. *Water Resources Research*, 59, e2022WR033836. https://doi.org/10.1029/2022WR033836

Fraehr, N., et al. (2023b). Supercharging hydrodynamic inundation models. *Nature Water*. https://doi.org/10.1038/s44221-023-00132-2

Fraehr, N., et al. (2024). LSG versus ML surrogates on Carlisle/Chowilla/Burnett. *Water Research*. https://doi.org/10.1016/j.watres.2024.121202

Fraehr, N. (2024). Public multi-fidelity flood cubes and code. Figshare. https://doi.org/10.26188/24312658

Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359–378.

Kohanpur, A. H., et al. (2023). Physics-informed GPR flood UQ. *Water Resources Research*. https://doi.org/10.1029/2022WR033939

López-Lopera, A. F., et al. (2022). Multioutput GP coastal flood. *Reliability Engineering & System Safety*. https://doi.org/10.1016/j.ress.2021.108139

Lu, et al. (2025). GP kernel choice in LSG. *Journal of Hydrology*. https://doi.org/10.1016/j.jhydrol.2025.132949

Markert, K. N., et al. (2026). Scalable FIER by watershed mosaicking. *Hydrology and Earth System Sciences*, 30, 459. https://doi.org/10.5194/hess-30-459-2026

Siripatana, A., et al. (2025). GPR versus PCE inundation UQ. *Water Resources Research*. https://doi.org/10.1029/2024WR039668

Tan, et al. (2025). Hybrid LSG downscaling and regionalized training. *Hydrology and Earth System Sciences*, 29, 3833. https://doi.org/10.5194/hess-29-3833-2025

Wan, et al. (2025). REOF flood extent ML. *Environmental Modelling & Software*. https://doi.org/10.1016/j.envsoft.2025.106562

Wang, R., et al. (2025). REOF + Sparse GP LF→HF. *International Journal of Disaster Risk Science*. https://doi.org/10.1007/s13753-025-00642-5

Wang, W., Wang, Q. J., & Nathan, R. (2026). Strategies for predicting flood inundation in a large and complex floodplain. *Water Resources Research*, 62, e2025WR042481. https://doi.org/10.1029/2025WR042481

Zanchetta, A. D. L., & Coulibaly, P. (2022). Probabilistic inundation maps via surrogates. *Geosciences*, 12(11), 426. https://doi.org/10.3390/geosciences12110426

Zenodo SFINCS–LSG scripts/data: https://doi.org/10.5281/zenodo.20352880

---

## Appendix A. Terminology ledger (canonical forms)

LSG; LSG-TS; LSG-Max; LF; HF; EOF; EC; EXT; WSE; H-LSG; residual_kmeans; SGPR; CRPS; CSI; POD; RFA; O1–O4; wet_train; all_cells; `var_scale`; AF; TF; τ = 0.03 m.

## Appendix B. Figure and table inventory

| ID | File / content | Role |
|----|----------------|------|
| Fig. 1 | `fig01_cross_case_csi_rmse_wet_train` | Wet_train CSI/RMSE cross-case |
| Fig. 2 | `fig02_error_budget_o1o4` | O1–O4 ladders |
| Fig. 3 | `fig03_global_vs_hlsg_ab` | Global vs H-LSG (Chowilla + Burnett) |
| Fig. 4 | `fig04_uq_calibration_crps_scale` | CRPS-scale UQ before/after |
| Fig. 5 | `fig05_spatial_maps_{carlisle,chowilla,burnett}_E1` | Spatial maps + P(wet) |
| Fig. 6 | `fig06_zoning_wet_correlation_ab` | Chowilla zoning sensitivity |
| Table 1 | Case inventory | Data |
| Table 2 | CSI/RMSE | Point skill |
| Table 3 | O1–O4 | Attribution |
| Table 4 | `var_scale` / CRPS | UQ |
| Table 5 | Chowilla zoning CSI/RMSE/O2−O1 | Zoning sensitivity |

## Appendix C. Items marked 待补充 / 未运行

- Author names, affiliations, corresponding author, acknowledgements, competing interests, CRediT contributions  
- Exact pinned software versions table  
- Chowilla / Burnett full-TS Grp1 folds (memory; Burnett HF stack ≈199 GB)  
- Brisbane licensed appendix results  
- FloodCastBench  
- Equal-capacity global vs H-LSG; residual zone contiguity maps  
- Nested CV for CRPS *s*; oracle-order factorial swaps  
- Training-only predictor of when zoning helps