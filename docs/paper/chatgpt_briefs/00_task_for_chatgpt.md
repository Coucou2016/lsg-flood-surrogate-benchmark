# Task for ChatGPT (external advisor only)

**Role.** You are an external peer-review / methods-writing advisor for a near-submission methods paper aimed at *Water Resources Research*, *Journal of Hydrology*, or *Environmental Modelling & Software*. A separate local agent will verify every numeric claim against repository JSON artifacts. Treat your advice as **non-authoritative**. Do not invent experiments, numbers, DOIs, or “typical” values.

**Web search.** Please turn **web search ON**. Prefer guidance on WRR / JoH / EMS methods-paper structure, AGU/Elsevier methods-paper conventions, and how to report **negative results** and **capacity-controlled ablations**. Cite sources you actually used.

## Primary materials (read from GitHub)

1. Briefs in this folder:  
   https://github.com/Coucou2016/lsg-flood-surrogate-benchmark/tree/main/docs/paper/chatgpt_briefs
2. Manuscript:  
   https://github.com/Coucou2016/lsg-flood-surrogate-benchmark/blob/main/docs/paper/manuscript.md
3. Research report (process detail; **not** the paper voice):  
   https://github.com/Coucou2016/lsg-flood-surrogate-benchmark/blob/main/docs/report/report.md
4. Supporting claim/evidence notes (repo-relative):  
   `docs/paper/04_capacity_controls.md`, `docs/paper/05_carlisle_capacity.md`, `docs/references/exemplar_conventions.md`

**Please list every GitHub URL / file you actually opened** at the start of your reply. If fetch fails, say so and work only from pasted excerpts.

## Constraints (hard)

1. **Paper vs research report.** The paper must be academic and publishable. Forbidden in the paper: local disk paths, absolute Windows paths, “we ran script X”, Cursor/ChatGPT process chatter, open TODOs such as 待补充 / 待修改, Chinese process notes. Repo-relative paths are acceptable only in Data/Code Availability when they identify public repository assets.
2. **Honesty on capacity controls.** Residual hierarchical zoning (H-LSG) is a **capacity-controlled negative localisation result** on Chowilla and Burnett (matched global often matches/beats O2−O1; Chowilla matched global has better wet RMSE; Burnett residual capacity worsens RMSE via LF→HF GP map). Carlisle Max is site-heterogeneous under a train-rank cap. Do not reframe this as a positive zoning accuracy win.
3. **No fabricated numbers.** If a quantity is not in the manuscript tables or cited JSON evidence paths, mark it unknown.
4. **Style target.** Imitate Fraehr et al. (2022, 2023 WRR; 2024 Water Research; 2024/2025 J. Environ. Manage.) and Wang et al. (2026 WRR): visual-first Results, third-person / standard scientific English, clear Methods→Results→Discussion, restrained novelty claims.
5. **Copyright.** Do not ask for or dump Elsevier full-text PDFs. Cite DOIs only.

## Deliverables requested from you

1. **Peer-review style critique** (Major / Minor) for WRR/JoH/EMS methods fit.
2. **Section-by-section polish plan** (Abstract → Conclusions + Availability): what to cut, move to report, rewrite, or reorder.
3. **Checklist of remaining defects** under: missing content; overreaching claims; paper–report leakage; style mismatch; statistical reporting; figure/table order; Data Availability hygiene.
4. **Concrete rewrite guidance** (phrase-level moves welcome) for Abstract novelty after capacity controls, Discussion framing of the negative result, and Methods clarity vs Fraehr/Wang.
5. Optional second pass: paper-vs-report boundary scrub (see `01_paper_vs_report_boundary.md`).

## What success looks like

Advice that helps a local editor produce a near-submission English manuscript that (a) keeps the diagnostic package and honest negative result as the contribution, (b) matches exemplar voice, and (c) contains no process leakage.
