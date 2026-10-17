# CaseRoute

A local investigation agent with FalkorDB as its context and memory layer. Built for **Track 01: Agents That Act on Connected Data**. The real-data workflow uses **20,275 historical Apache Spark reports** from GitBugs (18.67 MB CSV, CC BY 4.0). The separate checkout-company ownership lab remains fictional.

## Run

Requires Python 3.11+ and Docker Desktop (Linux containers).

```powershell
docker compose up -d
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python seed.py
python import_real_data.py
python -m uvicorn app:app --host 127.0.0.1 --port 8010
```

Open http://localhost:8010. FalkorDB Browser is at http://localhost:3001. API docs: http://localhost:8010/docs. The graph uses host port 6380 to avoid other local Redis instances.

The graph volume preserves records across container restarts. Seeding is idempotent and preserves attempts and edited ownership. `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_PASSWORD`, and `FALKORDB_GRAPH` configure the connection. Do not expose this prototype to the public internet: it has no user authentication and includes a demo ownership editor.

## Real data and Graph journey

The homepage includes an interactive **Connected issue landscape**. **Investigation map** shows a selected issue's component mentions, affected versions, related reports, source/project, saved reviews and (after a run) the final action. Click nodes to inspect source excerpts, search by issue ID/title, pan/zoom, or expand the canvas. Stage selection highlights the relevant relationship types. Decision nodes visualize the saved run's decision property; their dashed evidence links are visibly distinguished from stored source relationships.

**Entire issue graph** includes all **20,275 real issues, 20,361 total nodes and 74,803 links** in the real issue projection. Counts are validated against independent graph counts. Collection queries bypass FalkorDB's per-row result cap. This view excludes the fictional lab and historical run records; its layout uses component mentions as visual anchors, not an inferred dependency topology. Whole-corpus loads are cached in the browser during the page session.

Three real complex-case shortcuts include a Kafka → streaming DataFrame report mentioning **Kafka, PySpark, Spark SQL/DataFrames and Streaming**, plus Spark Connect/Python/SQL examples. These are source-backed `MENTIONS` edges with excerpts and a versioned extraction rule. They are not assertions of verified dependencies or root causes. The agent reads component intersections and can select an `investigate_component_boundary` action; it does not claim to have applied a fix. Fresh imports run this enrichment automatically. Existing imports can run `python components.py`.

The homepage now shows **Graph journey**. Run a report through source search, affected-version traversal, related-report lookup, prior-review recall and a saved next-step decision. Click each stage for actual Cypher, parameters, bounded result previews and execution timing. Replay highlights completed stages; it does not simulate a live model thought process.

**Real case library** lets you search genuine reports, inspect source descriptions and recorded outcomes, follow version relationships, then save a human applicability review. A rejected or insufficient historical lead makes later investigations request additional details. Source records and app reviews are stored separately.

Data attribution: **GitBugs / Apache Spark**, Avinash Patil, [GitBugs repository](https://github.com/av9ash/gitbugs), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), [2025 paper](https://arxiv.org/abs/2504.09651). See [DATASETS.md](DATASETS.md) and [data/manifest.json](data/manifest.json) for revision, checksum, transformations, limitations and alternatives considered. No owner or fix procedure is invented for real issues.

## LLM mode

Graph-only mode makes no model calls. Checking **Use LLM planning and next-step selection** makes two calls: interpret the report into a search plan, then choose a bounded review step from the returned graph evidence. Evidence IDs are constrained to supplied records and checked server-side. Factual UI text comes from source records rather than free-form generated diagnoses. The graph still controls evidence, memory and permissible actions.

**AnyAPI is the selected provider**, as requested. Its exact model ID is recorded in `llm_config.json` after authenticated model discovery. Put `ANYAPI_API_KEY` (or `ANY_API_KEY`) in the ignored local `.env` or environment; never paste it into chat or commit it. The parser reads only named settings without executing or interpolating file contents. `ANYAPI_MODEL` / `CASE_LLM_MODEL` override the chosen model; `CASE_LLM_PROVIDER` overrides the provider. Only enabling LLM mode sends bounded report and graph evidence to the configured provider.

The integration uses `https://api.anyapi.ai/v1/chat/completions` with **model + messages only**, matching the provided smoke test. JSON output is schema-validated server-side; schema enforcement by every AnyAPI model is not assumed. Provider errors are reported without silently switching to another provider. Receipts include the requested/returned model, usage and validated output, never credentials. The selected model passed the minimal live smoke test; current end-to-end status is in `VERIFICATION.md`.

```powershell
python anyapi_smoke.py --list-models
python anyapi_smoke.py nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
```

Ollama remains an explicit optional override (`CASE_LLM_PROVIDER=ollama`, `CASE_LLM_MODEL` set to an installed model). Earlier development checks used the existing `qwen2.5:0.5b` model; no model download was made. The alternative Vercel gateway adapter remains available but untested. `.env.example` lists the supported settings.

## Two-minute demo

1. Choose **Discount codes**, submit the sample report. Follow case → feature → Pricing API → Commerce Engineering. Inspect RUN-101 and the past resolution.
2. Record **Check failed**, with “Cache and price-book versions match.” The next check becomes discount eligibility. Restart the API, reopen the saved case and show the stored attempt.
3. Preview **Pricing API** in Impact explorer. Show direct discount impact and Campaigns → Checkout → Pricing API reachability. This does not mutate the graph.
4. Open **Campaign checkout**. Routing waits until the user selects the failing service.
5. In Ownership lab change Pricing API to Platform Reliability. Reopen the discount case; the handoff team changes. Restore Commerce Engineering afterward.

## Agent and graph model

The synthetic ownership lab uses a deterministic investigation policy, with no LLM or paid API requirement. Its tools resolve ownership, read case memory, find source-backed actions and rank untried actions using past resolutions and documented priority. The report is retained for the handoff; feature identification in this lab is a human input. The real-data journey has optional LLM planning as described above. No tool executes remediation or sends messages.

```text
Case -ABOUT-> Feature -DEPENDS_ON-> Service -OWNED_BY-> Team
Service -DEPENDS_ON-> Service
Action -FOR_SERVICE-> Service
Action -SUPPORTED_BY-> Document
ResolvedCase -ABOUT-> Feature
ResolvedCase -FIXED_BY-> Action
Case -TRIED {outcome, note, at}-> Action
```

The graph directly controls the team and available check. There is no in-memory routing fallback. A missing graph produces an explicit error. All Cypher is in `graph.py` and `seed.py`; user values are query parameters. Impact is bounded to three service hops and runs with `ro_query`.

## Verify

```powershell
python -m unittest discover -s tests -v
```

Integration tests require live FalkorDB. Each run creates and deletes a uniquely named test graph; the demo graph is preserved. Coverage includes sourced recommendations, memory on a fresh client, ownership mutation, ambiguity, seed idempotence and multi-hop impact. Full process/container restart and browser verification are separate acceptance gates.

`tests/test_real_cases.py` adds isolated graph evidence/memory tests and validates rejection of unsupported model outputs. `tests/test_anyapi.py` checks credential parsing, minimal request compatibility, schema validation, usage receipts and provider errors without network calls. Optional browser acceptance scripts require Playwright/Chromium: `python tests/browser_check.py` for the synthetic lab; `python tests/browser_real_check.py` for real-source workflows and two live calls to the configured provider. The latter records a marked acceptance review on the sample historical issue.

`tests/test_landscape.py` verifies component extraction/provenance, idempotent enrichment, multi-component decisions and full projection counts. `python tests/browser_landscape_check.py` verifies the complex-case canvas, the path into a final action, all-corpus coverage, node search/expansion and mobile layout without making LLM calls.

## Limits and submission status

This is a single-company local prototype. Ownership and recommendation sources older than 90 days (or missing valid dates) produce a review warning. Conflicting ownership blocks routing. Multi-tenant authentication, duplicate clustering, multi-agent coordination and independently held-out evaluation are not implemented. A passed check is recorded as an attempt; it does not automatically resolve a case. A human must interpret the result.

Before submission: complete browser/restart checks, record evaluation against a keyword baseline, capture the demo, publish the repository, and confirm current event rules and deadline. Track 02 and Track 03 are not claimed by this prototype.

Current verification and limits are in `VERIFICATION.md`. Run `python evaluate.py` for the 24-scenario synthetic policy benchmark; results are saved to `evaluation/results.json`. It compares against static feature/service lookup from the same fixture corpus, not an independent held-out language-routing benchmark. Optional browser checks: install Playwright, install Chromium with `python -m playwright install chromium`, run the server, then run `python tests/browser_check.py`.

AI assistance: OpenAI Codex assisted with planning, implementation and tests. Review and amend this disclosure to reflect all team contributions. Third-party dependencies retain their respective licenses; this repository has not yet selected a project license.
