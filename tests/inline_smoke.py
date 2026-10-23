"""Sandbox-only smoke test when browser navigation is policy-blocked. Not a persistence test."""
import json,pathlib,time
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1];out=ROOT/'qa';report={'mode':'inline_offline_fixture','checks':[],'notVerified':['real navigation','real localStorage persistence','official media playback'],'errors':[]}
def check(s,v):
 if not v:raise AssertionError(s)
 report['checks'].append(s)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1536,'height':1100},reduced_motion='reduce');page.route('**/*',lambda r:r.abort());page.on('pageerror',lambda e:report['errors'].append(str(e)))
 page.set_content((ROOT/'dist/index.html').read_text(),wait_until='domcontentloaded');count=page.evaluate('GamesTest.count');check('All fixture records rendered',page.locator('.game-card').count()==count)
 page.locator('#search').fill('tag:loot score>=9');check('Structured filtering',0<page.locator('.game-card').count()<count)
 page.locator('#search').fill('Halls of Torment');check('Name search',page.locator('.game-card').count()==1)
 page.locator('[data-open]').first.click();page.locator('#game-notes').fill('In-memory note');page.locator('#detail-status').select_option('Backlog');page.locator('#personal-rating').select_option('8');page.keyboard.press('Escape');check('Modal closes',not page.locator('#modal').evaluate('(e)=>e.open'))
 page.locator('[data-open]').first.click();check('Note retained in memory',page.locator('#game-notes').input_value()=='In-memory note');page.locator('[data-media-mode=screenshots]').click();check('Gallery controls',page.locator('.gallery-controls').count()==1);page.keyboard.press('Escape')
 page.locator('[data-save]').first.click();check('Favorite action',page.evaluate('GamesTest.personal.favorites.length===1'))
 page.locator('#search').fill('');page.locator('[data-view=table]').click();check('All table rows present',page.locator('tbody tr').count()==count);page.locator('th [data-sort=newest]').click();check('Sort control',page.evaluate("GamesTest.state.sort==='newest'"));page.locator('[data-view=grid]').click()
 page.locator('[data-compare]').nth(0).check();page.locator('[data-compare]').nth(1).check();page.locator('[data-action=compare]').click();check('Comparison renders',page.locator('.compare-column').count()==2);page.keyboard.press('Escape')
 page.locator('[data-action=save-view]').last.click();page.locator('#view-name').fill('Test view');page.locator('[data-action=commit-view]').click();check('Saved view works in memory',page.locator('[data-load-view]').count()==1)
 page.locator('[data-action=filters]').click();page.locator('#f-collection').select_option('Dark fantasy');check('Collection facet',page.evaluate('GamesTest.filtered.length<GamesTest.count'));page.locator('[data-action=reset]').first.click();page.locator('[data-action=filters]').click();page.screenshot(path=str(out/'desktop-inline.png'))
 page.set_viewport_size({'width':390,'height':844});check('Narrow layout no overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'mobile-inline.png'));page.locator('[data-action=menu]').click();check('Mobile navigation opens',page.locator('body').evaluate("e=>e.classList.contains('menu-open')"));page.locator('[data-shelf=favorites]').click();check('Saved shelf filters',page.locator('.game-card').count()==1)
 check('No JavaScript errors',not report['errors']);b.close()
report['passed']=True;(out/'inline-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
