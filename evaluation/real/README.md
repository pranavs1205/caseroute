# Real-report assessment: AI-assisted baseline complete

This is a **20-case known-history investigation study**, not a held-out discovery test. The source reports remain in the searchable graph and the runner supplies their IDs. Do not present its results as new-issue retrieval accuracy.

Selection was frozen before CaseRoute predictions: five multi-component reports, five sparse descriptions, five single-component reports, five other contexts. Selection uses a published deterministic hash seed. Demo cases and issues examined in previous saved runs are excluded. `plan.json` records IDs, source inputs, dataset revision/hash, exclusions, selection method and a content hash.

## Label before running

1. Read `review_packet.md` without looking at CaseRoute answers for those cases.
2. Fill `labels.csv`: reviewer initials/pseudonym, `reviewer_kind` (`human` or `ai_assisted`), semicolon-separated acceptable step IDs, `must_abstain` (`yes`/`no`), missing information and rationale.
3. `relevant_issue_ids` may contain independently identified useful source IDs. Leave it blank when unknown; blank does not mean irrelevant. Do not invent relevance labels. Original-source self-hits are a limitation of this known-history design.
4. Run `python real_evaluation.py lock`. This snapshots the labels and their hash. Subsequent changes invalidate the experiment rather than silently changing the score.

Allowed steps: `check_environment`, `review_recorded_resolution`, `request_details`, `investigate_component_boundary`. More than one can be acceptable. An outcome label such as Fixed or Invalid does not establish a root cause or a fix.

## Run and assess

```powershell
python real_evaluation.py run
# Optional separate model condition; makes actual calls to the configured provider:
python real_evaluation.py run --llm
```

The runner refuses unlabelled cases, changed labels/selection and prediction overwrites. Raw predictions include failures and are saved progressively. It verifies the graph's dataset revision. The graph-only and LLM conditions are separate; provider failures count as failures, not abstentions or silent fallbacks.

Fill the generated `post_review_graph.csv` / `post_review_llm.csv` after inspecting the returned source evidence. Use yes/no for `evidence_relevant`, `step_acceptable`, and `citations_supported`; give a concrete `failure_note`. Then run:

```powershell
python real_evaluation.py summarize
```

The summary distinguishes predeclared step agreement, required abstention, citation **membership**, predeclared relevance coverage, post-run content judgments (reviewer kind disclosed), and raw failures. Citation membership is not evidence support. Unjudged cases are not counted as correct. Report denominators and reviewer kind, preserve at least three failures if observed, and disclose the small stratified sample and single-reviewer limitations.

**Current status:** selection, pre-run AI-assisted labels, graph-only predictions and AI-assisted content judgments are complete. See [REPORT.md](REPORT.md): 7/20 prelabel agreement, 6/20 post-review acceptable actions, 10/20 useful non-self search hits, 0/8 required abstentions. Independent human review and an LLM-condition assessment remain pending. The old `evaluation/results.json` remains a separate authored synthetic policy benchmark.

Source: GitBugs / Apache Spark, Avinash Patil, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [DATASETS.md](../../DATASETS.md) for provenance and transformations. No CaseRoute predictions are included in the blinded source packet.

Judgment rubric: `evidence_relevant` means at least one useful **non-self** report in the top five search hits. `citations_supported` checks factual source binding, not whether the recommendation is adequate or a root cause is proven. Reviewer bias and excerpt-only review limits are in REPORT.md.
