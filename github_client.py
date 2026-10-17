"""Bounded, read-only GitHub API client for the single public repository pilot."""
import http.client
import json
import re
import shutil
import subprocess
from urllib.parse import urlencode

from anyapi_smoke import load_setting

REPOSITORY = 'getzep/graphiti'


class GitHubUnavailable(RuntimeError):
    pass


def token():
    value = load_setting(('GITHUB_TOKEN', 'GH_TOKEN'))
    if value:
        return value
    if shutil.which('gh'):
        try:
            result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    return ''


class GitHubClient:
    def __init__(self, credential=None):
        self.credential = token() if credential is None else credential
        self.receipts = []

    def get(self, path):
        if not (path.startswith('/repos/'+REPOSITORY+'/') or path == '/repos/'+REPOSITORY or path.startswith('/search/issues?')):
            raise ValueError('GitHub path is outside the pilot repository')
        connection = http.client.HTTPSConnection('api.github.com', timeout=20)
        headers = {'Accept':'application/vnd.github+json', 'User-Agent':'CaseRoute-public-repo-pilot',
                   'X-GitHub-Api-Version':'2022-11-28'}
        if self.credential:
            headers['Authorization'] = 'Bearer '+self.credential
        try:
            connection.request('GET', path, headers=headers)
            response = connection.getresponse()
            raw = response.read(2_000_001)
            self.receipts.append(dict(method='GET',path=path,status=response.status,
                                      remaining=response.getheader('x-ratelimit-remaining')))
            if response.status != 200:
                raise GitHubUnavailable(f'GitHub returned HTTP {response.status}. Check access or rate limits; no result was inferred.')
            if len(raw) > 2_000_000:
                raise GitHubUnavailable('GitHub response exceeded the 2 MB request limit.')
            return json.loads(raw)
        except (OSError, http.client.HTTPException, ValueError):
            raise GitHubUnavailable('GitHub was unavailable or returned invalid data. Try again later.') from None
        finally:
            connection.close()

    def search(self, keywords='', limit=10):
        # Remove GitHub qualifiers/operators: user text cannot change repository scope.
        words = re.findall(r'[A-Za-z0-9_]+', keywords)[:6]
        words = [w[:60] for w in words if w.upper() not in ('AND','OR','NOT')]
        query = ' '.join(['repo:'+REPOSITORY,'is:issue',*words])
        args = dict(q=query,per_page=min(limit,30))
        if not words:
            args.update(sort='updated',order='desc')
        payload = self.get('/search/issues?'+urlencode(args))
        items=[]
        for item in payload.get('items',[]):
            if 'pull_request' in item:
                continue
            number=item.get('number')
            if not isinstance(number,int) or item.get('html_url') != f'https://github.com/{REPOSITORY}/issues/{number}':
                continue
            items.append(item)
        return dict(query=query,items=items,incomplete=bool(payload.get('incomplete_results')))

    def issue(self, number):
        if not isinstance(number,int) or number < 1:
            raise ValueError('A positive GitHub issue number is required')
        item=self.get(f'/repos/{REPOSITORY}/issues/{number}')
        if 'pull_request' in item:
            raise ValueError('This pilot accepts issues, not pull-request numbers')
        return item
