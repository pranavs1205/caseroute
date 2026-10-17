# CaseRoute: 165-second captioned demo

[Public demo recording](https://github.com/pranavs1205/caseroute/releases/download/demo-v1/caseroute-demo.webm) ? [Release](https://github.com/pranavs1205/caseroute/releases/tag/demo-v1) ? [Passed recording receipt](verification/demo-receipt.json)

The final WebM decodes in Chromium at 1440?900, 164.52 seconds. Wall-clock interaction capture: 165.02 seconds.

Pitch: **An evidence-grounded investigation workflow that remembers what reviewers checked.**

Track: **01 — Agents That Act on Connected Data**. The main recording uses the actual graph-only agent policy and explicitly labels it. It does not simulate successful model calls. Optional AnyAPI calls are a separate capability; their provider errors remain visible.

| Time | Working behavior shown |
| --- | --- |
| 0–12 s | Product and real corpus. State the user problem: support needs a sourced next step, not another plausible guess. |
| 12–39 s | Four-component Kafka/PySpark/DataFrame/Streaming case. Inspect a MENTIONS edge and its source excerpt; explain the two-hop issue → component ← issue walk. |
| 39–55 s | Open actual source description and link. Its recorded outcome is Invalid; do not claim a proven fix. |
| 55–89 s | Agent proposes a boundary reproduction. Show executed Cypher, returned evidence, and the final-action path. |
| 89–108 s | Save a clearly marked demonstration review requesting the current environment and reproduction details. |
| 108–125 s | Reload and show the persisted review. Source outcome remains separate. |
| 125–143 s | Re-run: the graph memory changes the next action to request_details. |
| 143–153 s | Briefly show the separate synthetic ownership lab, explicitly labeled fictional. |
| 153–165 s | Close with evidence → bounded action → persistent memory and the public repository. |

Re-record: `python record_demo.py` with Playwright/Chromium and FalkorDB running. It imports into a generated isolated graph, captures real browser interactions, verifies the changed decision and reload, and deletes only its own graph on completion. The user's graph is untouched. The result is a captioned, silent WebM under ignored `artifacts/`; a successful receipt records duration and assertions. No private keys, terminal credentials or user desktop are recorded.

Case studies: [multi-component](../case_studies/multi-component.md), [straightforward](../case_studies/straightforward.md), [insufficient source](../case_studies/insufficient-source.md). Their human assessments remain pending. The 20-case reviewer study is separate and frozen before predictions.
