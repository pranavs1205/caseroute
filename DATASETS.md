# Real data used by CaseRoute

## Selected: GitBugs / Apache Spark

- Publisher: **Avinash Patil**, [GitBugs repository](https://github.com/av9ash/gitbugs).
- Research: [GitBugs: Bug Reports for Duplicate Detection, Retrieval Augmented Generation, Triage, and More](https://arxiv.org/abs/2504.09651), 2025. This is an arXiv preprint; no ICML or IEEE acceptance is claimed.
- Publisher-declared license: **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**. This attribution and the transformation notes should accompany redistributed subsets.
- Pinned revision: `eadf2d6794990a1aaa26d0ae15391f29f8969301`.
- [Source CSV](https://raw.githubusercontent.com/av9ash/gitbugs/eadf2d6794990a1aaa26d0ae15391f29f8969301/spark/spark_bugs.csv): **18,665,594 bytes (18.67 MB)**, **20,275 rows**. No full-repository download is needed.
- SHA-256: `34c18f07ab9877dfe15471d8356eb017b7658a87f0e1a20bf60043659ff1af02`.
- Import result: **20,275 HistoricalIssue nodes**, **68 Version nodes**, one Apache Spark project and a dataset provenance node. Counts and outcomes are in [data/manifest.json](data/manifest.json).

The CSV includes genuine historical reports with summaries, descriptions, numeric internal JIRA IDs, status, priority, recorded resolution, original dates and affected versions. It does **not** contain service ownership, runbooks, confirmed root causes, duplicate target IDs or executable fix procedures. The publisher README's displayed duplicate count differs from the actual CSV; CaseRoute's counts are computed from the downloaded file, not copied from the README.

## Reproduce the import

Start FalkorDB, activate the project Python environment, then:

```powershell
python import_real_data.py
```

The downloader pins a revision, checks exact size and SHA-256, and refuses downloads above 25 MB. It stores the raw CSV in ignored `data/raw/`, then imports in batches of 200 records. Repeated imports merge records by ID and preserve app reviews/runs. The tracked manifest is a provenance receipt; the raw CSV is not committed.

Transformations: split comma-separated affected versions into graph nodes; keep source dates as text because their timezone is unspecified; retain row numbers and source revision; construct JIRA links using numeric internal IDs (not fabricated SPARK ticket keys). Raw issue text is displayed as escaped text and never executed. No ownership, fix, dependency or duplicate-target relationship is inferred. This is a static historical snapshot, not a live issue feed. Source links can be unavailable even when the pinned CSV remains accessible.

**Component enrichment:** `components.py` adds 13,909 `MENTIONS` links to 16 software-component nodes. Deterministic word-boundary rules recognize explicit names/terms in titles or descriptions, with a supporting excerpt, exact match, source field and `component-mentions-v1` rule version on each edge. These derived links assert text mentions, not component ownership, service dependencies, cause or a verified fix. Original CSV fields and outcomes are preserved. The full issue projection has 20,361 nodes and 74,803 edges, including project/source hierarchy links. Dataset attribution remains available in this document and source details; the requested homepage paragraph was removed.

## Real workflow

1. Search genuine reports by symptom, optionally filtering by an affected Spark version.
2. Inspect a candidate's source description, recorded outcome and CSV provenance.
3. Traverse `HistoricalIssue → AFFECTS → Version ← AFFECTS ← HistoricalIssue` for version context beyond the selected report's text.
4. Choose a bounded human review step: check the current environment, inspect the original recorded resolution, or request more details.
5. Record an applicability review in FalkorDB. A previous `not_applicable` or `needs_more_info` review forces a subsequent investigation to request additional evidence rather than repeat the lead.
6. Save and reopen the actual query/model-call trace through `InvestigationRun` nodes.

```text
HistoricalIssue -SOURCED_FROM-> Dataset
HistoricalIssue -IN_PROJECT-> Project
HistoricalIssue -AFFECTS-> Version -VERSION_OF-> Project
Review -BASED_ON-> HistoricalIssue
InvestigationRun -EXAMINED-> HistoricalIssue
```

Shared affected versions are context, **not** proof that issues are duplicates, share a cause, or affect the current customer. App reviews never overwrite historical source outcomes. The fictional checkout-company ownership lab remains clearly labeled synthetic.

## Alternatives explored

| Candidate | What it offers | Decision |
| --- | --- | --- |
| [GHPR](https://github.com/soroushj/ghpr-dataset) | Real linked GitHub issues and fixing PRs; repository reports 14,384 instances; full CSV shown as 49.7 MB. | Good later option for stronger fix provenance. Not imported; redistribution terms need review. |
| [Kaggle Customer IT Support tickets](https://www.kaggle.com/dsv/10323677) | Support-email text, answers, priorities and queues. | Publisher explicitly says synthetically generated; does not meet the real-data request. |
| GitBugs / Apache Spark | Real reports and version relationships, research citation, publisher-declared CC BY 4.0, 18.67 MB CSV. | Selected and imported. |

## LLM role and verification limits

Graph-only mode is deterministic. Optional LLM mode makes two actual model calls: extract a search plan, then select an allowed next review step and cite supplied issue IDs after reading graph evidence. Model-generated Cypher is never executed. Foreign citations and invented versions are rejected; Python/runtime versions cannot silently become Spark-version filters. Factual explanation text is rendered from source fields, not free-form model diagnoses.

The selected provider is now **AnyAPI**, using an exact authenticated catalog ID recorded in `llm_config.json`. The Nemotron model passed a minimal smoke test and two real investigation calls through the browser. Its JSON is validated on the server; no native structured-output support is assumed for every routed model. Earlier development used the already-installed local `qwen2.5:0.5b`; its initial free-text draft combined unrelated report details, so the accepted schema excludes free-form diagnosis. No new local model was downloaded. These real reports have **not** been used to establish a validated accuracy score; the older 24-scenario evaluation is explicitly synthetic and separate.

## Public GitHub pilot (18 October 2026)

A separate `caseroute_github` graph imports bounded public records from getzep/graphiti through GitHub API reads and a commit-pinned partial Python AST index. Source URLs, checked/updated times and code commit are retained. Repository metadata reports Apache-2.0 for code; no blanket license is asserted for issue comments. Raw imports are not committed; verification receipts contain bounded metadata and references. Optional LLM review sends bounded report/evidence excerpts to the configured provider. See [GITHUB_PILOT.md](GITHUB_PILOT.md). The original Spark dataset and frozen 20-case assessment are unchanged.
