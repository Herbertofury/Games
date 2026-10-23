"""Real-browser regression for genre additions and public creator media."""
import contextlib,csv,json,os,pathlib,shutil,socket,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];out=R/'qa';out.mkdir(exist_ok=True)
data=json.loads((R/'data/catalog.json').read_text());by={g['id']:g for g in data['items']};expected=sum('Boomer shooters' in g.get('hubs',[]) for g in by.values())
port=8781;server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
report={'checks':[],'errors':[],'shooterCount':expected,'datasetHash':data['build']['datasetHash']}
def check(n,c):
 if not c:raise AssertionError(n)
 report['checks'].append(n)
try:
 for _ in range(30):
  with contextlib.closing(socket.socket()) as s:
   if s.connect_ex(('127.0.0.1',port))==0:break
  time.sleep(.1)
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1536,'height':1100},accept_downloads=True,reduced_motion='reduce');page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.set_default_timeout(15000)
  url=f'http://127.0.0.1:{port}/';page.goto(url,wait_until='domcontentloaded');page.wait_for_function('window.GamesTest')
  page.locator('[data-hub="Roguelites"]').click();check('All 170 original recommendations remain in their genre',len(page.evaluate('GamesTest.filtered'))==170)
  page.locator('[data-hub="Boomer shooters"]').click();check('Shooter hub has every accepted record',page.locator('.game-card').count()==expected)
  page.locator('[data-action=filters]').click();check('Ordinary controls do not activate the body theme attribute as a genre',page.evaluate("GamesTest.state.hub==='Boomer shooters' && GamesTest.filtered.length==="+str(expected)));page.locator('#f-provider').select_option('itch.io');ids=page.evaluate('GamesTest.filtered');check('Provider filter includes exact official alternate stores',bool(ids) and all(any(s['provider']=='itch.io' for s in by[i]['storefronts']) for i in ids))
  page.locator('#f-rating').select_option('90');ids=page.evaluate('GamesTest.filtered');check('Steam percentage filter does not invent non-Steam scores',all(by[i].get('steamUrl') and by[i]['rating']>=90 for i in ids))
  page.locator('#f-rating').select_option('0');page.locator('#f-hostRating').select_option('90');check('Native host ratings can be filtered without Steam conversion',bool(page.evaluate('GamesTest.filtered')) and all(by[i].get('externalRating',{}).get('value',0)/by[i].get('externalRating',{}).get('max',1)>=.9 for i in page.evaluate('GamesTest.filtered')));page.locator('#f-hostRating').select_option('0');page.locator('#f-provider').select_option('Patreon');check('Patreon support is discoverable without fake access claims',len(page.evaluate('GamesTest.filtered'))>=6)
  page.locator('#f-provider').select_option('');page.locator('#f-kind').select_option('Mod / expansion');check('Mod filter excludes unrelated standalone games',all(by[i]['kind']=='Mod / expansion' for i in page.evaluate('GamesTest.filtered')))
  page.locator('#f-kind').select_option('');page.locator('#f-status').select_option('Demo');check('Demos are separate from full releases',all(by[i]['status']=='Demo' for i in page.evaluate('GamesTest.filtered')))
  page.locator('#f-status').select_option('');page.locator('#f-offSteam').check();check('Beyond-Steam view contains real non-support alternatives',all(any(s['provider']!='Steam' and s['kind']!='support' for s in by[i]['storefronts']) for i in page.evaluate('GamesTest.filtered')))
  page.goto(url+'#game=external%3Agolden-souls-2',wait_until='domcontentloaded');check('External deep link opens exact game',page.locator('.modal-banner h2').inner_text()=='Doom: The Golden Souls 2')
  check('Base-game requirement is prominent','DOOM2.WAD' in page.locator('.requirements').inner_text());check('Support is separated from buying','Membership does not automatically' in page.locator('.support-note').inner_text());check('Native five-star rating remains a five-star rating','/ 5' in page.locator('.detail-stats').inner_text())
  page.locator('#game-notes').fill('External record persistence regression');page.locator('#personal-rating').select_option('8');page.locator('.detail-save').click();page.reload(wait_until='domcontentloaded');check('External notes survive reload',page.locator('#game-notes').input_value()=='External record persistence regression');check('External favorite survives reload','external:golden-souls-2' in page.evaluate('GamesTest.personal.favorites'))
  page.screenshot(path=str(out/'shooters-external-detail.png'))
  # Validate opt-in behavior with actual publisher-provided video IDs; no fabricated player.
  yt=next((g for g in by.values() if not g.get('steamUrl') and any(t.get('youtube') for t in g['trailers'])),None)
  if yt:
   page.goto(url+'#game='+yt['id'],wait_until='domcontentloaded');page.locator('[data-media-mode=trailer]').click();check('Creator video requires user activation',page.locator('.trailer-frame').count()==0 and page.locator('[data-youtube]').count()==1)
   vid=page.locator('[data-youtube]').get_attribute('data-youtube');page.locator('[data-youtube]').click();check('Actual official YouTube ID passed to privacy-enhanced player',page.locator('.trailer-frame').get_attribute('src').startswith('https://www.youtube-nocookie.com/embed/'+vid));page.keyboard.press('Escape');check('Closing detail disposes the external player',page.locator('.trailer-frame').count()==0)
  else:report['creatorVideoNote']='No publisher-provided embeddable video IDs were available; no playback claim.'
  page.keyboard.press('Escape');page.locator('[data-hub="Boomer shooters"]').click();page.locator('#search').fill('provider:itch.io');check('Provider query operator works',len(page.evaluate('GamesTest.filtered'))>0)
  page.locator('[data-action=export]').click()
  with page.expect_download() as dl:page.locator('[data-export=csv]').click()
  target=out/'multiplatform.csv';dl.value.save_as(str(target));rows=list(csv.DictReader(target.open(encoding='utf-8-sig')));check('CSV exports correct external URLs and native ratings',any(r['Official URL'].startswith('https://batandy.itch.io/') and r['Native scale']=='5' for r in rows));page.keyboard.press('Escape')
  page.locator('[data-hub="Boomer shooters"]').click();page.wait_for_timeout(700);page.screenshot(path=str(out/'shooters-desktop.png'));check('Shooter hero uses its own art and accent',page.locator('body').get_attribute('data-hub')=='shooters')
  # Measure the actual full-record render; records are never virtualized.
  ms=page.evaluate("() => {const t=performance.now(); render(); return performance.now()-t;}");report['fullShooterRenderMs']=round(ms,2);check('All records still present after measured render',page.locator('.game-card').count()==expected)
  page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'shooters-mobile.png'));check('New genre mobile layout has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  page.goto(url+'#game=external%3Aproject-osiris',wait_until='domcontentloaded');check('Mobile external requirements remain visible',page.locator('.requirements').count()==1);check('No JavaScript runtime errors',not report['errors']);b.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(out/'multiplatform-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
