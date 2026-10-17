# CaseRoute verification — 16 October 2026, IST

## GitHub pilot gate ? 18 October 2026

The separate Graphiti pilot imported 30 public issues and a balanced 16/236-file Python snapshot at commit `a107b622205733c0a53617ce0cd79fe4461cdb35`, 382,760 downloaded code bytes, 20 GitHub GET requests and no model calls for sync. The original Spark graph/evaluation remain separate.

All 36 existing backend checks and all 11 repository-pilot checks pass (47 total). Browser verification passes real issue #2014 to SearchResults.merge, self exclusion, new-report local retrieval, saved rejection/reload, HTTP 409 stale-write rejection and mobile layout without horizontal overflow. One live AnyAPI repository review passes one model call; it requests details and cites an allowed issue. No GitHub writes, code execution, tested patch or fix-quality score is claimed.

See [pilot documentation](GITHUB_PILOT.md), [sync receipt](submission/verification/github-sync.json), [browser receipt](submission/verification/github-browser.json) and [LLM receipt](submission/verification/github-llm-smoke.json). Old public video predates this extension.

## Graph-guidance gate ? 18 October, after the frozen baseline

Technical identifier enrichment added 75,232 excerpt-supported edges and 33,168 identifier nodes. Degree-discounted two-hop retrieval, primary-component checks, report-type and sufficiency gates are implemented. All 36 backend tests pass. Browser and fresh full-import checks pass; one live AnyAPI run passed two bounded calls with a permitted action. [Detailed analysis](GRAPH_IMPROVEMENTS.md) and [setup receipt](submission/verification/guidance-setup-check.json).

Development replays are separate: v2 16/20 action agreement and 6/8 required clarification; v3 18/20 and 7/8. This is in-sample development after inspecting failures, not independent validation or new retrieval quality. Original baseline artifacts are unchanged. The existing public video is the preceding release snapshot.

## Submission evidence gate ? 18 October

- Fresh Windows Python 3.11.5 virtual environment installed from `requirements.lock`; `pip check` passed. Docker 29.8.2 and pinned FalkorDB image used.
- `acceptance.py` passed a full fresh CSV import/enrichment, source counts, persistent memory from a new client, changed real-case decision, saved-run reload and full projection validation. Its uniquely named graph was deleted; the normal graph was preserved. [Receipt](submission/verification/setup-check.json). Full projection query: 5941.98 ms locally, not a comparative speedup.
- All **26 backend tests passed** in that clean virtual environment, including four assessment-integrity tests. Functional success is separate from recommendation quality.
- [Three actual case studies](case_studies/) captured with marked reviews and fresh-client reload. The insufficient-source case preserves an initial inappropriate generic action.
- [Twenty real-report AI-assisted baseline](evaluation/real/REPORT.md): 7/20 prelabel agreement, 6/20 post-review acceptable actions, 10/20 useful non-self search hits, 0/8 required clarifications. No independent human, held-out new-issue or LLM quality claim.
- [Working captioned demo](https://github.com/pranavs1205/caseroute/releases/download/demo-v1/caseroute-demo.webm) passed real source, executed query, saved review, reload and changed-decision assertions. Chromium decoded the 164.52-second 1440?900 WebM without error. [Receipt](submission/verification/demo-receipt.json).
- Public repository: https://github.com/pranavs1205/caseroute. Main demo is graph-only; previous AnyAPI success and subsequent upstream 502 remain separate smoke-test evidence.

Earlier entries below are historical development checks; the 26-test count above supersedes their smaller totals. The decision policy was not tuned against this frozen real-case set.

The workspace initially contained only PRODUCT_PLAN.md. The prototype was built and tested against a real local FalkorDB instance during this session.

## Real-data and LLM extension

**Interactive landscape update:** Removed the requested homepage dataset paragraph and placed remaining provenance under collapsed source details. Added a canvas viewer with pan, zoom, fit, full-screen, node search, node/edge inspection and source excerpts. The complete real-issue projection contains **20,275 issues, 20,361 nodes, 74,803 links**, with independent count validation. An initial naive query was truncated by FalkorDB's result-set cap; the final collection-query implementation bypasses that cap. A tested full load took **6,786.97 ms** on this local machine (not a database-comparison speedup claim); the default focused four-component map loaded in about **734 ms** in the recorded browser run. Timings are backend projection times and exclude canvas rendering.

Added 13,909 rule-extracted component mentions across 16 component nodes, each with exact match, source field, excerpt and extraction-rule version. Three complex-case shortcuts use real reports. For `spark-13289604`, four components are linked from the title: Kafka, Python/PySpark, SQL/DataFrames and Streaming. The graph policy reads component-intersection leads and chooses a boundary-reproduction step. This source's recorded outcome is Invalid; no verified fix is fabricated. The canvas adds final-decision visualization from saved run properties with dashed evidence-use links, distinct from stored source relationships.

**22 backend tests pass** after adding component/projection tests. `tests/browser_landscape_check.py` passed paragraph removal, complex-case paths, inspected source evidence, the saved final-action path, all 20,275 issues / 74,803 links, zoom/search/expand and mobile width. Screenshots: `artifacts/complex-issue-landscape.png`, `artifacts/graph-to-final-action.png`, `artifacts/full-issue-corpus.png`, `artifacts/landscape-mobile.png`. Summary: `artifacts/landscape-check.json`. The browser landscape check itself uses graph-only mode.

The additional complex-case AnyAPI probe could not complete: the endpoint reported **HTTP 502** through the application's explicit 503 provider-error response. It did not switch providers or claim a successful saved LLM run. Earlier AnyAPI end-to-end success below remains valid historical evidence, but the new complex-case LLM path is not currently live-verified. The graph-only complex-case workflow is verified.

**Final provider update:** User selected **AnyAPI**. The key is loaded from the ignored local `.env` or environment (`ANYAPI_API_KEY` / `ANY_API_KEY`), without printing or executing credential contents. Authenticated `/v1/models` succeeded. The listed Gemma model returned HTTP 429 and the listed Qwen model returned HTTP 403; the listed **`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`** model passed the exact minimal smoke test and is selected in `llm_config.json`.

**Current checks: 17 backend tests pass.** Four AnyAPI checks cover safe dotenv parsing, minimal `model` + `messages` compatibility, validated usage receipts, malformed model output and explicit provider failures without credential echo or fallback. The complete real-data browser suite then passed with **two actual AnyAPI calls**, graph evidence, saved applicability review, decision/evidence snapshot equality after reloading the run, trace replay and phone-width layout. The latest `artifacts/live-llm-check.json` and screenshots now reflect AnyAPI. The Ollama results below are earlier development evidence, not the selected provider. No new local model was downloaded. No model-quality score is claimed.

The homepage is now **Graph journey**, with a **Real case library** alongside the synthetic lab. Imported GitBugs / Apache Spark CSV: **18,665,594 bytes**, **20,275 real historical reports**, **68 affected versions**. Dataset revision, SHA-256, attribution, license and transformations are recorded in `DATASETS.md` and `data/manifest.json`.

The original **13 graph/policy tests** pass, including source/version traversal, persistent review memory, rejection of foreign LLM citations and invented versions, and no unvalidated diagnosis field. The test graphs use tiny isolated schema fixtures; the browser acceptance checks use the actual imported real corpus. With the four AnyAPI checks, the current total is **17**.

`python tests/browser_real_check.py` passed real corpus counts, source search/inspection, actual executed Cypher trace and replay, saved reviews across reload, two live local Ollama calls and mobile layout. Screenshots are in ignored `artifacts/graph-journey-home.png`, `artifacts/graph-journey-trace.png`, `artifacts/real-case-evidence.png`, `artifacts/llm-graph-journey.png`, and `artifacts/real-mobile.png`. `artifacts/live-llm-check.json` records the live response and model usage. The journey displays execution receipts, not private model thoughts or simulated live stages.

Both actual LLM calls used the already-installed `qwen2.5:0.5b` through local Ollama. No model download or paid cloud request was made. An initial free-text output blended unrelated reports; free-form diagnosis was removed from the accepted schema. A later citation outside the supplied evidence was correctly rejected, then evidence IDs were constrained with a per-request enum plus server-side checks. The accepted workflow lets the LLM select a review step while source fields generate factual UI copy. This small model is a smoke-test choice; quality/accuracy on real reports remains unmeasured. Cloud gateway configuration is implemented but not live-tested.

The historical dataset lacks ownership, runbooks, verified fix procedures and service dependencies. Those fields are not fabricated. The earlier synthetic benchmark remains a separate test and is not an accuracy result for the real-data workflow.

## Verified

- Live graph: source-backed action with a relevant past resolution; failed action excluded on the next investigation.
- Case memory: failed attempt and next recommendation survived restarting both the API process and CaseRoute database container, then were read through HTTP.
- Ownership mutation: changing the graph edge changes the handoff team; conflicting ownership holds routing.
- Ambiguity: Campaign checkout waits for a failing-service selection before recommending a check.
- Impact: Pricing API reaches Discount codes directly, and Campaigns through Checkout; preview uses read-only queries.
- Browser: case creation, failed attempt, reopen, impact, ambiguity selection, mobile width and no uncaught JavaScript errors. Screenshots are in local ignored `artifacts/`.
- Idempotent seed preserves memory and edited ownership.
- Source freshness: older than 90 days or invalid dates produce review warnings.
- Exhausted checks and missing ownership do not invent a handoff.

## Benchmark

`evaluation/results.json` records 24 authored scenarios across six policy conditions. Initial run: graph policy **24/24**, static lookup **12/24**; median investigation **53.91 ms**, maximum **127.60 ms** on this machine. Timing excludes case creation and browser/network rendering.

This is a synthetic policy benchmark authored alongside implementation. Feature and optional service are supplied by a human. The static baseline has initial ownership and runbooks but no updates or attempt memory. These numbers do not establish general language understanding, production accuracy, database superiority or load capacity. An independently authored held-out evaluation remains open.

## Local environment

- API: http://localhost:8010
- Dedicated container: `caseroute-graph`; graph `caseroute`
- FalkorDB: localhost:6380; Browser: http://localhost:3001
- Persistent volume: `caseroute-data`; append-only persistence enabled
- Python dependencies installed only into workspace `.deps/`; `run.ps1` supports this setup. Clean installations should use `.venv` and `requirements.lock`.
- Another existing project's port 6379 and container were left untouched.

## Remaining submission work

- Independent held-out scenarios and failure analysis; stronger baseline with equivalent update/memory access.
- Actual demo video, screenshots selected for submission, public Git repository and final license choice.
- Confirm current hackathon rules, deadline and track requirements against official sources before submission.
- No public deployment, external messages or hackathon submission has been made.
- Track 02 coordination/isolation and duplicate clustering remain stretch scope. The synthetic lab is deterministic; the real-data journey has optional LLM planning and step selection. There is no MCP server, automatic feature selection for the fictional company, or remediation execution.
