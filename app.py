from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from redis.exceptions import RedisError
from graph import Store
from real_cases import RealCases
from landscape import Landscape
from llm import LLMUnavailable, configuration, investigate as run_investigation
import os
from github_client import GitHubUnavailable, REPOSITORY
from repo_pilot import RevisionConflict
from repositories import RepositoryRegistry

app = FastAPI(title='CaseRoute', description='Graph-guided investigations with sourced real historical reports and a synthetic ownership lab')
store = Store()
real = RealCases(store)
landscape = Landscape(real)
repository_registry = RepositoryRegistry()


@app.exception_handler(RevisionConflict)
async def repo_conflict(request, exc):
    return JSONResponse(status_code=409, content={'detail':str(exc)})


@app.exception_handler(GitHubUnavailable)
async def github_error(request, exc):
    return JSONResponse(status_code=503, content={'detail':str(exc)})


class RepoSyncInput(BaseModel):
    include_code: bool = True
    max_pages: int = Field(default=2,ge=1,le=5)
    restart: bool = False


class RepoSearchInput(BaseModel):
    keywords: str = Field(default='', max_length=160)
    live: bool = False
    offset: int = Field(default=0,ge=0)


class RepoIntakeInput(BaseModel):
    title: str = Field(min_length=5,max_length=400)
    body: str = Field(default='',max_length=12000)
    version: str = Field(default='',max_length=80)
    source_number: int | None = Field(default=None,ge=1)


class RepoRunInput(BaseModel):
    use_llm: bool = False


class RepoObservationInput(BaseModel):
    outcome: Literal['needs_more_info','not_applicable','useful_lead']
    note: str = Field(min_length=3,max_length=2000)
    revision: int = Field(ge=0)


class RepositoryInput(BaseModel):
    repository: str = Field(min_length=3,max_length=220)


@app.get('/api/repos')
def repositories():
    return repository_registry.list()


@app.post('/api/repos',status_code=201)
def add_repository(data: RepositoryInput):
    return repository_registry.add(data.repository)


@app.post('/api/repos/search')
def search_repositories(data: RepoSearchInput):
    if data.live:raise ValueError('Cross-repository search uses local evidence. Select a repository for live search.')
    return repository_registry.search_all(data.keywords)


@app.get('/repo.js')
def repo_script():
    return FileResponse(Path(__file__).parent/'static'/'repo.js',media_type='text/javascript')


@app.get('/api/repo/status')
def repo_status(repository: str = REPOSITORY):
    return repository_registry.pilot(repository).stats()


@app.post('/api/repo/sync')
def repo_sync(data: RepoSyncInput,repository: str = REPOSITORY):
    return repository_registry.pilot(repository).sync(data.include_code,data.max_pages,data.restart)


@app.post('/api/repo/search')
def repo_search(data: RepoSearchInput,repository: str = REPOSITORY):
    return repository_registry.pilot(repository).search(data.keywords,data.live,data.offset)


@app.get('/api/repo/issues/{number}')
def repo_issue(number: int,repository: str = REPOSITORY):
    return repository_registry.pilot(repository).issue(number)


@app.post('/api/repo/issues/{number}/refresh')
def repo_issue_refresh(number: int,repository: str = REPOSITORY):
    return repository_registry.pilot(repository).refresh(number)


@app.get('/api/repo/intakes')
def repo_intakes(repository: str = REPOSITORY):
    return repository_registry.pilot(repository).cases()


@app.post('/api/repo/intakes',status_code=201)
def repo_intake_create(data: RepoIntakeInput,repository: str = REPOSITORY):
    return repository_registry.pilot(repository).create(data.title,data.body,data.version,data.source_number)


@app.get('/api/repo/intakes/{cid}')
def repo_intake_read(cid: str,repository: str = REPOSITORY):
    return repository_registry.pilot(repository).case(cid)


@app.post('/api/repo/intakes/{cid}/run')
def repo_intake_run(cid: str,data: RepoRunInput,repository: str = REPOSITORY):
    return repository_registry.pilot(repository).investigate(cid,data.use_llm)


@app.post('/api/repo/intakes/{cid}/observations')
def repo_intake_observe(cid: str,data: RepoObservationInput,repository: str = REPOSITORY):
    return repository_registry.pilot(repository).observe(cid,data.outcome,data.note,data.revision)


@app.get('/api/graph/examples')
def graph_examples():
    return landscape.examples()


@app.get('/api/graph/landscape')
def graph_landscape(issue: str | None = None):
    if issue and len(issue) > 80:
        raise ValueError('Issue ID is too long')
    return landscape.projection(issue)


@app.get('/landscape.js')
def landscape_script():
    return FileResponse(Path(__file__).parent / 'static' / 'landscape.js', media_type='text/javascript')


@app.get('/landscape.css')
def landscape_styles():
    return FileResponse(Path(__file__).parent / 'static' / 'landscape.css', media_type='text/css')


@app.exception_handler(LLMUnavailable)
async def llm_error(request, exc):
    return JSONResponse(status_code=503, content={'detail': str(exc)})


@app.exception_handler(RedisError)
async def database_error(request, exc):
    return JSONResponse(status_code=503, content={'detail': 'FalkorDB is unavailable. Start the graph and run python seed.py.'})


@app.exception_handler(ValueError)
async def invalid(request, exc):
    return JSONResponse(status_code=400, content={'detail': str(exc)})


@app.exception_handler(KeyError)
async def missing(request, exc):
    return JSONResponse(status_code=404, content={'detail': str(exc.args[0])})


class CaseInput(BaseModel):
    feature: str = Field(min_length=1, max_length=80)
    report: str = Field(min_length=5, max_length=4000)


class AttemptInput(BaseModel):
    action_id: str
    outcome: Literal['failed', 'inconclusive', 'passed']
    note: str = Field(default='', max_length=2000)
    service: str | None = None


class OwnerInput(BaseModel):
    service: str
    team: str


class InvestigationInput(BaseModel):
    report: str = Field(min_length=5, max_length=4000)
    use_llm: bool = False
    issue_id: str | None = Field(default=None, max_length=60)
    version: str | None = Field(default=None, max_length=50)


class ReviewInput(BaseModel):
    outcome: Literal['applicable', 'not_applicable', 'needs_more_info']
    note: str = Field(min_length=3, max_length=2000)


@app.get('/')
def home():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')


@app.get('/journey.js')
def journey_script():
    return FileResponse(Path(__file__).parent / 'static' / 'journey.js', media_type='text/javascript')


@app.get('/journey.css')
def journey_styles():
    return FileResponse(Path(__file__).parent / 'static' / 'journey.css', media_type='text/css')


@app.get('/api/real/stats')
def real_stats():
    return {**real.stats(), 'llm': configuration()}


@app.get('/api/real/issues')
def real_issues(q: str = '', version: str | None = None):
    if len(q) > 4000 or (version and len(version) > 50):
        raise ValueError('Search input is too long')
    return real.search(q, version)


@app.get('/api/real/issues/{iid}')
def real_issue(iid: str):
    trace = []
    return {**real.context(iid, trace), 'trace': trace}


@app.post('/api/real/issues/{iid}/reviews', status_code=201)
def real_review(iid: str, data: ReviewInput):
    return real.review(iid, data.outcome, data.note)


@app.post('/api/agent/investigate')
def agent_investigate(data: InvestigationInput):
    return run_investigation(real, data.report, data.use_llm, data.issue_id, data.version)


@app.get('/api/agent/runs')
def agent_runs():
    return real.runs()


@app.get('/api/agent/runs/{rid}')
def agent_run(rid: str):
    return real.run(rid)


@app.get('/api/catalog')
def catalog():
    return store.catalog()


@app.get('/api/cases')
def cases():
    return store.cases()


@app.post('/api/cases', status_code=201)
def create_case(data: CaseInput):
    return store.investigate(store.create_case(data.feature, data.report))


@app.get('/api/cases/{cid}')
def investigate(cid: str, service: str | None = None):
    return store.investigate(cid, service)


@app.post('/api/cases/{cid}/attempts')
def attempt(cid: str, data: AttemptInput):
    return store.attempt(cid, data.action_id, data.outcome, data.note, data.service)


@app.get('/api/impact/{service}')
def impact(service: str):
    return store.impact(service)


@app.post('/api/demo/ownership')
def ownership(data: OwnerInput):
    return store.change_owner(data.service, data.team)
