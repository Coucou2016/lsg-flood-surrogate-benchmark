# ChatGPT reply (external advisor)

**Chat URL:** https://chatgpt.com/c/6a81ed88-e3d8-83ea-8220-836179df5d1c
**Web search:** ON (GitHub raw + venue guidance; Elsevier guide pages partially failed full fetch)
**Status:** Advisory only — local editor verifies against JSON.

---

Web search ran. I successfully opened and read the requested public repository materials. No requested GitHub fetch failed.

GitHub URLs/files actually opened:

https://github.com/Coucou2016/lsg-flood-surrogate-benchmark/tree/main/docs/paper/chatgpt_briefs

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/paper/chatgpt_briefs/00_task_for_chatgpt.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/paper/chatgpt_briefs/01_paper_vs_report_boundary.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/paper/chatgpt_briefs/02_current_claims_and_evidence.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/paper/chatgpt_briefs/03_style_exemplars_summary.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/paper/chatgpt_briefs/04_questions.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/paper/manuscript.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/report/report.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/references/exemplar_conventions.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/paper/04_capacity_controls.md

https://raw.githubusercontent.com/Coucou2016/lsg-flood-surrogate-benchmark/main/docs/paper/05_carlisle_capacity.md

https://github.com/Coucou2016/lsg-flood-surrogate-benchmark

https://github.com/nfraehr/Hybrid_LSG_model

I also verified Figshare DOI 10.26188/24312658; it resolves to Niels Fraehr's 2024 Carlisle/Chowilla/Burnett dataset/code deposit, CC BY 4.0. 
DOI
 I searched current AGU/WRR, Journal of Hydrology, and Environmental Modelling & Software guidance. The official Elsevier JoH/EMS guide pages appeared in search results, but direct full-page opening returned an internal fetch error, so my venue comments use the text exposed in Elsevier's official indexed results rather than claiming a full guide-page read. 
科学直达
+1

My overall assessment is: the scientific paper is now viable, and the capacity-controlled negative result is substantially stronger than a zoning-win paper would have been. The main remaining work is manuscript discipline, not another experimental campaign. The present draft has the core scientific logic, but it is not yet submission-clean because research-report/repository language remains embedded throughout.

A) Peer review — Major / Minor
Major 1 — The central claim is now defensible, but some causal wording remains stronger than the controls warrant

The matched-capacity evidence is coherent. On Chowilla, matched-global 15-D improves wet RMSE relative to H-LSG and reduces O2−O1 further; on Burnett, both H-LSG and matched-18 global reduce truncation error while degrading operational depth skill, and the oracle analysis locates the H-LSG discrepancy predominantly in the LF→HF mapping rather than EXT. Carlisle correctly remains a rank-capped heterogeneous case rather than being used to rescue a general localisation claim. 
GitHub
+2
GitHub
+2

I would nevertheless change language such as “confirming a capacity/approximation confound rather than a localisation effect” and “this is a capacity artefact.” Your own Limitations correctly acknowledge that matching input dimension does not equalize every kernel, regularisation, noise, and optimization degree of freedom. 
GitHub
 The referee-safe formulation is:

“The native-capacity advantage cannot be attributed uniquely to localisation and is reproduced or exceeded by changes in representation capacity under the tested controls.”

That is a strong negative result without claiming causal identification beyond the design.

Major 2 — Statistical interpretation is appropriate, but “negative result” must remain a controlled-comparison term, not a formal statistical null

The manuscript is correct to define held-out events, not cells, as evaluation units: Carlisle/Chowilla Max each have one held-out event, whereas Burnett has 18. 
GitHub
 Do not manufacture pixel-level p-values. Raster cells are spatially dependent components of a map, not independent experimental replicates.

This also means that phrases such as “statistically no localisation effect,” “equivalent performance,” or “proves no benefit” should not appear. Modern statistical guidance distinguishes effect magnitude from significance, and a formal claim of practical equivalence would require an a priori meaningful-effect bound plus an appropriate equivalence analysis. 
Taylor & Francis Online
+1

Your current preferred formulation—“no demonstrated accuracy advantage under the evaluated capacity-matched conditions”—is the correct level of inference.

Major 3 — The paper's most important experiment arrives too late

The current Results sequence remains visually sensible through domain → extent → error → probabilistic maps → aggregate skill, consistent with your Fraehr/Wang convention notes. 
GitHub
 But after the native global/H-LSG comparison, the reader is diverted through UQ and an alternative zoning sensitivity before reaching Tables 6–9, even though the equal-capacity tests determine the paper's principal conclusion. 
GitHub
+1

Move capacity control immediately after native global versus H-LSG. The logical sequence should be:

visual evidence → overall LSG skill → O1–O4 → native global/H-LSG → capacity controls → protocol sensitivity → UQ → secondary zoning sensitivity.

This preserves “visual-first” while making the paper claim-first once the basic spatial evidence is established.

Major 4 — Manuscript/report separation is presently the largest submission-readiness defect

The boundary brief is correct: scientific protocol belongs in the paper; local chronology, debug history, Windows/hardware diary, commands, filenames, and advisor history belong in the report. 
GitHub
 The manuscript currently violates that boundary in Abstract, Methods, Experimental Design, Results, Discussion, Availability, and Appendix C.

This is not cosmetic. At present, parts of §5 read like a repository README rather than a journal Methods section, while §3.8 reads like an execution log. 
GitHub
 The report itself demonstrates exactly what should stay outside the paper: absolute Windows location, Git-state notes, a ChatGPT session URL, debugging chronology, junction/MD5 details, and run history. 
GitHub
+1

Major 5 — Abstract requires substantial compression, especially for WRR

Using simple whitespace tokenization, I count roughly 371 words in the present Abstract. WRR/AGU requires an abstract under 250 words and recommends topic/gap → methods/data → key findings → novelty/implication. 
GitHub
+1

The current abstract also carries too many secondary details simultaneously: EXT+WSE, SGPR, O1–O4, CRPS, Chowilla matched capacity, Burnett mechanism, inducing points, zone count, Burnett LF→LSG CSI, Carlisle CRPS, Chowilla scoring protocol. The negative localisation finding gets diluted by diagnostic inventory.

For WRR, target about 220–235 words. Preserve only:

problem/gap;

matched-capacity test and diagnostic framework;

Chowilla + Burnett negative result;

Carlisle qualification;

one compact sentence on UQ/diagnostic contribution.

Major 6 — Scope limitations are scientifically adequate but need one extra layer of prominence

The limitations themselves are good: no full-TS Chowilla/Burnett capacity-controlled evaluation, imperfect capacity matching, no connectivity-constrained partition inference, path-dependent O1–O4, no Burnett nested CRPS CV, unequal event replication, perfect-prognosis HF targets, only three public sites, no ML rebenchmark, and no 50%-larger extrapolation rerun. 
GitHub

The problem is placement rather than absence. Abstract/Conclusions should identify the principal inference as applying to the evaluated Grp1 maximum-surface setting, rather than leaving readers to discover this in §8. You do not need to place RAM figures, Burnett nested-CV absence, Brisbane licensing, or the ML non-rerun in the Abstract.

Major 7 — Data/code availability is public but not yet WRR-clean

AGU requires supporting data/software to be available for peer review, prefers preserved repositories with persistent identifiers, requires an Availability Statement, and asks for repository, DOI/persistent identifier where available, software version/development-platform information, and licensing/access conditions. It also specifically recommends that analysis/figure code hosted on GitHub be preserved in a repository such as Zenodo. 
AGU

The public repository is accessible and clearly contains code, configs, tests, evaluation summaries, and figures. 
GitHub
 However, the root file listing I opened does not show an explicit LICENSE file. The upstream Hybrid LSG repository is GPL-3.0. 
GitHub
 Before WRR submission, I would freeze/tag the exact submitted code state, archive that release under a persistent DOI if feasible, and clarify licensing consistently with any incorporated upstream code. Do not invent a code DOI in the manuscript meanwhile.

Minor issues

The reference list is not yet bibliography-ready. Several entries are abbreviated descriptions rather than full article titles and complete metadata—for example “GP kernel choice in LSG,” “Gaussian process flood emulator,” and incomplete author forms such as “Lu, et al.” 
GitHub
 Run the entire list through the bibliography source rather than manually polishing selected citations.

“Anti-case,” “skill lives in,” “report honestly,” “hypothesis to be falsified,” “classic pathology”-type wording, and similar rhetorical constructions should be replaced by restrained scientific descriptions. “Negative result” itself is acceptable because it defines the study's principal controlled finding; the surrounding prose should be less argumentative.

For venue fit, I would currently rank EMS as the cleanest methods fit, because its official scope emphasizes clear model/software objectives, substantial testing/evaluation, comparisons with alternative approaches, uncertainty/sensitivity, and generalizable methodological insight. JoH is viable if the hydrological contribution remains central rather than becoming a software paper; its author guidance asks Research Articles to make a clear substantive contribution to hydrological science. WRR is also viable, particularly because this is directly in the LSG lineage, but requires the tightest scope qualification and Open Research cleanup. 
水资源研究
+3
www.elsevier.com
+3
期刊之家
+3

Bennett et al. (2013), Characterising performance of environmental models, DOI 10.1016/j.envsoft.2012.09.011, would be a useful high-level EMS citation: it explicitly combines visual analysis, quantitative criteria, test-data characterization, and purpose-dependent model evaluation. 
科学直达
 Hutton et al. (2016), DOI 10.1002/2016WR019285, is an optional WRR-level citation if reproducibility is explicitly discussed as part of the methodological contribution. 
AGU Publications

B) Section-by-section polish plan

Title/front matter. The scientific title is accurate. Remove “Target venues: WRR / JoH / EMS” from the manuscript. Author/affiliation/CRediT placeholders are tolerable during internal drafting, but they must be resolved before submission. 
GitHub

Abstract. Cut approximately one third. Delete the process-autobiographical sentence about an early interpretation of the runs. Replace “find that it does not survive” with the tested scientific outcome directly. Keep two principal quantitative contrasts at most. Mention Carlisle as the qualification. Compress UQ to one result/implication sentence. WRR specifically requires <250 words. 
GitHub
+1

Introduction. The three-gap structure works. Keep the distinction among localization, attribution, and UQ. Change “hypothesis to be falsified” to “evaluated under matched-capacity controls.” I would also remove most of the headline-result recital in the final Introduction paragraph and end with objectives/RQs plus a short paper roadmap, closer to Wang's architecture. Wang's 2026 WRR paper uses a conventional motivation → gap → study aim → section roadmap structure. 
AGU Publications
+1

Related work. Essentially sound. LESS is correctly defined as training-event selection rather than capacity allocation; Tan is correctly treated as focus-area regionalized training; REOF–SGP is an adjacent dimensional-reduction/localization lineage rather than the exact residual hierarchy tested here. External search supports those distinctions. 
科学直达
+2
HESS
+2
 Keep the explicit novelty exclusions. Do not expand this section into an exhaustive localisation review.

Methods §3.1–3.3. Strongest part of Methods. Retain equations, wet threshold, EXT/WSE distinction, and the capacity equation. Convert code identifiers such as residual_kmeans into scientific terminology on first use (“residual k-means zoning; implementation key …”), then avoid code typography repeatedly.

Methods §3.4. Keep the scientific point that small Max training sets make the sparse-GP approximation sensitive to inducing budget. Remove the debugging narrative about “two inducing points on a per-column linspace diagonal” from main Methods. That belongs in reproducibility documentation/SI unless the exact initialization algorithm is essential to reproducing a reported experiment. State the final rule and the sensitivity experiment instead. 
GitHub

Methods §3.5–3.7. Retain. The distinction between calibration changing variance but not mean predictions is particularly important. Likewise, keep the O1–O4 warning that the ladder is ordered and non-additive. 
GitHub
 Replace “comparable in spirit” with the more exact “not directly numerically comparable because only Grp1 rather than fold-aggregated performance is reported.”

Methods §3.8. Keep the statistical-unit paragraph and perfect-prognosis statement. Move the Windows build, Dell model, CPUs, RAM, and long package-version inventory out of the main text. A versioned environment/requirements file plus archived code is more useful reproducibility information than host-brand history. AGU emphasizes reproducible code/data availability rather than workstation autobiography. 
AGU

Datasets. Delete Table 1's Config column. Retain case, LF/HF source, approximate spatial scale, event/split information, and TS/Max availability. Replace the exact “199 GB versus 128 GB machine” narrative with “full time-series evaluation was not computationally feasible with the available memory” in the main text; details can remain in SI/report. Cite the Figshare dataset directly. 
DOI

Experimental design. Rewrite almost completely as scientific design rather than file manifest. Define: fixed field mode; native global baseline; residual hierarchy; matched-global-up control; residual-modes-zero control; inducing-budget sensitivity; zone-count sensitivity; folds; masks; oracle diagnostics; UQ protocol. Move YAML filenames, scripts, JSON filenames, and outputs/... catalogues to the public repository documentation. The present §5 is the largest paper/report leakage block. 
GitHub
+1

Results. Delete meta-comments about following Fraehr/Wang conventions, filesystem explanations for absent hydrographs, figure filenames, “honest” maps, and “our workflow scores.” The scientific results themselves are usable. Rename “strong-LF anti-case” to something such as “Sensitivity to the scoring domain on Chowilla.” 
GitHub

Reorder the core:

spatial figures;

headline skill;

O1–O4;

native global versus H-LSG;

capacity-controlled Chowilla/Burnett/Carlisle results and nuisance sensitivities;

scoring-domain sensitivity;

UQ;

optional wet-correlation zoning sensitivity.

That puts the evidence deciding RQ1 next to the observation that motivated RQ1.

Discussion. §7.1 is close to journal form. Keep the dual contribution: diagnostic package + controlled negative result. Delete all account-of-discovery language. Change categorical “capacity artefact” statements to “not uniquely attributable to localisation under matched-capacity controls.” Replace “the skill lives in the multi-fidelity map” with “the observed improvement is attributable primarily to the multi-fidelity mapping.” 
GitHub

Rename “Open questions” to “Implications and future evaluation” or fold it into Limitations. The existing questions are scientifically reasonable; the problem is that the manuscript should read as closed, not as a research notebook waiting for additional runs. 
GitHub

Limitations. Keep almost all scientific content. This is unusually good restraint. Shorten the computational-detail wording and foreground three boundaries: Max-surface/Grp1 scope, event-level replication, and perfect-prognosis HF target. The no-ML-rebenchmark/no-extrapolation statement should remain. 
GitHub

Conclusions. Retain the negative result as paragraph 1–2, but qualify it as applying to the evaluated Max-surface Grp1 setting. Remove “The reusable message for WRR / JoH / EMS.” Replace it with “The broader methodological implication is…”. 
GitHub

Availability. Replace the internal-path bullet catalogue with one journal paragraph; see F below.

C) Remaining-defects checklist
Missing / submission-incomplete

Abstract compression for WRR.

Complete bibliographic metadata and reference normalization.

Final author affiliations, CRediT, funding, acknowledgements, and competing-interest statement before submission.

Preferably a frozen/versioned preserved code release for WRR; do not invent its DOI.

Explicit code licensing/permissions check.

No additional scientific experiment is required merely to make the present central conclusion defensible; the unrun experiments should remain scope limitations rather than artificial gaps. 
AGU
+1

Unsupported/unreal suggestions or claims to eliminate

No full-TS Chowilla/Burnett result.

No Burnett nested-CRPS stability result.

No reproduced Fraehr-2024 ML benchmark.

No new 50% extrapolation experiment.

No Brisbane numerical evidence.

No observational-validation claim.

No exact 13-D global capacity match on Carlisle.

No “localisation never helps” generalization.

No statistical significance/equivalence claim. 
GitHub
+1

Evidence-ledger audit

C1 multi-fidelity carries primary skill: SUPPORTED.

C2 Chowilla capacity-controlled negative localisation result: SUPPORTED.

C3 Burnett extra residual capacity degrades RMSE through the mapping path: SUPPORTED, but use “consistent with / attributed by the ordered oracle diagnostic,” not absolute causal proof.

C4 inducing-point and zone-count confounds: SUPPORTED.

C5 Carlisle rank-limited heterogeneity: SUPPORTED; it must remain explicitly non-generalizable.

C6 CRPS calibration: SUPPORTED if written “helps Carlisle/Burnett under reported metrics; null/adverse on Chowilla”; do not say calibration universally improves reliability.

C7 Chowilla mask/protocol sensitivity: SUPPORTED.

C8 O1–O4 ordered, non-additive interpretation: SUPPORTED.

C9 novelty exclusions: SUPPORTED and essential.

C10 closed computational/scope boundaries: SUPPORTED, but Appendix C currently expresses them in revision-log form rather than paper form. 
GitHub
+1

One number group is visibly orphaned relative to the supplied claim/evidence ledger: the mean P(wet) values in the Figure 4 prose (≈0.364/0.310/0.554). 
GitHub
 I am not calling them fabricated; I am saying the supplied C1–C10 ledger does not provide a clear evidence pointer for them. Either attach their machine-readable provenance or remove them—they are not important to the paper's argument anyway.

Also reconcile support-note hygiene: 04_capacity_controls.md still states that Carlisle nested CRPS CV was not run, whereas the current manuscript, claim ledger, and 05_carlisle_capacity.md report the Carlisle nested result. 
GitHub
+1
 This looks like a stale handoff note, not a manuscript-data problem, but the public supporting documentation should not contradict the paper.

D) Answers to all questions in 04_questions.md
Q1 — Which closed limitations need greater prominence?

Most important: explicitly delimit the headline inference to the evaluated Grp1 Max-surface setting in Abstract and Conclusions.

Full-TS Chowilla/Burnett non-evaluation belongs prominently in Limitations, but the memory numbers do not belong in the Abstract. Burnett nested CRPS CV need not enter Abstract/Conclusions because the Burnett calibration result is secondary and current text already states its scope. No ML rebenchmark and no 50% extrapolation are sufficiently disclosed in Methods/Limitations; they need not consume Abstract space. Brisbane licensing is adequately disclosed as a dataset boundary. 
GitHub
+1

An arguably more important reader-facing limitation than any of those is that Carlisle/Chowilla Max headline comparisons each contain only one held-out event; keep this prominent in Statistical Reporting and Limitations.

Q2 — Effect sizes without p-values?

Yes. This is appropriate and preferable. With N_event=1 for two Max cases, no meaningful population-level event test exists there. Pixel p-values would create pseudoreplication. The recommended manuscript sentence is:

“Performance differences are reported as descriptive, controlled contrasts on held-out events. The held-out event is the independent evaluation unit; raster cells contribute to spatial performance metrics but are not treated as independent statistical replicates. Accordingly, no cell-level null-hypothesis tests are reported.”

Do not call the negative result “statistically significant” or “statistically equivalent.” Formal equivalence would require a scientifically justified equivalence margin and suitable independent replication. 
Taylor & Francis Online
+1

Q3 — Should Tables 6–9 move?

Yes. Put capacity controls immediately after native global/H-LSG. They determine whether the apparent O2−O1 change is localization or capacity. UQ and wet-correlation sensitivity should follow the central causal-diagnostic sequence rather than interrupt it.

This does not break visual-first architecture because the domain/extent/depth maps already occur before quantitative inference. 
GitHub
+1

Q4 — Three candidate Abstract endings

Option 1 — strongest default

“Matched-capacity controls therefore show that the apparent truncation advantage of H-LSG on Chowilla and Burnett is not uniquely attributable to localisation and does not yield a corresponding held-out depth-RMSE advantage over the relevant global baselines. Carlisle Max remains heterogeneous under a hard training-rank constraint. These results establish capacity-controlled evaluation, together with oracle error attribution and calibrated uncertainty, as a more defensible basis for assessing localised reduced-order flood surrogates.”

Option 2 — more quantitative

“On Chowilla, the capacity-matched global model produces lower wet RMSE and a smaller O2−O1 contrast than H-LSG, while on Burnett additional residual capacity reduces truncation error but degrades depth prediction through the LF→HF mapping. Carlisle differs because the global Max representation is training-rank limited. The resulting contribution is a diagnostic framework for separating localisation from model capacity rather than a claim that zoning universally improves flood-surrogate accuracy.”

Option 3 — shortest / WRR-oriented

“Residual hierarchical zoning thus provides no demonstrated accuracy advantage over the relevant capacity-controlled global baselines on Chowilla and Burnett, while Carlisle Max remains a rank-limited heterogeneous case. More generally, localisation claims in reduced-order flood surrogates should be evaluated against matched representation capacity and mapping complexity before improvements are attributed to spatial partitioning.”

All three preserve the negative result without claiming “zoning never helps.” The evidence for that site qualification is explicit in the current capacity-control results. 
GitHub
+1

Q5 — Availability paragraph

Use F below.

Q6 — Leakage scrub

See the dedicated scrub immediately below section F. The boundary brief's diagnosis is correct and I found additional instances. 
GitHub

Q7 — Is related-work positioning balanced?

Yes, substantially. LESS is correctly separated as an HF training-event-selection strategy; Tan's HESS work uses regionalized training for focus areas; Wang's REOF–SGP combines rotated EOFs with sparse GP. None is presented as the exact same simultaneous whole-domain global-plus-zonal residual hierarchy. 
科学直达
+2
HESS
+2

I would add at most one higher-level methods citation, particularly for EMS: Bennett et al. (2013), DOI 10.1016/j.envsoft.2012.09.011. It gives an established model-performance-evaluation rationale for combining visual diagnostics, test characterization, quantitative criteria, and advanced diagnostics. 
科学直达
 If reproducibility becomes an explicit contribution rather than just an Availability feature, Hutton et al. (2016), DOI 10.1002/2016WR019285, is also appropriate. 
AGU Publications

Do not add literature merely to make §2 longer.

Q8 — Current title and keywords?

The current title is scientifically accurate after capacity controls, although long. 
GitHub
 It correctly prevents reviewers from interpreting H-LSG as a zoning-win paper.

Two alternatives:

Residual hierarchical zoning in multi-fidelity flood surrogates: a capacity-controlled negative result with oracle error budgets and calibrated uncertainty

Does residual hierarchical zoning improve LSG flood surrogates? A capacity-controlled negative result on public benchmarks

I prefer option 1 for EMS and the current/question-style title or option 2 for WRR.

For keywords, I would prioritize indexing terms over rhetoric: flood inundation; multi-fidelity surrogate; LSG; empirical orthogonal functions; Gaussian process; model capacity; spatial localisation; uncertainty quantification; model evaluation. “Negative result” can stay in the title but is less useful as a keyword.

Q9 — What should a local editor reject automatically?

Reject any suggestion to:

add an experiment that was not run;

“complete” missing values from intuition;

alter JSON-backed numbers for narrative consistency;

create pixel-level p-values or significance claims;

describe non-significance as equivalence;

restore zoning as an accuracy-upgrade narrative;

claim exact Carlisle equal-capacity matching;

imply Burnett nested CRPS CV exists;

claim independent observational validation;

describe Brisbane as part of the public evaluated evidence;

conflate wet_train with all_cells;

conflate LSG-TS time-series metrics with Max-surface metrics;

turn O1–O4 differences into additive percentages or unique causal shares;

claim ML superiority without rerunning the Fraehr baselines;

invent a code DOI, software version, license, or repository release;

restore local disk paths, commands, script diaries, ChatGPT/Cursor references, Chinese TODO tokens, or revision-log prose.

E) Phrase-level moves toward Fraehr/Wang voice

These are the highest-value line edits:

Current tendency	Journal-style replacement
“an early reading of our own runs suggested…”	“Native-capacity comparisons suggested…”
“Here we test that claim … and find that it does not survive.”	“We evaluate this interpretation using matched-capacity controls.”
“hypothesis to be falsified”	“hypothesis evaluated under matched-capacity controls”
“confirming a … confound rather than a localisation effect”	“showing that the observed difference cannot be attributed uniquely to localisation”
“skill lives in the multi-fidelity map”	“the observed skill improvement is attributable primarily to the multi-fidelity mapping”
“Chowilla strong-LF anti-case”	“Chowilla sensitivity to the scoring domain”
“report this honestly”	“this null outcome is reported explicitly”
“the failure is localised by the oracle ladder”	“the oracle decomposition attributes the discrepancy primarily to…”
“a low-m collapse can be misread as…”	“performance is sensitive to the inducing-point budget, which confounds interpretation of zoning effects”
“Results follow the Fraehr/Wang visual-first convention”	delete; let the structure demonstrate it
“These are our workflow scores”	“Values correspond to the Grp1 evaluation used in this study…”
“reusable message for WRR / JoH / EMS”	“The broader methodological implication is…”

The target is not to eliminate scientific “we.” Fraehr and Wang use ordinary study-centered prose. The key is to remove autobiography, defensive adjectives, editor-facing language, and repository vocabulary. Your own style brief correctly captures their abstract pattern: problem → method → setting → a few quantitative outcomes → implication. 
GitHub
+2
AGU Publications
+2

F) Journal-ready Data and Code Availability

Data and code availability. The paired high- and low-fidelity hydrodynamic datasets for the Carlisle, Chowilla, and Burnett case studies are publicly available from the University of Melbourne Figshare repository (Fraehr, 2024; https://doi.org/10.26188/24312658
; CC BY 4.0). The implementation, configuration files, and evaluation outputs used for the analyses reported in this study are publicly available at https://github.com/Coucou2016/lsg-flood-surrogate-benchmark
. The implementation builds on and is cross-referenced to the publicly available Hybrid LSG reference code at https://github.com/nfraehr/Hybrid_LSG_model
. Licensed Brisbane TUFLOW/URBS data are not redistributed and are not part of the public-benchmark results reported in this study.

The Figshare scope and license are verified. 
DOI
 The two GitHub repositories are public. 
GitHub
+1

For WRR specifically, I would make one pre-submission infrastructure improvement: archive the submitted code release in a preservation repository and cite that persistent identifier in addition to GitHub. AGU explicitly distinguishes the development platform from preserved/citable software and asks for version/access/license information where applicable. 
AGU

Paper-vs-report boundary scrub

These are the must-fix manuscript leaks I verified.

Front matter — MUST FIX: remove the target-journal line. That is submission planning, not article content. 
GitHub

Abstract — MUST FIX: remove “an early reading of our own runs”. State the native-capacity observation impersonally. 
GitHub

§3.4 — MODIFY/MOVE: retain the final inducing-budget method and sensitivity rationale; move the debugging history of the old diagonal initialization to report/SI. 
GitHub

§3.8 — MUST MOVE: Windows build, Dell workstation, Xeon CPUs and host-RAM diary out of main Methods. 
GitHub

Table 1 — MUST FIX: delete config-file column. 
GitHub

§5 — MUST REWRITE: remove YAML names, script names, JSON inventories, outputs/... paths and artifact cataloguing from experimental-design prose. 
GitHub

§6 opening — MUST FIX: remove the meta-sentence announcing the Fraehr/Wang presentation convention.

§6 opening / Appendix B — MUST FIX: eliminate the Chinese token “缺数据” and filesystem rationale for hydrographs. Simply state that hydrograph evaluation is outside the retained evaluation outputs/scope. 
GitHub
+1

Figure prose — MUST FIX: remove internal identifiers such as fig03_peak_depth_error_*; retain “Figure 3.”

§6.4 — EVIDENCE FIX: remove or provenance-link the three mean P(wet) values; they are peripheral and currently orphaned relative to the supplied claim ledger. 
GitHub

§7.3 — MUST FIX: remove the second account of how earlier runs were interpreted. Scientific Discussion should explain evidence, not chronology of author belief. 
GitHub

Conclusions — MUST FIX: remove journal names from the claimed methodological implication. 
GitHub

Availability — MUST REWRITE: public DOI/repository first; internal subpaths are optional secondary locators, not the Availability Statement itself. 
GitHub
+1

Appendix B — DELETE OR CONVERT TO SI: internal figure-file inventory is manuscript-production metadata.

Appendix C — MUST DELETE FROM PAPER: “Completed in this revision,” internal Markdown pointers, and completed-run ledger belong in the research report/handoff, not a published appendix. 
GitHub

The research report should continue retaining the process material. Its Windows path, Git-state notes, advisor URL, ingest chronology, MD5/junction discussion, SGPR debugging sequence, and other engineering history are useful provenance for the project but would materially weaken the manuscript if copied back into it. 
GitHub
+1

Bottom-line editorial decision: I would not request another experiment before polishing this version. I would request a major textual/structural revision: foreground Tables 6–9; compress the Abstract below 250 words for WRR; make the negative finding explicitly conditional on the evaluated Max/Grp1 setting; remove all report/repository leakage; soften categorical causal language; and convert Availability into a persistent, public-resource statement. Once those are done, the core contribution reads as a legitimate methods result: capacity matching changes the interpretation of apparent localization gains, and the diagnostic framework explains why. 
GitHub
+1