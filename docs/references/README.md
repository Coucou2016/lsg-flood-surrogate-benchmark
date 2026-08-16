# Reference papers for this manuscript

This folder holds the **anchor papers** that our manuscript and Chinese report imitate for method framing and **results presentation** (visual-first inundation maps before statistics).

Markdown conversions here are **English structural extractions** (text + figure/table caption indices). They are **not** full bilingual nature-reader builds (no Chinese parallel columns).

## Which papers we imitate

| Role | Paper | What we take from it |
| --- | --- | --- |
| LSG method (core) | **Fraehr et al. 2022 WRR** | EOF + Sparse GP upskilling; extent dynamics; POD/RFA/CSI language; hit/miss/false-alarm maps |
| LSG method (EXT+depth / unstructured) | **Fraehr et al. 2023 WRR** | Hybrid depth+extent LSG; study-area map first; peak-depth panels; detected/miss/FA categorical maps; CSI/POD/RFA tables |
| Benchmark cases + ML comparison framing | **Fraehr et al. 2024 Water Research** | Carlisle / Chowilla / Burnett public cubes; LSG vs 1dCNN / LSTM-SRR / GP-EOF / LSTM-EOF; LOOCV-by-group; wet-train scoring; CSI + depth metrics + extrapolation protocol |
| Training-event selection (HF budget) | **Fraehr et al. 2024/2025 J. Environ. Manage.** | LESS: LF-candidate → max-inundation + EOF-diversity selection of HF training events (complements our capacity controls; not a zoning claim) |
| LSG-Max / LSG-TS + large floodplain framing | **Wang et al. 2026 WRR** | LSG-Max vs LSG-TS; LF resolution; peak-depth **error maps** (red/blue); extent agreement maps; hydrograph panels; metric bubble plots |

## Local files

### Fraehr et al. 2022 — WRR `10.1029/2022WR032248`

- PDF: [`Fraehr_2022_WRR_Upskilling_LF_Hydrodynamic_LSG.pdf`](Fraehr_2022_WRR_Upskilling_LF_Hydrodynamic_LSG.pdf) (~1.87 MB)
- Markdown: [`Fraehr_2022_WRR_Upskilling_LF_Hydrodynamic_LSG.md`](Fraehr_2022_WRR_Upskilling_LF_Hydrodynamic_LSG.md)
- License / access: AGU open access (**CC BY-NC**). Acquired lawfully from University of Melbourne Minerva Access bitstream (publisher Wiley/AGU PDF blocked by Cloudflare for automated curl on this host).
- Redistribution: **OK for non-commercial sharing with attribution** under CC BY-NC; prefer linking the DOI for commercial contexts.

### Fraehr et al. 2023 — WRR `10.1029/2022WR033836`

- PDF: [`Fraehr_2023_WRR_Fast_Accurate_Hybrid_Floodplain_LSG.pdf`](Fraehr_2023_WRR_Fast_Accurate_Hybrid_Floodplain_LSG.pdf) (~2.44 MB)
- Markdown: [`Fraehr_2023_WRR_Fast_Accurate_Hybrid_Floodplain_LSG.md`](Fraehr_2023_WRR_Fast_Accurate_Hybrid_Floodplain_LSG.md)
- License / access: AGU open access (**CC BY**). VoR PDF fetched via authenticated browser session after Cloudflare challenge (OA; Minerva record is metadata-only).
- Redistribution: **OK** under CC BY with attribution.

### Fraehr et al. 2024 — Water Research `10.1016/j.watres.2024.121202`

- **Verified identity (from PDF first page):** *Assessment of surrogate models for flood inundation: The physics-guided LSG model vs. state-of-the-art machine learning models* — Niels Fraehr, Quan J. Wang, Wenyan Wu, Rory Nathan — *Water Research* **252 (2024) 121202** — available online 24 January 2024 — **CC BY 4.0**.
- Local PDF (gitignored): `1-s2.0-S0043135424001027-main.pdf`
- MinerU Markdown (gitignored full text): [`Fraehr_2024_WaterResearch_Assessment_surrogate_LSG.md`](Fraehr_2024_WaterResearch_Assessment_surrogate_LSG.md) — extraction method: **MinerU API** (`/api/v4/file-urls/batch`, model `vlm`).
- Assets (gitignored): `Fraehr_2024_WaterResearch_Assessment_surrogate_LSG_assets/`
- **Publish policy:** VoR PDF + full-text MD are **local-only** (excluded from the public GitHub mirror by default even though the VoR is CC BY). Cite the DOI; do not redistribute the Elsevier layout PDF from this repo.

### Fraehr et al. 2024/2025 — Journal of Environmental Management `10.1016/j.jenvman.2024.123570`

- **Verified identity (from PDF text):** *Generation and selection of training events for surrogate flood inundation models* — Niels Fraehr, Quan J. Wang, Wenyan Wu, Rory Nathan — *Journal of Environmental Management* **373 (2025) 123570** — available online 6 December 2024 — **CC BY 4.0**.
- Local PDF (gitignored): `1-s2.0-S0301479724035564-main.pdf`
- MinerU Markdown (gitignored full text): [`Fraehr_2024_JEnvironManage_Generation_selection_training_events.md`](Fraehr_2024_JEnvironManage_Generation_selection_training_events.md) — extraction method: **MinerU API**.
- Assets (gitignored): `Fraehr_2024_JEnvironManage_Generation_selection_training_events_assets/`
- **Publish policy:** same as above — local-only; cite DOI only in the public mirror.

### Wang et al. 2026 — WRR `10.1029/2025WR042481`

- PDF: [`Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.pdf`](Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.pdf) (~3.05 MB; already present in workspace root — copied here, not re-downloaded)
- Markdown (publisher-style local extract, pre-existing): [`Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.md`](Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.md)
- Markdown (PDF structural extract): [`Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.from_pdf.md`](Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.from_pdf.md)
- License / access: AGU gold OA (**CC BY**).
- Redistribution: **OK** under CC BY with attribution.

## Presentation conventions

See [`exemplar_conventions.md`](exemplar_conventions.md) for the exact figure/table/metric order we now mirror in `docs/paper/manuscript.md` and `docs/report/`.

## Git / publish note

- Push OA AGU PDFs (**Fraehr 2022 CC BY-NC**, **Fraehr 2023 CC BY**, **Wang 2026 CC BY**) only if the public mirror’s license policy allows; CC BY-NC is redistribution-OK for non-commercial mirrors with attribution.
- **Do not** push Elsevier VoR PDFs or their MinerU full-text Markdown (Fraehr 2024 Water Research; Fraehr 2024/2025 J. Environ. Manage.), even when CC BY — keep them local and cite DOIs.
- Auxiliary `_*.json` probe files and `_mineru_convert_report.json` in this folder are scratch metadata and need not be published.
- MinerU API token lives only in `.secrets/mineru_token.txt` or `MINERU_TOKEN` (never committed).
