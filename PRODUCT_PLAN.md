# CaseRoute — independent product and execution plan

**Updated 15 October 2026, India time.** CaseRoute is an original support operations product centered on FalkorDB. Its UI, graph schema, traversal tools, decision policy, and case memory are built in this repository. It does not connect to another support platform. Standard third-party dependencies still need normal attribution and accurate AI-assistance disclosure in the final submission.

## Execution update — 16 October 2026

**Landscape extension:** Homepage dataset paragraph removed. Interactive full graph and focused investigation maps are implemented with node/edge evidence inspection, source-backed component mentions, complex-case shortcuts and a visible final-action path. The real projection contains 20,275 issues, 20,361 nodes and 74,803 links. Graph-only multi-component flow, full coverage and mobile layout are browser-verified; 22 backend tests pass. The latest complex-case AnyAPI probe encountered upstream HTTP 502, so its LLM completion remains unverified. See `VERIFICATION.md`.

**Latest update:** Real CSV import, homepage Graph journey, real-case applicability reviews and saved evidence snapshots are implemented and browser-verified. The user selected **AnyAPI**; authenticated model discovery, a minimal Nemotron smoke test and two end-to-end model calls pass. Provider/model configuration is in `llm_config.json`; credentials stay in ignored `.env` or the environment. The backend suite now has **17 passing tests**. Earlier Ollama statements below describe development checks, not the current provider. Real-data agent accuracy remains unmeasured.

The repository initially contained only this plan; its earlier implementation statements were not evidence of files in this workspace. A Python/FastAPI prototype and browser UI have now been implemented here with real FalkorDB queries. Seven live integration tests pass. Browser case, memory, impact and ambiguity checks pass, and failed-check memory survived an API and database-container restart. A 24-scenario synthetic policy benchmark and its limitations are recorded in `evaluation/results.json` and `VERIFICATION.md`.

Local API: http://localhost:8010. Dedicated graph: localhost:6380; FalkorDB Browser: http://localhost:3001. Setup is in `README.md`. Ownership conflict handling and source freshness warnings are implemented. Independent held-out evaluation, demo video, public repository, final licensing and submission remain open. Track 02 coordination and duplicate clustering remain stretch scope. The agent is deterministic; feature selection is human input.

The daily gates below are the original schedule. Use `VERIFICATION.md` for current acceptance evidence and remaining work.

## Problem and user

**Real-data extension (16 Oct):** The homepage is now a Graph journey over 20,275 real historical Apache Spark reports from GitBugs, with 68 affected-version nodes, source provenance, applicability reviews and persisted execution traces. Its CSV is 18.67 MB and publisher-licensed CC BY 4.0. Optional LLM mode interprets the report and selects a constrained review step after graph retrieval; the installed local Ollama model is used for smoke testing. See `DATASETS.md`. The fictional company flow below remains an ownership/impact lab; its teams and runbooks are not presented as facts about Apache Spark.

A support lead at a software company receives “checkout fails when a discount is applied.” A ticket's text alone does not say which service or team owns the failure, what runbook applies, which past case is relevant, or which checks have already failed. CaseRoute creates a sourced handoff by following relationships among a **case, feature, service, owner, document, action and past resolution**. A person reviews the result and performs the check.

The product can serve different companies after importing their own permitted ownership and runbook data. The hackathon demo uses a single fictional company and synthetic data. It is a working prototype, not a proven multi-company deployment.

## Distinctive FalkorDB functions

| Function | User value and graph work | Status / acceptance gate |
| --- | --- | --- |
| **Evidence path handoff** | Case → feature → service → team and documented action → source; explains why a team and check are suggested. | Implemented in code. Live graph check needed; change an `OWNED_BY` edge and observe the answer change. |
| **Attempt-aware next step** | Failed or inconclusive action is stored on the case and filtered on reopening; relevant resolved case raises a documented check. | Implemented in code. Verify restart persistence on a live graph and no repeated action. |
| **What-if impact preview** | Read-only, bounded feature → service → upstream-service traversal lists affected features and cases if a service changes or fails. It also identifies teams to consult. | Implemented in code. Verify direct and two-hop reachability on live FalkorDB; no graph mutation; no claim that an actual outage occurred. |
| **Ownership conflict alert** | A feature spans services owned by several teams; show candidates and hold the handoff until a human chooses the failing service. | Basic ambiguity gate implemented. Next: add source-dated ownership decisions, flag stale/conflicting records. |
| **Graph-guided duplicate cluster** | Group active cases that share a downstream service and symptom, so support can avoid fragmented investigations. | Stretch only after the first three flows pass; require an example where text similarity alone misses the shared service. |

FalkorDB's [bounded variable-length relationship pattern](https://docs.falkordb.com/cypher/match) supports the impact walk. Its [BFS and other graph algorithms](https://docs.falkordb.com/algorithms) are options for larger graphs; this small demo uses bounded Cypher and does not claim an algorithm it has not implemented.

## Product scope and demonstrations

1. **Case flow:** Select feature and paste a synthetic customer report. Show owner, check, source excerpt, previous resolved case, graph path and a human-review handoff draft.
2. **Memory flow:** Record a failed check. Reopen the same case after process restart; display history and choose a different documented action.
3. **Impact flow:** Preview Pricing API disruption. Show directly affected Discount codes plus features that depend on Checkout or Campaigns downstream, and any existing cases to review.
4. **Ambiguity flow:** Campaign checkout spans services with different owners. Do not silently assign a single team; list owner candidates and ask for confirmation.

## Graph model

`Case -ABOUT→ Feature -DEPENDS_ON→ Service -OWNED_BY→ Team`

`Service -DEPENDS_ON→ upstream Service` (bounded to three service hops in previews)

`Action -FOR_SERVICE→ Service`, `Action -SUPPORTED_BY→ Document`, `ResolvedCase -ABOUT→ Feature`, `ResolvedCase -FIXED_BY→ Action`, `Case -TRIED→ Action` (outcome and time)

All paths are derived from FalkorDB queries. The UI does not maintain a separate owner map or cached recommendation. Data includes synthetic source IDs and dates; importing a real company requires consent, privacy controls and provenance review beyond this prototype.

## Remaining daily gates

| Date (IST) | Build and verify | Deliverable |
| --- | --- | --- |
| **15 Oct night** | Run FalkorDB Docker on a capable host; seed graph; check browser case, attempt, impact, ambiguity; fix any query incompatibility. | Recorded results with screenshots or terminal output for four flows. Until this happens, product is unverified end to end. |
| **16 Oct** | Improve UI for clear impact paths; add graph edit or controlled fixture demonstrating owner-change effect; inspect error states and source freshness. | One complete two-minute demo without manual data edits during the recording. |
| **17 Oct** | Create 20–25 synthetic held-out scenarios; compare against simple keyword/text routing with same source corpus; report accuracy and failures. Decide if a real two-role handoff is worth Track 02. | Evaluation counts, misses, latency, graph removal check. |
| **18 Oct** | Freeze features, clean setup, public repository, video, README/model/Cypher, AI-use disclosure, submission by **11:59 PM IST**. | Reproducible local installation, selected track evidence and submitted entry. |

## Track choice

- **01 Agents That Act on Connected Data — primary:** graph-based multi-hop investigation, documented action selection, counterfactual impact preview, explainable result.
- **03 Company Brain — conditional:** only enter if owner knowledge, runbooks, case decisions, update history and sources form a convincing company workflow in the finished demo.
- **02 Agent Memory and Coordination — conditional:** persisted attempts alone are insufficient for the strongest claim; add a second role/agent handoff and isolation if time permits.

The event [allows one entry in multiple tracks](https://www.wemakedevs.org/hackathons/falkordb), but every selected track should be demonstrated. The [rules](https://www.wemakedevs.org/hackathons/falkordb/rules) require FalkorDB central, permitted data, public repository, setup/model/Cypher, demo video, track names and AI-use disclosure. Do not assert a prize or hiring outcome.

## Build resources and risks

- Required: Docker-capable machine, Python 3.11+, FalkorDB, public Git host, screen capture. No model API is required for the current deterministic agent and human-reviewed drafts.
- Docker is available with local-engine permissions. Live graph and browser checks have now run; see `VERIFICATION.md` for evidence and limits.
- On a service dependency cycle, bound the traversal to three hops and deduplicate results. Validate on realistic examples before increasing depth.
- Seed and demo only synthetic data. Never use private company tickets or personal customer data in a public submission.
