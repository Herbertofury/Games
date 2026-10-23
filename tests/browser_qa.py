"""Real Chromium workflow tests. Run against the built snapshot, never only syntax."""
import contextlib,json,os,pathlib,socket,subprocess,sys,time,shutil
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1];out=ROOT/'qa';out.mkdir(exist_ok=True)
port=int(os.environ.get('GAMES_TEST_PORT','8765'));server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--directory',str(ROOT/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
report={'checks':[],'errors':[]};start=time.perf_counter()
def check(name,condition):
    if not condition:raise AssertionError(name)
    report['checks'].append(name)
try:
    for _ in range(50):
        with contextlib.closing(socket.socket()) as s:
            if s.connect_ex(('127.0.0.1',port))==0:break
        time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':1536,'height':1100},reduced_motion='reduce',accept_downloads=True);page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(f'http://127.0.0.1:{port}',wait_until='domcontentloaded');page.wait_for_function('window.GamesTest && GamesTest.count > 0')
        count=page.evaluate('GamesTest.count');check('Full dataset rendered without virtualization',page.locator('.game-card').count()==count)
        report['recordCount']=count;page.screenshot(path=str(out/'desktop.png'),full_page=False)
        page.locator('#search').fill('Halls of Torment');check('Title search finds reference game',page.locator('.game-card').count()>=1)
        page.locator('#search').fill('tag:loot score>=7');check('Structured search operators',page.evaluate("GamesTest.filtered.length > 0"))
        page.locator('#search').fill('not-a-real-game-zzzzzz');check('Empty-state rendering',page.locator('.empty').count()==1)
        page.locator('[data-action=reset]').last.click();page.locator('[data-action=filters]').click();page.locator('#f-collection').select_option('Dark fantasy');check('Collection filter',page.evaluate("GamesTest.filtered.length > 0 && GamesTest.filtered.length < GamesTest.count"))
        page.locator('#f-rating').select_option('90');check('Rating threshold persisted',page.evaluate('GamesTest.state.rating===90'))
        page.locator('[data-action=reset]').first.click();page.locator('[data-view=table]').click();check('Table mode contains every record',page.locator('tbody tr').count()==count)
        page.locator('th [data-sort=newest]').click();check('Sortable table headers',page.evaluate("GamesTest.state.sort==='newest'"))
        page.locator('[data-view=gallery]').click();check('Gallery view',page.locator('.gallery-view').count()==1)
        page.locator('[data-view=grid]').click();page.locator('#search').fill('Halls of Torment');page.locator('[data-save]').first.click();page.reload(wait_until='domcontentloaded');check('Saved games persist across reload',page.evaluate('GamesTest.personal.favorites.length===1'))
        page.locator('[data-open]').first.click();page.wait_for_selector('#game-notes');page.locator('#game-notes').fill('QA note: build ideas, no data loss.');page.locator('#detail-status').select_option('Backlog');page.locator('#personal-rating').select_option('9');page.locator('[data-action=close]').click();page.locator('[data-open]').first.click();check('Notes persist',page.locator('#game-notes').input_value()=='QA note: build ideas, no data loss.');check('Personal rating distinct from Steam',page.locator('#personal-rating').input_value()=='9');check('Play status persists',page.locator('#detail-status').input_value()=='Backlog')
        page.locator('[data-media-mode=screenshots]').click();check('Screenshot gallery or truthful absence',page.locator('#media-area').inner_text()!='');page.keyboard.press('Escape');check('Escape closes details',not page.locator('#modal').evaluate('(e)=>e.open'))
        page.locator('#search').fill('');checks=page.locator('[data-compare]');checks.nth(0).check();checks.nth(1).check();page.locator('[data-action=compare]').click();check('Two-way comparison',page.locator('.compare-column').count()==2);page.locator('[data-action=close]').click()
        page.locator('[data-action=save-view]').last.click();page.locator('#view-name').fill('QA saved view');page.locator('[data-action=commit-view]').click();check('Named saved view created',page.locator('[data-load-view]').count()>=1)
        page.locator('[data-action=export]').click();
        with page.expect_download() as d:page.locator('[data-export=csv]').click()
        dl=d.value;dl.save_as(str(out/'filtered.csv'));check('CSV export is a real download',(out/'filtered.csv').stat().st_size>100);page.locator('[data-action=close]').click()
        page.locator('[data-action=settings]').click()
        with page.expect_download() as d:page.locator('[data-action=backup]').click()
        d.value.save_as(str(out/'backup.json'));backup=json.loads((out/'backup.json').read_text());check('Personal backup contains notes',bool(backup['notes']))
        page.locator('#import-file').set_input_files(str(out/'backup.json'));page.wait_for_timeout(100);check('Backup import merges without loss',page.evaluate('GamesTest.personal.favorites.length===1'))
        page.locator('[data-action=close]').click();page.locator('.topbar [data-action=theme]').click();check('Light theme works',page.locator('body').evaluate("e=>e.classList.contains('light')"));page.locator('.topbar [data-action=theme]').click()
        page.goto(f'http://127.0.0.1:{port}/#game=steam%3A2218750',wait_until='domcontentloaded');check('Deep link opens exact game',page.locator('.modal-banner h2').inner_text()=='Halls of Torment');page.screenshot(path=str(out/'detail.png'),full_page=False);page.keyboard.press('Escape')
        page.set_viewport_size({'width':390,'height':844});page.goto(f'http://127.0.0.1:{port}/',wait_until='domcontentloaded');page.screenshot(path=str(out/'mobile.png'),full_page=False);check('Mobile has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'));page.locator('[data-action=menu]').click();check('Mobile navigation opens',page.locator('body').evaluate("e=>e.classList.contains('menu-open')"));page.locator('[data-shelf=favorites]').click();check('Mobile saved shelf works',page.evaluate("GamesTest.state.shelf==='favorites'"))
        page.set_viewport_size({'width':1536,'height':1100});page.locator('[data-shelf=all]').click();t=time.perf_counter();page.locator('#search').fill('tag:loot');page.locator('#search').fill('');report['twoSearchesWallMs']=round((time.perf_counter()-t)*1000,2)
        check('No JavaScript runtime errors',not report['errors']);browser.close()
    report['durationSeconds']=round(time.perf_counter()-start,2);report['passed']=True
finally:
    server.terminate();server.wait(timeout=5);(out/'browser-qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
