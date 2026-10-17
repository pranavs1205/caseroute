"""Own a temporary API process; inspect real ranked paths without model calls."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


def main():
    output=Path('artifacts');output.mkdir(exist_ok=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    with (output/'guidance-server.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
        try:
            for _ in range(30):
                try:
                    with urllib.request.urlopen(base+'/api/real/stats',timeout=2):break
                except OSError:time.sleep(1)
            else:raise RuntimeError('Owned API failed startup')
            with sync_playwright() as p:
                browser=p.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1000})
                page.set_default_timeout(30000)
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base)
                page.locator('[data-tab="library"]').click()
                page.locator('#library-query').fill('Fix pyspark.pandas.mlflow.load_model')
                page.get_by_role('button',name='Search real reports',exact=True).click()
                page.locator('[data-issue="spark-13559808"]').click()
                expect(page.locator('#library-detail')).to_contain_text('Why these related reports?')
                ranked=page.locator('#library-detail .card').filter(has=page.get_by_role('heading',name='Why these related reports?'))
                ranked.locator('summary').first.click()
                expect(ranked).to_contain_text('connected reports')
                expect(ranked).to_contain_text('Source:')
                ranked.scroll_into_view_if_needed()
                page.screenshot(path=str(output/'ranked-evidence.png'))
                page.locator('#investigate-source').click()
                page.locator('#journey-llm').uncheck()
                with page.expect_response(lambda r:r.url.endswith('/api/agent/investigate')) as response:
                    page.locator('#journey-form button').click()
                result=response.value.json()
                assert response.value.status==200,result
                assert result['decision']['next_step']=='check_environment'
                primary={c['name'] for c in result['decision']['guidance']['primary_components']}
                assert not {'Scheduler','Shuffle'} & primary
                index=next(i for i,s in enumerate(result['trace']) if s['tool']=='rank_technical_evidence')
                page.locator(f'[data-stage="{index}"]').click()
                expect(page.locator('#stage-detail')).to_contain_text('HAS_SIGNAL')
                page.locator('#stage-detail').scroll_into_view_if_needed()
                page.screenshot(path=str(output/'ranked-query-receipt.png'))
                page.set_viewport_size({'width':390,'height':844})
                page.screenshot(path=str(output/'guidance-mobile.png'))
                assert not errors,errors
                receipt=dict(passed=True,issue=result['context']['issue']['id'],policy=result['decision']['guidance']['policy'],
                             ranked_reports=len(result['context']['ranked_evidence']),primary_components=sorted(primary),
                             next_step=result['decision']['next_step'],model_calls=0,browser_errors=errors)
                (output/'guidance-browser.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
                print(json.dumps(receipt,indent=2));browser.close()
        finally:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()


if __name__=='__main__':
    main()
