# Explaining CaseRoute to judges

CaseRoute helps a support/engineering reviewer investigate a reported symptom, inspect connected historical evidence, select a bounded next step, and remember what has already been checked.

The real workflow stores historical issues, affected versions, source provenance, rule-extracted component mentions, reviewer notes and saved investigation runs in FalkorDB. Queries follow an issue through a version or component to other issues, then read previous reviews before selecting the next step. Removing FalkorDB removes the evidence/memory tools; the app has no local owner-map fallback.

The agent has a deterministic graph-policy mode and an optional two-stage AnyAPI mode. The model extracts a search plan, then chooses an allowed step from the graph evidence. The server validates IDs, versions and prerequisites. It renders factual text from source fields rather than trusting a generated diagnosis. A saved negative/insufficient review overrides a repeated lead with a request for more details.

The graph visualizer renders stored nodes/edges. A saved decision property is projected as a labeled final-action node with dashed evidence-use links. Those visual links are distinct from source relationships. Mention extraction records exact matched text, field, excerpt and rule version; a mention or shared version does not prove dependency, duplication or cause.

The demo's next step is a human investigation action, not an executed production repair. The separate synthetic lab shows ownership-edge changes, failed-check exclusion and hypothetical impact traversal using fictional teams/runbooks. No company ownership is invented for Spark.

Validation includes a fresh isolated Python environment, a fresh full graph import, reload/memory checks, source-count checks and browser acceptance. Three real case studies preserve limitations. The frozen 20-case study has AI-assisted prelabels and judgments: 7/20 prelabel action agreement, 6/20 post-review acceptable actions and 0/8 required clarifications. The implementation-informed review is not independent validation; synthetic policy results are not a real-world accuracy claim.

AI-use disclosure: OpenAI Codex assisted with implementation, tests, documentation and demo automation. Participants must review the code and be able to explain these decisions themselves. Do not claim novelty for graph ticket routing generally, verified root causes, production deployment, independent evaluation before it exists, or a guaranteed prize.
