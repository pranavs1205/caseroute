"""Record a captioned 2–3 minute real browser demo in an isolated graph.

Requires Playwright + Chromium. No LLM calls, synthetic model responses or edits
to the user's graph. The video is a real screen capture with explanatory captions.
"""
import contextlib
import io
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from uuid import uuid4

from components import enrich
from graph import Store
from import_real_data import download, load, records
from seed import seed
from playwright.sync_api import sync_playwright, expect

ISSUE='spark-13289604'
TITLE='Error in writing a pyspark streaming dataframe created from Kafka source to a csv file'


def main():
    root=Path(__file__).parent
    output=root/'artifacts';output.mkdir(exist_ok=True)
    name='caseroute_video_'+uuid4().hex
    store=Store(name)
    server=None
    receipt=dict(graph=name,mode='graph_only',captioned=True,audio=False,passed=False)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            seed(store);source=download();load(store,source,manifest_path=None);enrich(store,records(source))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        base=f'http://127.0.0.1:{port}'
        env={**os.environ,'FALKORDB_GRAPH':name}
        log=(output/'demo-server.log').open('w',encoding='utf-8')
        server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
        for _ in range(45):
            try:
                with urllib.request.urlopen(base+'/api/real/stats',timeout=2) as response:
                    if json.load(response)['issues']==20275:break
            except OSError:
                if server.poll() is not None:raise RuntimeError('Demo API startup failed; see ignored server log.')
                time.sleep(1)
        else:raise RuntimeError('Demo API was not ready')
        with sync_playwright() as p:
            browser=p.chromium.launch()
            context=browser.new_context(viewport={'width':1440,'height':900},record_video_dir=str(output/'video-takes'),record_video_size={'width':1440,'height':900})
            page=context.new_page();page.set_default_timeout(30000)
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            started=time.monotonic()

            def caption(text):
                page.evaluate('''text=>{let box=document.getElementById('demo-caption');if(!box){box=document.createElement('div');box.id='demo-caption';box.style='position:fixed;left:6%;right:6%;bottom:18px;padding:15px 22px;background:#103b32f2;color:white;font:600 20px/1.45 system-ui;z-index:99999;border-radius:10px;box-shadow:0 4px 22px #0003;pointer-events:none';document.body.appendChild(box)}box.textContent=text}''',text)

            def until(seconds):
                remaining=started+seconds-time.monotonic()
                while remaining>0:
                    page.wait_for_timeout(min(remaining,1)*1000)
                    remaining=started+seconds-time.monotonic()

            def source_view():
                page.locator('[data-tab="library"]').click()
                page.locator('#library-query').fill('writing pyspark streaming dataframe Kafka')
                page.locator('#library-version').fill('2.4.5')
                page.get_by_role('button',name='Search real reports',exact=True).click()
                page.locator('[data-issue="'+ISSUE+'"]').click()
                page.locator('#library-detail').scroll_into_view_if_needed()
                expect(page.locator('#library-detail')).to_contain_text(TITLE)

            page.goto(base)
            expect(page.locator('#real-count')).to_have_text('20,275')
            expect(page.locator('#map-status')).to_contain_text('nodes')
            caption('CaseRoute: an evidence-grounded investigation workflow that remembers what reviewers checked.');until(12)
            page.locator('#landscape').scroll_into_view_if_needed()
            caption('Real Spark report: a Kafka source flows through PySpark, DataFrames and Streaming. Each mention has a source excerpt.');until(26)
            page.locator('#node-inspector [data-neighbor="kafka"]').click()
            expect(page.locator('#node-inspector')).to_contain_text('MENTIONS')
            caption('FalkorDB follows issue → component ← other issue. A shared component is a lead—not proof of a common cause.');until(39)
            source_view()
            page.locator('#library-detail').get_by_text('Source description',exact=True).click()
            caption('Inspect the actual report and original link. Its recorded outcome is Invalid; CaseRoute does not invent a fix.');until(55)
            page.locator('#explore-source-graph').click()
            expect(page.locator('#map-status')).to_contain_text('nodes')
            with page.expect_response(lambda response:response.url.endswith('/api/agent/investigate')) as first_response:
                page.locator('#map-investigate').click()
            first=first_response.value.json();assert first_response.value.status==200
            assert first['decision']['next_step']=='investigate_component_boundary'
            page.locator('#journey-result').scroll_into_view_if_needed()
            caption('The graph-only agent selects a bounded action: isolate a reproduction across the four mentioned components.');until(73)
            page.locator('[data-stage="6"]').click()
            expect(page.locator('#stage-detail')).to_contain_text('MENTIONS')
            caption('The execution receipt exposes the multi-hop Cypher, parameters, returned evidence and timing. This run makes no LLM calls.');until(89)
            previous_review=page.locator('#review-note').element_handle()
            with page.expect_response(lambda response:response.url.endswith('/api/real/issues/'+ISSUE)):
                page.locator('#open-real-source').click()
            previous_review.wait_for_element_state('hidden')
            expect(page.locator('#tab-library')).to_be_visible()
            expect(page.locator('#review-note')).to_have_value('')
            page.locator('#review-outcome').select_option('needs_more_info')
            note='Demo review: current environment and reproduction are not supplied; request those before treating this lead as applicable.'
            page.locator('#review-note').fill(note)
            page.get_by_role('button',name='Save review to graph',exact=True).click()
            expect(page.locator('#review-memory')).to_contain_text(note)
            page.locator('#review-memory').scroll_into_view_if_needed()
            caption('Save a reviewer check in FalkorDB. This marked demonstration review requests the current environment and reproduction.');until(108)
            page.reload();source_view()
            expect(page.locator('#review-memory')).to_contain_text(note)
            page.locator('#review-memory').scroll_into_view_if_needed()
            caption('Reload the app: the review is still here. Historical source status remains separate from our investigation memory.');until(125)
            page.locator('#investigate-source').click()
            with page.expect_response(lambda response:response.url.endswith('/api/agent/investigate')) as second_response:
                page.locator('#journey-form button').click()
            second=second_response.value.json();assert second_response.value.status==200
            assert second['decision']['next_step']=='request_details'
            page.locator('#journey-result .evidence').scroll_into_view_if_needed()
            caption('The next decision changes: request details. The graph’s saved review prevents blindly repeating the earlier lead.');until(143)
            page.locator('[data-tab="cases"]').click()
            page.locator('#tab-cases h1').scroll_into_view_if_needed()
            caption('Separate synthetic lab: fictional service ownership, documented checks and impact previews. These are not facts about Spark.');until(153)
            page.locator('[data-tab="journey"]').click()
            page.locator('#landscape').scroll_into_view_if_needed()
            caption('Track 01 · Connected evidence → explainable next step → persistent review memory. github.com/pranavs1205/caseroute');until(165)
            assert not errors,errors
            receipt.update(passed=True,duration_seconds=round(time.monotonic()-started,2),first_run=first['id'],second_run=second['id'],
                           initial_step=first['decision']['next_step'],after_review_step=second['decision']['next_step'],
                           issue=ISSUE,source_resolution=first['context']['issue']['resolution'],captured_url=base)
            video=page.video
            page.screenshot(path=str(output/'demo-final-frame.png'))
            context.close();video.save_as(str(output/'caseroute-demo.webm'));browser.close()
        print(json.dumps(receipt,indent=2))
    finally:
        if server:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()
        assert store.graph.name==name and name.startswith('caseroute_video_')
        store.graph.delete()
        receipt['temporary_graph_deleted']=True
        (output/'demo-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
