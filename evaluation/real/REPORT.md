# Twenty real Spark reports: AI-assisted assessment

CaseRoute completed all 20 graph-only investigations. Its evidence inspection and persistence work, but the present decision policy is too generic for many real reports. This study does **not** justify a strong accuracy claim.

| Measure | Observed result |
| --- | --- |
| Completed executions | 20/20 |
| Action ID matches prewritten acceptable steps | 7/20 |
| Action acceptable after inspecting its specific component choices | 6/20 |
| At least one useful **non-self** report among the top five search hits | 10/20 |
| Clarification requested when prelabel required abstention | 0/8 |
| Citation IDs belong to supplied evidence | 20/20 |
| Factual source binding checked in generated text | 20/20 |
| Original issue itself appears in top five | 20/20 ? excluded from relevance successes |

Citation membership and source binding do not establish that the recommended step is good, a common root cause exists, or a fix was found. The factual-text check is narrow: titles, recorded outcomes, versions and cited source fields; it does not count recommendations as proven.

## Method and reviewer

The user authorized the Codex assistant to assess on their behalf. The reviewer is **AI-assisted and implementation-informed**, not an independent human or external model panel. Source-only acceptable-step labels and required abstentions were locked before generating these 20 CaseRoute answers. Lock timestamps and SHA-256 values are in `labels.lock.json`; raw answers are in `graph_predictions.json`. No labels were revised to improve the score.

Selection is deterministic and stratified: five multi-component, five sparse, five single-component and five other reports. Demo reports and previously examined saved-run issues were excluded. The sample is small and not representative of all Spark reports. The original reports remain searchable and the runner supplies their IDs: this measures **known-history investigation**, not discovery of new or held-out issues. All runs use the graph-only policy; no LLM calls or LLM quality scores are included.

Post-run judgments inspected source descriptions and returned candidate titles/excerpts. Long source texts and candidate descriptions were reviewed as excerpts, not as a complete audit of every linked original JIRA discussion. A useful lead must share a concrete subsystem, API, test family or engineering migration; generic Spark/version overlap alone is insufficient. Specific title-only migration analogues can count as contextual leads, but cannot establish diagnosis. Relevant non-self IDs were not labeled before the run, so there is no predeclared retrieval-relevance score. The 10/20 result is explicitly a subjective post-run judgment.

## Concrete failures

- **R04, MLflow/Pandas:** the report concerns feature-name mismatch. Scheduler/Shuffle mentions in its stack trace make the policy choose a broad component boundary. The prewritten action enum allowed a boundary check, but the actual component choices fail closer review. This explains 7/20 enum agreement versus 6/20 acceptable actions.
- **R03, Thrift Server:** the source names a missing BouncyCastle provider. Generic ORC/Hive/Scheduler relationships obscure the more useful dependency/classpath investigation.
- **R06?R10, sparse sources:** the policy proposes environment checks even when descriptions are absent or repeat the title. All eight predeclared clarification cases fail immediate abstention.
- **R18, usage logging:** unrelated search hits do not help investigate staticmethod logger attachment. The generic environment action misses the described boundary.

Useful examples include Kafka micro-batch test-family leads (R01), streaming temp-view/session context (R05), ANSI configuration checks (R11), and session-lifecycle test failures (R14). These are leads for a reviewer, not verified fixes.

## What this establishes

The graph connects inspectable evidence and remembers reviews that can change the next action. This assessment does not establish better accuracy or speed than a baseline, autonomous remediation, or independent real-case correctness. The separate 24/24 synthetic benchmark checks authored policy scenarios only.

Priorities suggested by the failures: ask for missing evidence before generic actions; distinguish maintenance requests from incidents; reduce incidental stack-trace component influence. Preserve this baseline and use a new frozen sample for any later quality claim.

## Inspect the cases and reproduce

Read [review_packet.md](review_packet.md) for all 20 source reports, [labels.csv](labels.csv) for prewritten judgments, [post_review_graph.csv](post_review_graph.csv) for per-case assessments, and [summary.json](summary.json) for raw counts. `python real_evaluation.py summarize` recalculates the summary. Prediction overwrites are refused; keep the original run intact.

Dataset: GitBugs / Apache Spark, Avinash Patil, CC BY 4.0. Provenance and transformations: [DATASETS.md](../../DATASETS.md). Human independent review remains pending.
