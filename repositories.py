"""Public repository onboarding and persistent graph isolation."""
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor

from graph import Store
from github_client import GitHubClient, REPOSITORY, normalize_repository
from repo_pilot import RepoPilot, now


class RepositoryRegistry:
    def __init__(self,store=None,pilot_store_factory=None,client_factory=None):
        self.store=store or Store(os.getenv('CASE_REPOSITORY_CATALOG','caseroute_repository_catalog'))
        self.pilot_store_factory=pilot_store_factory or (lambda repo:Store(self.graph_name(repo)))
        self.client_factory=client_factory or (lambda repo:GitHubClient(repository=repo))
        self._initialized=False

    def graph_name(self,repo):
        if repo==REPOSITORY:return os.getenv('CASE_GITHUB_GRAPH','caseroute_github')
        return 'caseroute_repo_'+hashlib.sha256(repo.encode()).hexdigest()[:32]

    def initialize(self):
        if self._initialized:return
        # Preserve the existing Graphiti pilot and investigations without a copy.
        self.store.write('MERGE (r:ConnectedRepository {id:$repo}) ON CREATE SET r.graph=$graph,r.added=$now',
                         repo=REPOSITORY,graph=self.graph_name(REPOSITORY),now=now())
        self._initialized=True

    def list(self):
        self.initialize()
        return self.store.read('MATCH (r:ConnectedRepository) RETURN properties(r) AS repository ORDER BY r.id')

    def add(self,value):
        repo=normalize_repository(value)
        client=self.client_factory(repo)
        meta=client.get('/repos/'+repo)
        if meta.get('private'):raise ValueError('Only public repositories are supported in this workspace.')
        canonical=normalize_repository(meta['full_name'])
        if canonical!=repo:raise ValueError('Repository moved. Add the current owner/repository shown on GitHub.')
        self.initialize()
        self.store.write('''MERGE (r:ConnectedRepository {id:$repo}) ON CREATE SET r.added=$now
            SET r.graph=$graph,r.description=$description,r.language=$language,r.checked=$now''',
            repo=repo,graph=self.graph_name(repo),now=now(),description=meta.get('description') or '',language=meta.get('language') or 'Unknown')
        self.pilot(repo)
        return dict(repository=repo,github_calls=len(client.receipts),repositories=self.list())

    def pilot(self,value=REPOSITORY):
        repo=normalize_repository(value)
        self.initialize()
        rows=self.store.read('MATCH (r:ConnectedRepository {id:$repo}) RETURN properties(r) AS repository',repo=repo)
        if not rows:
            raise KeyError('Add this repository to the workspace first.')
        pilot=RepoPilot(self.pilot_store_factory(repo),repository=repo,client_factory=lambda:self.client_factory(repo))
        if not rows[0]['repository'].get('initialized'):
            pilot.index()
            self.store.write('MATCH (r:ConnectedRepository {id:$repo}) SET r.initialized=true',repo=repo)
        return pilot

    def search_all(self,keywords):
        results=[];limited=[]
        names=[entry['repository']['id'] for entry in self.list()]
        def search(repo):
            try:return repo,self.pilot(repo).search(keywords)
            except KeyError:return repo,dict(results=[])
        with ThreadPoolExecutor(max_workers=min(8,len(names))) as pool:
            batches=list(pool.map(search,names))
        for repo,found in batches:
            if found.get('has_more'):limited.append(repo)
            results.extend({**item,'repository':repo} for item in found['results'])
        return dict(results=results,github_calls=0,cached=True,query=keywords,incomplete=False,
                    limited_repositories=limited,
                    scope='Cached preview across connected repositories (up to 30 hits per repository); select a repository to paginate or investigate.')
