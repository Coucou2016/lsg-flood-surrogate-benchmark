# Literature review — verified references and novelty gaps

**Date:** 2026-08-16 (re-checked same day after ChatGPT peer-review advisor pass)  
**Workflows:** nature-academic-search `multi-source-search` + `citation-verification` (WebSearch/WebFetch; ChatGPT used as advisor only).  
**Advisor chats:** literature https://chatgpt.com/c/6a8129c4-e368-83ea-b448-236b427f9ae0 ; peer review https://chatgpt.com/c/6a815ce3-60c4-83ea-99ad-0149a2ac3c4c (web search ON; DOIs cited).  
**GitHub for ChatGPT:** not available this turn (`gh` missing on host); advisor reviewed pasted CONTEXT only.

## Verified core LSG lineage

| Paper | Venue / year | DOI | Status |
|---|---|---|---|
| Fraehr et al. — Upskilling LF hydrodynamic flood models via EOF + Sparse GP | WRR 2022 | [10.1029/2022WR032248](https://doi.org/10.1029/2022WR032248) | verified |
| Fraehr et al. — Fast/accurate hybrid floodplain LSG (depth + unstructured) | WRR 2023 | [10.1029/2022WR033836](https://doi.org/10.1029/2022WR033836) | verified |
| Fraehr et al. — Supercharging hydrodynamic inundation models | Nature Water 2023 | [10.1038/s44221-023-00132-2](https://doi.org/10.1038/s44221-023-00132-2) | verified |
| Fraehr et al. — LSG vs ML surrogates (Carlisle/Chowilla/Burnett) | Water Research 2024 | [10.1016/j.watres.2024.121202](https://doi.org/10.1016/j.watres.2024.121202) | verified |
| Wang, Wang & Nathan — Strategies for large/complex floodplain LSG (Brisbane) | WRR 2026 | [10.1029/2025WR042481](https://doi.org/10.1029/2025WR042481) | verified; local MD confirms §5/§6 name **zonal EOF as future work** |
| Lu et al. — GP kernel choice in LSG | Journal of Hydrology 2025 | [10.1016/j.jhydrol.2025.132949](https://doi.org/10.1016/j.jhydrol.2025.132949) | verified |
| Public cubes / code deposit | Figshare 2024 | [10.26188/24312658](https://doi.org/10.26188/24312658) | verified |

## SFINCS–LSG (compound coastal)

| Item | DOI / URL | Status |
|---|---|---|
| EGU 2025 abstract (early SFINCS–LSG) | [10.5194/egusphere-egu25-5209](https://doi.org/10.5194/egusphere-egu25-5209) | verified |
| EGU 2026 abstract | [10.5194/egusphere-egu26-11062](https://doi.org/10.5194/egusphere-egu26-11062) | verified (**both** years exist) |
| Zenodo scripts/data | [10.5281/zenodo.20352880](https://doi.org/10.5281/zenodo.20352880) | verified |
| SSRN preprint (compound SFINCS–LSG) | [10.2139/ssrn.6727349](https://doi.org/10.2139/ssrn.6727349) | verified metadata 2026-08-16; **not** a peer-reviewed journal article — cite as preprint if used |

**Correction vs ChatGPT first pass:** do not cite only EGU 2025; EGU26-11062 is real. Re-check 2026-08-16: Tan/Rukai Wang/Markert/SFINCS DOIs still resolve; exact residual hierarchical LSG + CRPS-map posterior + O1–O4 ladder still **NOT FOUND**.

## Closest prior art that constrains novelty

| Paper | DOI | What it is | Implication for us |
|---|---|---|---|
| Zeli Tan et al. 2025 — hybrid LSG downscaling; regionalized training; dimensionality-reduction vs LSG/mapping error | [10.5194/hess-29-3833-2025](https://doi.org/10.5194/hess-29-3833-2025) | LSG + regional focus subdomain + **two-part** error split (Houston depth+velocity) | Blocks “first LSG localization” and “first LSG error decomposition”; still ≠ simultaneous residual multi-zone hierarchy or O1–O4 ladder |
| Rukai Wang et al. 2025 — REOF + Sparse GP LF→HF | [10.1007/s13753-025-00642-5](https://doi.org/10.1007/s13753-025-00642-5) | Hydrodynamic LF/HF + **rotated EOF** + SGP | Blocks broad “first localized EOF multi-fidelity flood surrogate” |
| Wan et al. 2025 — REOF flood extent ML | [10.1016/j.envsoft.2025.106562](https://doi.org/10.1016/j.envsoft.2025.106562) | Satellite FIER/REOF lineage | Terminology risk only; not LSG |
| Markert et al. 2026 — scalable FIER by watershed mosaicking | [10.5194/hess-30-459-2026](https://doi.org/10.5194/hess-30-459-2026) | Spatially partitioned REOF forecasts | Blocks “first zonal EOF flood forecasting”; not LF→HF LSG |
| Chang et al. 2020 / 2023 FIER | [10.1016/j.rse.2020.111732](https://doi.org/10.1016/j.rse.2020.111732), [10.1016/j.envsoft.2023.105643](https://doi.org/10.1016/j.envsoft.2023.105643) | REOF inundation forecasting | Adjacent only |

## Probabilistic flood-surrogate UQ (not LSG-specific)

Verified examples used to **reject** “first probabilistic flood map surrogate”:

- Donnelly et al. 2022 GP flood emulator — [10.1016/j.watres.2022.119100](https://doi.org/10.1016/j.watres.2022.119100)
- López-Lopera et al. multioutput GP coastal flood — [10.1016/j.ress.2021.108139](https://doi.org/10.1016/j.ress.2021.108139)
- Kohanpur et al. 2023 flood UQ / physics-informed GPR — [10.1029/2022WR033939](https://doi.org/10.1029/2022WR033939)
- Siripatana et al. 2025 GPR vs PCE inundation UQ — [10.1029/2024WR039668](https://doi.org/10.1029/2024WR039668)
- Zanchetta & Coulibaly 2022 probabilistic inundation maps via surrogates — [10.3390/geosciences12110426](https://doi.org/10.3390/geosciences12110426) (DOI resolves; full-text fetch returned 406 here — treat metadata as verified, deep claim check as **uncertain** until PDF read)

## Local manuscript cross-check

`Water Resources Research - 2026 - Wang - Strategies for Predicting Flood Inundation in a Large and C.md` §5/§6:

> zonal EOF analysis … undertaken separately for each zone … future work

Fraehr companion code exists under `data/external/carlisle/python_data/`. Our contribution is an **implementation/evaluation** of that named future direction plus diagnostics/UQ — not discovery of the idea.

## Novelty triage table

| Claim | Verdict | Evidence |
|---|---|---|
| Multi-fidelity LSG itself | **Already published** | Fraehr 2022/2023; Wang 2026 |
| Separate EXT and depth/WSE modelling | **Already published** (concept) | Fraehr 2023 WRR |
| Any “localized/rotated EOF” for floods | **Already published** | Wang 2025 REOF-SGP; FIER lineage |
| Regionalized / focus-subdomain LSG | **Already published** | Tan 2025 |
| Two-part LSG error split (DR vs mapping) | **Already published** | Tan 2025 |
| Simultaneous whole-domain **residual hierarchical** multi-zone LSG (global + residual local bases; EXT global / WSE residual) | **Claimed novel / not found as exact match** | Searches + advisor; distinguish carefully from REOF and Tan |
| Calibrated LSG GP **posterior → inundation maps** with CRPS-scale variance | **Claimed novel / not found as exact match** | Probabilistic flood surrogates exist; LSG-calibrated map posterior not found |
| Staged **O1–O4 oracle** ladder for LSG | **Claimed novel / not found as exact match** | Tan’s two-component split is closest prior |
| Zoning yields large CSI gains | **Rejected by our JSON** | Modest O2−O1; Chowilla CSI driven by wet_train protocol / LSG not zoning |
| “First identification that global EOF compresses driver zones” | **Unsafe** | SFINCS–LSG EGU abstracts already discuss EOF compression noise |

## Explicit FOUND / NOT FOUND (advisor + independent check)

| Question | Narrow LSG wording | Verdict |
|---|---|---|
| (i) Zonal/hierarchical EOF for **multi-fidelity hydrodynamic LSG** with simultaneous local bases | Exact match | **NOT FOUND** (related: Tan regionalize; Wang REOF-SGP; FIER partitioning) |
| (ii) Calibrated probabilistic **LSG** with GP posterior on maps | Exact match | **NOT FOUND** (related: many non-LSG probabilistic flood surrogates) |
| (iii) O1–O4-style oracle ladder | Exact match | **NOT FOUND** (related: Tan ER_DR / ER_LSG) |

## ChatGPT advice retained vs rejected

**Retained (after verification):** Tan 2025 and Rukai Wang 2025 as highest novelty risks; frame as diagnostic/probabilistic extension of LSG; do not claim first localized EOF.

**Rejected / corrected:**

- SFINCS–LSG “only EGU 2025” → also EGU 2026 (`egu26-11062`).
- Any implication that zoning is the headline accuracy win → contradicted by local O2−O1 and Chowilla all-cells vs wet_train tables.
- Broad “first zonal EOF flood model” → false under FIER/Markert/Wang REOF.
- Occasional “Freaehr” typo in advisor text → Fraehr.
