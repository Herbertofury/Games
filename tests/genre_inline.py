import json,pathlib
from playwright.sync_api import sync_playwright
r=pathlib.Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1536,'height':1100});page.set_default_timeout(4000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda route:route.abort());page.set_content((r/'dist/index.html').read_text(),wait_until='domcontentloaded')
 print('INIT',page.locator('.game-card').count(),errors,flush=True)
 page.locator('[data-hub="Boomer shooters"]').click();print('BOOM',page.locator('.game-card').count(),errors,flush=True)
 page.locator('[data-hub="Roguelites"]').click();assert page.locator('.game-card').count()==page.evaluate("CATALOG.build.hubCounts.Roguelites")
 page.locator('[data-hub="Boomer shooters"]').click();page.locator('#search').fill('PAPERHEAD');print('SEARCH',page.locator('.game-card').count(),flush=True);page.locator('[data-open]').first.click();assert page.locator('.storefronts a').count()>0;page.keyboard.press('Escape');page.locator('#search').fill('');page.screenshot(path='/mnt/data/boomer-inline.png');assert not errors;print('PASS',flush=True);b.close()
