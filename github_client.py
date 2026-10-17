"""Bounded, read-only GitHub API client for the single public repository pilot."""
import http.client
import json
import re
import shutil
import subprocess
from urllib.parse import urlencode, urlsplit

from anyapi_smoke import load_setting

REPOSITORY = 'getzep/graphiti'


def normalize_repository(value):
    value=value.strip()
    if value.startswith('https://'):
        parsed=urlsplit(value)
        if parsed.netloc.lower()!='github.com' or parsed.query or parsed.fragment:
            raise ValueError('Use a public github.com repository URL or owner/repository.')
        value=parsed.path.strip('/')
    value=value.removesuffix('.git')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}',value) or value.split('/')[-1] in ('.','..'):
        raise ValueError('Use owner/repository or https://github.com/owner/repository.')
    return value.lower()


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
    def __init__(self, credential=None, repository=REPOSITORY):
        self.repository=normalize_repository(repository)
        self.credential = token() if credential is None else credential
        self.receipts = []
        self.has_next=False

    def get(self, path):
        if not (path.startswith('/repos/'+self.repository+'/') or path == '/repos/'+self.repository or path.startswith('/search/issues?')) or '..' in path.split('?')[0].split('/'):
            raise ValueError('GitHub path is outside the selected repository')
        connection = http.client.HTTPSConnection('api.github.com', timeout=20)
        headers = {'Accept':'application/vnd.github+json', 'User-Agent':'CaseRoute-public-repo-pilot',
                   'X-GitHub-Api-Version':'2022-11-28'}
        if self.credential:
            headers['Authorization'] = 'Bearer '+self.credential
        try:
            connection.request('GET', path, headers=headers)
            response = connection.getresponse()
            self.has_next='rel="next"' in (response.getheader('link') or '')
            limit=10_000_000 if path.startswith('/repos/'+self.repository+'/issues?') else 2_000_000
            raw = response.read(limit+1)
            self.receipts.append(dict(method='GET',path=path,status=response.status,
                                      remaining=response.getheader('x-ratelimit-remaining')))
            if response.status != 200:
                raise GitHubUnavailable(f'GitHub returned HTTP {response.status}. Check access or rate limits; no result was inferred.')
            if len(raw) > limit:
                raise GitHubUnavailable('GitHub response exceeded the bounded request size limit; import remains incomplete.')
            return json.loads(raw)
        except (OSError, http.client.HTTPException, ValueError):
            raise GitHubUnavailable('GitHub was unavailable or returned invalid data. Try again later.') from None
        finally:
            connection.close()

    def search(self, keywords='', limit=10):
        # Remove GitHub qualifiers/operators: user text cannot change repository scope.
        words = re.findall(r'[A-Za-z0-9_]+', keywords)[:6]
        words = [w[:60] for w in words if w.upper() not in ('AND','OR','NOT')]
        query = ' '.join(['repo:'+self.repository,'is:issue',*words])
        args = dict(q=query,per_page=min(limit,30))
        if not words:
            args.update(sort='updated',order='desc')
        payload = self.get('/search/issues?'+urlencode(args))
        items=[]
        for item in payload.get('items',[]):
            if 'pull_request' in item:
                continue
            number=item.get('number')
            if not isinstance(number,int) or item.get('html_url','').lower() != f'https://github.com/{self.repository}/issues/{number}':
                continue
            items.append(item)
        return dict(query=query,items=items,incomplete=bool(payload.get('incomplete_results')))

    def issue(self, number):
        if not isinstance(number,int) or number < 1:
            raise ValueError('A positive GitHub issue number is required')
        item=self.get(f'/repos/{self.repository}/issues/{number}')
        if 'pull_request' in item:
            raise ValueError('This pilot accepts issues, not pull-request numbers')
        return item

    def issue_page(self,page):
        if not isinstance(page,int) or page<1:raise ValueError('Invalid issue page')
        payload=self.get('/repos/'+self.repository+'/issues?'+urlencode(dict(state='all',sort='created',direction='asc',per_page=100,page=page)))
        if not isinstance(payload,list):raise GitHubUnavailable('GitHub returned an invalid issue page.')
        items=[i for i in payload if 'pull_request' not in i]
        return dict(items=items,has_next=self.has_next,records=len(payload))
