# Style exemplars summary (paraphrase only; cite DOI)

**Copyright note.** This brief paraphrases structure and presentation conventions. It does **not** reproduce Elsevier full text. Prefer DOIs:

| Paper | DOI |
| --- | --- |
| Fraehr et al. 2022 WRR | https://doi.org/10.1029/2022WR032248 |
| Fraehr et al. 2023 WRR | https://doi.org/10.1029/2022WR033836 |
| Fraehr et al. 2024a Water Research | https://doi.org/10.1016/j.watres.2024.121202 |
| Fraehr et al. 2024b J. Environ. Manage. | https://doi.org/10.1016/j.jenvman.2024.123570 |
| Wang et al. 2026 WRR | https://doi.org/10.1029/2025WR042481 |

Local convention notes (non-copyrighted distillation): `docs/references/exemplar_conventions.md` on GitHub.

## Distilled style moves (what to imitate)

1. **Abstract.** Problem → method name → study setting → 2–4 quantitative outcomes → implication. Avoid lab-process autobiography.
2. **Introduction.** Motivation → prior LSG lineage → explicit gap → objectives/RQs → paper roadmap. Wang 2026 ends intro with “remainder of this paper is structured…”.
3. **Visual-first Results.** Study-area / domain map → categorical extent (hit/miss/false alarm) → peak-depth error maps (diverging red/blue) → then metric tables/plots. Hydrographs only when true time series exist.
4. **Metric language.** CSI / POD / RFA; wet-train vs all-cells stated explicitly; depth RMSE (our headline) vs Fraehr 2024a AvgPeakDiff/FI suite (do not silently equate).
5. **Methods tone.** Define symbols once; state protocols (threshold τ = 0.03 m; group hold-out); engineering necessities (e.g. inducing-point floor) as robustness, not novelty.
6. **Discussion.** Lead with what the evidence supports; compare to prior art without claiming priority they already have; limitations as closed scientific boundaries.
7. **Negative / null results.** Exemplars report limited accuracy and then diagnose (Wang 2026: initial limited accuracy → finer LF resolution). Model our capacity-control negative result the same way: clear, early, not a footnote.

## Ask ChatGPT (web search ON)

1. From WRR / JoH / EMS author guidance and recent methods papers, propose **phrase-level** edits so our manuscript voice matches Fraehr/Wang (third person or standard scientific “we”, restrained adjectives, no software-log tone).
2. Suggest Abstract and Discussion openers that foreground the **capacity-controlled negative localisation result** while still selling the diagnostic package (O1–O4, CRPS calibration, public benchmarks).
3. Comment on whether hardware/software pin lists belong in Methods, SI, or Availability for these venues.
4. Recommend figure/table numbering narrative that stays visual-first after capacity-control tables were added.
