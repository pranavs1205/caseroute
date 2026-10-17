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

app = FastAPI(title='CaseRoute', description='Graph-guided investigations with sourced real historical reports and a synthetic ownership lab')
store = Store()
real = RealCases(store)
landscape = Landscape(real)


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
