"""Browser acceptance check. Requires Playwright and a running local API."""
from pathlib import Path
from playwright.sync_api import sync_playwright


def check():
    Path('artifacts').mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://127.0.0.1:8010')
        page.get_by_text('● FalkorDB connected').wait_for()
        page.get_by_role('button', name='Case workspace', exact=False).click()
        page.locator('#feature').select_option('discounts')
        page.get_by_role('button', name='Investigate case').click()
        page.locator('#result').get_by_text('RUN-101', exact=False).first.wait_for()
        cid = page.locator('#result .eyebrow').first.inner_text()
        assert 'Commerce Engineering' in page.locator('#result').inner_text()
        page.locator('#attempt-note').fill('Browser gate: versions match')
        page.get_by_role('button', name='Check failed', exact=True).click()
        page.locator('#result').get_by_text('RUN-102', exact=False).first.wait_for()
        page.reload()
        page.get_by_role('button', name='Case workspace', exact=False).click()
        page.get_by_role('button', name=cid, exact=False).click()
        page.get_by_text('Browser gate: versions match', exact=True).wait_for()
        page.screenshot(path='artifacts/case-memory.png', full_page=True)
        page.get_by_role('button', name='Ownership lab', exact=False).click()
        page.locator('#owner-service').select_option('pricing')
        page.locator('#owner-team').select_option('platform')
        page.get_by_role('button', name='Update graph ownership').click()
        page.locator('#notice').get_by_text('Platform Reliability', exact=False).wait_for()
        page.get_by_role('button', name='Case workspace', exact=False).click()
        page.get_by_role('button', name=cid, exact=False).click()
        page.locator('#result').get_by_text('To Platform Reliability', exact=False).wait_for()
        page.get_by_role('button', name='Ownership lab', exact=False).click()
        page.locator('#owner-team').select_option('commerce')
        page.get_by_role('button', name='Update graph ownership').click()
        page.locator('#notice').get_by_text('Commerce Engineering', exact=False).wait_for()
        page.get_by_role('button', name='Impact explorer', exact=False).click()
        page.locator('#impact-service').select_option('pricing')
        page.get_by_role('button', name='Preview impact').click()
        page.locator('#impact-result').get_by_text('Read only', exact=True).wait_for()
        assert 'Campaigns' in page.locator('#impact-result').inner_text()
        page.screenshot(path='artifacts/impact.png', full_page=True)
        page.get_by_role('button', name='Case workspace', exact=False).click()
        page.locator('#feature').select_option('campaign')
        page.get_by_role('button', name='Investigate case').click()
        page.locator('#choose-service').wait_for()
        page.screenshot(path='artifacts/ambiguity.png', full_page=True)
        page.locator('#choose-service').select_option('campaigns')
        page.locator('#result').get_by_text('RUN-301', exact=False).first.wait_for()
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path='artifacts/mobile.png', full_page=True)
        assert not errors, errors
        browser.close()
        print('PASS: browser case, memory, impact, ambiguity and mobile layout; no JavaScript errors')
        print('Persistence case:', cid)


if __name__ == '__main__':
    check()
