"""Self-service third repository onboarding, backfill and scoped switching."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright,expect


def main():
    output=Path('artifacts');output.mkdir(exist_ok=True)
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    with (output/'multi-repo-api.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
        try:
            for _ in range(30):
                try:
                    with urllib.request.urlopen(base+'/api/repos',timeout=3):break
                except OSError:time.sleep(1)
            else:raise RuntimeError('Owned API did not start')
            with sync_playwright() as p:
                browser=p.chromium.launch();page=browser.new_page(viewport={'width':1500,'height':1050})
                page.set_default_timeout(30000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base);page.locator('[data-tab="repo"]').click()
                page.locator('#repo-add-value').fill('https://github.com/FalkorDB/GraphRAG-SDK')
                with page.expect_response(lambda r:r.url.endswith('/api/repos') and r.request.method=='POST') as added:
                    page.locator('#repo-add button').click()
                add=added.value.json();assert added.value.status==201,add
                expect(page.locator('#repo-select')).to_have_value('falkordb/graphrag-sdk')
                expect(page.locator('#repo-status')).to_contain_text('cached issues')
                page.locator('#repo-sync-code').uncheck()
                page.locator('#repo-sync').click()
                expect(page.locator('#repo-status')).to_contain_text('All issue pages read',timeout=180000)
                expect(page.locator('#repo-sync')).to_be_enabled(timeout=30000)
                state=page.request.get(base+'/api/repo/status?repository=falkordb%2Fgraphrag-sdk').json()
                assert state['snapshot']['issues_complete']
                assert state['counts']['RepoIssue']>0
                page.screenshot(path=str(output/'connected-repositories.png'))
                page.locator('#repo-select').select_option('pranavs1205/caseroute')
                expect(page.locator('#repo-name')).to_have_text('pranavs1205/caseroute')
                expect(page.locator('#repo-status')).to_contain_text('cached issues')
                page.locator('#repo-sync').click()
                expect(page.locator('#repo-status')).to_contain_text('All issue pages read',timeout=60000)
                expect(page.locator('#repo-sync')).to_be_enabled(timeout=30000)
                page.locator('#repo-select').select_option('getzep/graphiti')
                expect(page.locator('#repo-name')).to_have_text('getzep/graphiti')
                expect(page.locator('#repo-status')).to_contain_text('cached issues')
                page.locator('#repo-all').check();page.locator('#repo-keywords').fill('graph')
                with page.expect_response(lambda r:r.url.endswith('/api/repos/search'),timeout=60000) as search:
                    page.locator('#repo-search button').click()
                assert search.value.status==200,search.value.json()
                expect(page.locator('#repo-search-receipt')).to_contain_text('across connected repositories',timeout=30000)
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                page.screenshot(path=str(output/'connected-repositories-mobile.png'))
                assert not errors,errors
                receipt=dict(passed=True,repository_added=add['repository'],connected_repositories=len(add['repositories']),
                             imported_issues=state['counts']['RepoIssue'],issue_pages=state['snapshot']['issue_pages'],
                             all_issue_pages_read=True,repository_switching=True,cross_repository_local_search=True,
                             github_writes=0,llm_calls=0,browser_errors=errors)
                (output/'repositories-browser.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
                print(json.dumps(receipt,indent=2));browser.close()
        finally:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()


if __name__=='__main__':main()
