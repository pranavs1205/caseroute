"""Real public issue → code path → observation → reload; owns its API process."""
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
    with (output/'repo-browser-server.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
        try:
            for _ in range(30):
                try:
                    with urllib.request.urlopen(base+'/api/repo/status',timeout=3):break
                except OSError:time.sleep(1)
            else:raise RuntimeError('Owned API did not start')
            with sync_playwright() as p:
                browser=p.chromium.launch();page=browser.new_page(viewport={'width':1500,'height':1050})
                page.set_default_timeout(30000)
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base);page.locator('[data-tab="repo"]').click()
                expect(page.locator('#repo-status')).to_contain_text('30 cached issues')
                page.locator('#repo-keywords').fill('#2014')
                page.locator('#repo-search button').click()
                page.locator('[data-repo-issue="2014"]').click()
                expect(page.locator('#repo-issue')).to_contain_text('SearchResults.merge()')
                with page.expect_response(lambda r:r.url.endswith('/api/repo/intakes')) as response:
                    page.locator('#repo-investigate-source').click()
                result=response.value.json();assert response.value.status==201,result
                case=result['intake']['id']
                assert not any(x['id'].endswith('#2014') for x in result['run']['issues'])
                assert any(x['symbol']=='SearchResults.merge' for x in result['run']['code'])
                expect(page.locator('#repo-case')).to_contain_text('SearchResults.merge')
                page.locator('#repo-case').scroll_into_view_if_needed()
                page.screenshot(path=str(output/'github-issue-code-path.png'))
                note='Browser acceptance: source release differs; request current version and reproduction before using this lead.'
                page.locator('#repo-outcome').select_option('not_applicable');page.locator('#repo-note').fill(note)
                page.locator('#repo-observation button').click()
                expect(page.locator('#repo-case .evidence')).to_contain_text('request_details')
                page.reload();page.locator('[data-tab="repo"]').click()
                page.locator('[data-intake="'+case+'"]').click()
                expect(page.locator('#repo-case')).to_contain_text(note)
                stale=page.request.post(base+'/api/repo/intakes/'+case+'/observations',data=dict(outcome='useful_lead',note='Stale browser check',revision=0))
                assert stale.status==409
                page.locator('#repo-title').fill('SearchResults.merge ranking differs in my application')
                page.locator('#repo-body').fill('My application merges results from two groups using SearchResults.merge. I expected the scores to remain in descending order with the configured limit, but the result order changes. This is a new local report for investigation, not a published GitHub issue.')
                page.locator('#repo-version').fill('not yet verified')
                with page.expect_response(lambda r:r.url.endswith('/api/repo/intakes')) as fresh:
                    page.locator('#repo-new button').click()
                new=fresh.value.json();assert fresh.value.status==201
                assert new['run']['code'] and new['run']['issues']
                assert new['run']['github_calls']==0 and new['run']['llm_calls']==0
                expect(page.locator('#repo-case')).to_contain_text(new['intake']['id'])
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                page.screenshot(path=str(output/'github-pilot-mobile.png'))
                assert not errors,errors
                receipt=dict(passed=True,source_issue='getzep/graphiti#2014',known_case=case,new_case=new['intake']['id'],
                    source_self_excluded=True,declaration='SearchResults.merge',observation_persists=True,
                    stale_write_status=stale.status,new_report_github_calls=0,llm_calls=0,browser_errors=errors)
                (output/'github-browser.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
                print(json.dumps(receipt,indent=2));browser.close()
        finally:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()


if __name__=='__main__':main()
