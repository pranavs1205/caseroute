# Add repositories and import all available issue pages

CaseRoute now supports user-added **public GitHub repositories**, with no hardcoded one- or two-repository allowlist. Add a repository using `owner/name` or an HTTPS GitHub repository URL. No code/configuration edit is needed for each new repository.

This is a local shared workspace. Graph separation prevents accidental mixing of repository evidence and case memory; it is not per-user authentication or a hosted tenant-permissions system. Private repository onboarding is rejected in this version.

## Use the workspace

Open http://localhost:8010 and select **GitHub repos**.

1. Enter a public repository URL under **Connect a public repository** and click **Add repository**.
2. Select the connected repository. Its issues, new investigations, saved observations and code evidence are scoped to that repository.
3. Click **Import all issue pages / resume**. The browser requests batches until GitHub pagination ends. Use **Pause after current batch** to stop; the next import resumes from the saved cursor.
4. Use **Refresh all issues from page one** for a new traversal after updates. A completed old import is explicitly timestamped; it does not claim knowledge of later GitHub changes.
5. Search locally, use a direct issue number/URL, or explicitly enable live search for the selected repository. Cached result pages can be browsed beyond the first 30 hits.
6. Enable **Search cached issues across all connected repositories** for a workspace preview. Results retain repository identity; opening a result switches to its own repository before investigation. The preview returns up to 30 hits per repository; select that repository to paginate further. Global live GitHub search is not performed automatically.
7. Open an existing report or create a new local investigation. New reports do not become source issues. Observations persist and rejected leads require more evidence.

## All issues means pagination, not a search sample

Backfill uses `GET /repos/{owner}/{repo}/issues` with `state=all`, creation-order pagination and 100 records per page. Pull requests are excluded by their `pull_request` field. The next request is constructed for the selected repository; arbitrary pagination URLs are never followed.

The cursor advances only after a page has been ingested and its derived signal degrees updated. Each API batch reads up to two pages by default (configurable to five), but **there is no total page limit**. The UI/CLI continues batches to the end. Network/rate-limit failures leave the cursor available for retry, and replayed pages upsert the same issue IDs.

The UI distinguishes **import incomplete** from **all issue pages read**. This means pagination was exhausted during that traversal, not a transactionally consistent snapshot of GitHub. GitHub edits/deletions during pagination, API access limits and later new issues require refresh. Source bodies remain capped at 12,000 characters; comments are fetched separately (first ten on explicit refresh). Importing all issue records does not mean importing every comment or entire issue body.

[GitHub documents repository issues](https://docs.github.com/en/rest/issues/issues#list-repository-issues) and [pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api). Bulk ingestion no longer relies on search API results or its result cap.

## Graph separation and code coverage

`RepositoryRegistry` stores connected repository metadata in a persistent catalog. Each repository maps to its own FalkorDB graph using a stable normalized-ID hash. Existing Graphiti records remain in `caseroute_github`; its old investigations are preserved. IDs and technical signals include repository identity.

The graph tools and optional one-call LLM review operate inside the selected graph. Cached cross-repository search reads graphs independently and retains provenance; it does not silently treat shared names from different projects as the same component.

Issue ingestion works independently of implementation language. Optional code analysis currently supports Python AST declarations and ambiguous call-name leads, with a generic repository-layout selector rather than Graphiti-specific paths. Code indexing remains a **partial sample of up to 16 eligible Python files**, capped at 3 MB per snapshot and pinned to a commit. A JavaScript/Java/C++ repository can use issue search and investigations, but does not gain full code understanding from this Python index. No repository code or tests are executed, and no fixes/PRs are published.

## Observed live coverage ? 18 October 2026

| Repository | Imported issue records | API pages exhausted |
| --- | ---: | ---: |
| getzep/graphiti | 597 | 20 |
| falkordb/graphrag-sdk | 95 | 4 |
| pranavs1205/caseroute | 0 | 1 |

The underlying API pages also contain pull requests, explaining why 20 pages can yield fewer than 2,000 issue records. These counts describe the verified local traversal and may change on a future refresh. [Coverage receipt](submission/verification/repository-coverage.json).

A real browser check adds GraphRAG-SDK as a third repository, finishes its import, switches repositories and searches cached evidence across them. Tests cover idempotent onboarding, same-number issue isolation, case-memory separation, rejecting private/foreign repositories, retry after a simulated rate limit, cursor completion/reset and local search pagination. The original Graphiti issue-to-code/reload flow remains a separate regression gate. No new diagnosis-accuracy claim is made.

## CLI and API

```powershell
python github_pilot.py add https://github.com/owner/repository
python github_pilot.py list
python github_pilot.py sync --repo owner/repository --issues-only --all
python github_pilot.py sync --repo owner/repository --issues-only --all --restart
python github_pilot.py search keyword --repo owner/repository
```

Omit `--issues-only` to include the partial Python snapshot on the first batch. Subsequent batches import issues only. CLI receipts accumulate calls from all batches in the invocation. The earlier single-pilot receipts remain historical artifacts.

API additions: `GET/POST /api/repos`, `POST /api/repos/search`. Scoped existing routes accept `?repository=owner/repository`; missing selection defaults to Graphiti for compatibility. `POST /api/repo/sync` accepts `include_code`, `max_pages`, `restart`. `POST /api/repo/search` accepts `offset` for cached pagination.

No LLM calls occur during onboarding, issue ingestion, cached/live GitHub search, or graph-only investigation. Registration makes one metadata request. Each issue batch makes one metadata request plus one per issue page; a Python snapshot adds commit/tree/blob requests. GitHub credentials remain optional for public reads but affect rate limits. Existing environment token or authenticated `gh` session support is retained.

For a future hosted multi-user product, add GitHub App installation, user/repository authorization, background sync jobs and webhooks. The current change provides self-service public repository onboarding in the local app, not that hosted permission system.
