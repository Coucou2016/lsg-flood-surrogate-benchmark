# Reference papers for this manuscript

This folder holds the **anchor papers** that our manuscript and Chinese report imitate for method framing and **results presentation** (visual-first inundation maps before statistics).

Markdown conversions here are **English structural extractions** (text + figure/table caption indices). They are **not** full bilingual nature-reader builds (no figure image crops, no Chinese parallel columns).

## Which papers we imitate

| Role | Paper | What we take from it |
| --- | --- | --- |
| LSG method (core) | **Fraehr et al. 2022 WRR** | EOF + Sparse GP upskilling; extent dynamics; POD/RFA/CSI language; hit/miss/false-alarm maps |
| LSG method (EXT+depth / unstructured) | **Fraehr et al. 2023 WRR** | Hybrid depth+extent LSG; study-area map first; peak-depth panels; detected/miss/FA categorical maps; CSI/POD/RFA tables |
| Benchmark cases + ML comparison framing | **Fraehr et al. 2024 Water Research** | Carlisle / Chowilla / Burnett public cubes; surrogate vs LSG comparison design (PDF **not** acquired here — see below) |
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

- PDF: **未下载**
- Reason: Europe PMC marks full text as **subscription required**; Minerva item is **metadata.only** (no ORIGINAL bitstream); ScienceDirect presented a robot challenge. OpenAlex listed a hybrid/OA flag, but no lawful PDF URL resolved in this environment.
- Do **not** scrape paywalled Elsevier PDFs. Keep any future institutional copy **local-only** and **exclude from git** (Elsevier license typically does not allow redistribution of the VoR PDF).
- We still cite this paper for Carlisle/Chowilla/Burnett benchmark framing; conventions cross-check uses Fraehr 2022/2023 + Wang 2026 + our prior literature notes.

### Wang et al. 2026 — WRR `10.1029/2025WR042481`

- PDF: [`Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.pdf`](Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.pdf) (~3.05 MB; already present in workspace root — copied here, not re-downloaded)
- Markdown (publisher-style local extract, pre-existing): [`Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.md`](Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.md)
- Markdown (PDF structural extract): [`Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.from_pdf.md`](Wang_2026_WRR_Strategies_Flood_Inundation_Large_Complex.from_pdf.md)
- License / access: AGU gold OA (**CC BY**).
- Redistribution: **OK** under CC BY with attribution.

## Presentation conventions

See [`exemplar_conventions.md`](exemplar_conventions.md) for the exact figure/table/metric order we now mirror in `docs/paper/manuscript.md` and `docs/report/`.

## Git / publish note

- Push OA PDFs (**Fraehr 2022 CC BY-NC**, **Fraehr 2023 CC BY**, **Wang 2026 CC BY**) only if the public mirror’s license policy allows; CC BY-NC is redistribution-OK for non-commercial mirrors with attribution.
- **Never** push Elsevier VoR PDFs if later acquired under subscription.
- Auxiliary `_*.json` probe files in this folder are scratch metadata and need not be published.
