"""Real source → graph trace → persisted review; includes configured live LLM calls."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def check():
    Path('artifacts').mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width':1440, 'height':1100})
        page.set_default_timeout(20000)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://127.0.0.1:8010')
        provider = page.request.get('http://127.0.0.1:8010/api/real/stats').json()['llm']['provider']
        expect(page.locator('#real-count')).to_have_text('20,275')
        page.screenshot(path='artifacts/graph-journey-home.png', full_page=True)
        page.locator('#journey-version').fill('3.4.0')
        page.get_by_role('button', name='Run graph investigation', exact=False).click()
        page.locator('#stage-rail').wait_for()
        expect(page.locator('#journey-result')).to_contain_text('Graph-only')
        page.locator('[data-stage="2"]').click()
        expect(page.locator('#stage-detail')).to_contain_text('AFFECTS')
        expect(page.locator('#stage-detail')).to_contain_text('Actual parameterized query')
        page.get_by_role('button', name='Replay recorded steps').click()
        page.screenshot(path='artifacts/graph-journey-trace.png', full_page=True)
        page.get_by_role('button', name='Real case library', exact=False).click()
        page.locator('#library-query').fill('PySpark Python 3.7')
        page.locator('#library-version').fill('3.4.0')
        page.get_by_role('button', name='Search real reports').click()
        page.locator('[data-issue="spark-13525982"]').click()
        expect(page.locator('#library-detail')).to_contain_text('Make PySpark working with Python 3.7')
        expect(page.locator('#library-detail')).to_contain_text('Shared-version')
        page.locator('#review-note').fill('Browser acceptance: confirm the current runtime and minimal reproduction.')
        page.get_by_role('button', name='Save review to graph').click()
        expect(page.locator('#review-memory')).to_contain_text('Browser acceptance: confirm the current runtime')
        page.reload()
        page.get_by_role('button', name='Real case library', exact=False).click()
        page.locator('#library-query').fill('PySpark Python 3.7')
        page.locator('#library-version').fill('3.4.0')
        page.get_by_role('button', name='Search real reports').click()
        page.locator('[data-issue="spark-13525982"]').click()
        expect(page.locator('#review-memory')).to_contain_text('Browser acceptance: confirm the current runtime')
        page.screenshot(path='artifacts/real-case-evidence.png', full_page=True)
        page.get_by_role('button', name='Investigate this source').click()
        page.locator('#journey-llm').check()
        with page.expect_response(lambda r: r.url.endswith('/api/agent/investigate'), timeout=120000) as response:
            page.get_by_role('button', name='Run graph investigation', exact=False).click()
        result = response.value.json()
        assert response.value.status == 200, result
        expect(page.locator('#journey-result')).to_contain_text('LLM + graph')
        llm_calls = [s for s in result['trace'] if s['kind']=='llm']
        assert len(llm_calls) == 2
        assert all((s['usage'].get('output_tokens') or s['usage'].get('completion_tokens',0)) > 0 for s in llm_calls)
        assert all(s['provider'] == provider for s in llm_calls)
        assert result['decision']['next_step'] == 'request_details'  # prior review is respected
        saved = page.request.get('http://127.0.0.1:8010/api/agent/runs/' + result['id']).json()
        assert saved['context'] == result['context']
        assert saved['decision'] == result['decision']
        assert saved['trace'] == result['trace']
        page.locator('[data-stage="0"]').click()
        expect(page.locator('#stage-detail')).to_contain_text(provider)
        page.screenshot(path='artifacts/llm-graph-journey.png', full_page=True)
        Path('artifacts/live-llm-check.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        page.reload()
        page.locator('[data-run="' + result['id'] + '"]').click()
        expect(page.locator('#journey-result')).to_contain_text('LLM + graph')
        expect(page.locator('#journey-result')).to_contain_text('Relationships returned by FalkorDB')
        for name in ['journey','library']:
            page.locator(f'[data-tab="{name}"]').click()
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name, page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})'))
        page.screenshot(path='artifacts/real-mobile.png', full_page=True)
        assert not errors, errors
        browser.close()
        print('PASS: real corpus counts, graph trace, replay, sources, persisted human review, two live '+provider+' calls and mobile layout')


if __name__ == '__main__':
    check()
