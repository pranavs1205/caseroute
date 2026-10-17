"""Complex real issue → canvas graph → decision, plus full-corpus coverage."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    Path('artifacts').mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1600,'height':1150})
        page.set_default_timeout(30000)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8010')
        expect(page.locator('#map-status')).to_contain_text('nodes')
        expect(page.locator('#complex-examples')).to_contain_text('Kafka')
        expect(page.locator('#node-inspector')).to_contain_text('MENTIONS')
        assert page.get_by_text('GitBugs / Apache Spark, published by Avinash Patil under',exact=False).count()==0
        page.get_by_role('button',name='Zoom in',exact=True).click()
        page.get_by_role('button',name='Fit graph',exact=True).click()
        page.screenshot(path='artifacts/complex-issue-landscape.png',full_page=True)
        with page.expect_response(lambda r:r.url.endswith('/api/agent/investigate')) as receipt:
            page.locator('#map-investigate').click()
        result=receipt.value.json()
        assert receipt.value.status==200,result
        assert result['context']['issue']['id']=='spark-13289604'
        assert len(result['context']['components'])==4
        assert result['decision']['next_step']=='investigate_component_boundary'
        page.locator('[data-stage="5"]').click()
        expect(page.locator('#stage-detail')).to_contain_text('MENTIONS')
        expect(page.locator('#map-queries')).to_contain_text('load_issue_nodes')
        page.locator('#map-search').fill(result['context']['issue']['id'])
        page.get_by_role('button',name='Find node',exact=True).click()
        page.locator('#map-search-results button').first.click()
        expect(page.locator('#node-inspector')).to_contain_text('EXAMINED')
        page.screenshot(path='artifacts/graph-to-final-action.png',full_page=True)
        with page.expect_response(lambda r:'/api/graph/landscape' in r.url and '?issue=' not in r.url,timeout=90000) as full:
            page.get_by_role('button',name='Entire issue graph',exact=True).click()
        all_graph=full.value.json()
        assert full.value.status==200
        assert all_graph['issue_count']==20275
        assert len(all_graph['nodes'])==20361
        assert len(all_graph['edges'])==74803
        expect(page.locator('#map-status')).to_contain_text('20,275 issues',timeout=90000)
        page.screenshot(path='artifacts/full-issue-corpus.png',full_page=True)
        page.locator('#map-search').fill('spark-13289604')
        page.get_by_role('button',name='Find node',exact=True).click()
        page.locator('#map-search-results button').first.click()
        page.get_by_role('button',name='Expand this issue',exact=True).click()
        expect(page.locator('#map-status')).to_contain_text('17 issues')
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path='artifacts/landscape-mobile.png',full_page=True)
        assert not errors,errors
        Path('artifacts/landscape-check.json').write_text(json.dumps({'seed':result['context']['issue']['id'],
            'components':[c['name'] for c in result['context']['components']], 'decision':result['decision'],
            'full_graph':{k:all_graph[k] for k in ['issue_count','query_ms','scope_note']},
            'nodes':len(all_graph['nodes']),'edges':len(all_graph['edges'])},indent=2),encoding='utf-8')
        browser.close()
        print('PASS: removed paragraph, complex four-component issue, inspectable graph, final-action path, all 20,275 issues / 74,803 links, zoom/search/expand and mobile')


if __name__=='__main__':
    main()
