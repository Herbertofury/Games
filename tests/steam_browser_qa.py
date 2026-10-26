"""Real Chromium and real local backend; Steam upstream explicitly mocked."""
import contextlib,json,pathlib,shutil,socket,subprocess,sys,time,os,urllib.parse,urllib.request
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];Q=R/'qa';Q.mkdir(exist_ok=True)
report={'scope':'Real Chromium and backend with mocked Steam transport. Not a live Steam login or a remote wishlist mutation.','checks':[],'errors':[]}
servers=[subprocess.Popen([sys.executable,'-m','http.server','8791','--bind','127.0.0.1','--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL),subprocess.Popen(['node',str(R/'tests/steam-browser-service.mjs')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)]
def check(name,condition):
 if not condition:raise AssertionError(name)
 report['checks'].append(name)
def wait(port):
 for _ in range(80):
  with contextlib.closing(socket.socket()) as s:
   if s.connect_ex(('127.0.0.1',port))==0:return
  time.sleep(.1)
 raise RuntimeError('Test server did not start')
try:
 for port in [8791,8792]:wait(port)
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1050},reduced_motion='reduce',accept_downloads=True)
  sync_requests=[]
  def network(route):
   u=route.request.url
   if u=='http://127.0.0.1:8792/sync' and route.request.method=='POST':sync_requests.append(u)
   if u.startswith('https://steamcommunity.com/openid/login'):
    qs=urllib.parse.parse_qs(urllib.parse.urlsplit(u).query);back=qs['openid.return_to'][0];nonce=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+urllib.parse.urlsplit(back).query[-10:]
    params={'openid.ns':'http://specs.openid.net/auth/2.0','openid.mode':'id_res','openid.op_endpoint':'https://steamcommunity.com/openid/login','openid.identity':'https://steamcommunity.com/openid/id/76561198000000001','openid.claimed_id':'https://steamcommunity.com/openid/id/76561198000000001','openid.return_to':back,'openid.response_nonce':nonce,'openid.assoc_handle':'test','openid.signed':'op_endpoint,claimed_id,identity,return_to,response_nonce,assoc_handle','openid.sig':'fixture-signature'}
    route.fulfill(status=302,headers={'Location':back+'&'+urllib.parse.urlencode(params)},body='')
   elif u.startswith('http://127.0.0.1:'):route.continue_()
   else:route.abort()
  context.route('**/*',network)
  page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.clock.install();page.goto('http://127.0.0.1:8791/',wait_until='domcontentloaded');page.wait_for_selector('#steam-filter')
  page.evaluate("prefs.notes['steam:504230']='Personal note kept';prefs.favorites=['steam:504230'];persist();state={...defaults};render();")
  count=page.evaluate('games.length');check('Complete catalog remains present',page.locator('.game-card').count()==count)
  # Explicitly exercise the unconfigured fallback even on a configured release.
  page.evaluate("window.GAMES_STEAM_CONFIG.serviceUrl=''")
  page.locator('.heading-actions [data-steam-action=open]').click()
  check('Unconfigured sign-in is disabled honestly',page.locator('[data-steam-action=signin]').is_disabled())
  check('Local imports work without deployment',page.locator('#steam-file').is_visible())
  sample={'rgOwnedApps':[504230,367520],'rgWishlist':[1533420],'steamApiKey':'MUST-NOT-PERSIST','cookies':'MUST-NOT-PERSIST'}
  page.locator('#steam-file').set_input_files({'name':'steam.json','mimeType':'application/json','buffer':json.dumps(sample).encode()})
  page.locator('[data-steam-action=import]').click()
  check('Import is explicitly unauthenticated','not an authenticated account' in page.locator('.steam-account-state').inner_text())
  check('Only whitelisted fields are retained','MUST-NOT-PERSIST' not in page.evaluate("localStorage.getItem('games.steam.v1')"))
  page.locator('[data-steam-action=close]').click();page.locator('#steam-filter').select_option('owned');check('Exact AppID ownership filter',set(page.evaluate('GamesTest.filtered'))=={'steam:504230','steam:367520'})
  check('Owned badges appear on cards',page.locator('.steam-owned').count()==2)
  page.locator('[data-view=table]').click();check('Table ownership view',page.locator('tbody tr').count()==2 and page.locator('tbody .steam-owned').count()==2)
  page.locator('[data-view=grid]').click();page.locator('#steam-filter').select_option('wishlist');check('Wishlist matches the exact AppID',page.evaluate('GamesTest.filtered')==['steam:1533420'])
  page.locator('#steam-filter').select_option('unplayed');check('Missing playtime is not zero playtime',page.locator('.game-card').count()==0)
  page.locator('#steam-filter').select_option('all');page.locator('.heading-actions [data-steam-action=open]').click()
  before=page.evaluate("localStorage.getItem('games.steam.v1')")
  page.locator('#steam-file').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"response":{}}'})
  check('Invalid import is non-destructive',page.evaluate("localStorage.getItem('games.steam.v1')")==before)
  page.locator('[data-steam-action=close]').click();page.evaluate("window.GAMES_STEAM_CONFIG.serviceUrl='http://127.0.0.1:8792';")
  page.locator('.heading-actions [data-steam-action=open]').click();page.locator('[data-steam-action=signin]').click()
  page.wait_for_function("JSON.parse(localStorage.getItem('games.steam.v1')||'null')?.source==='steam' && JSON.parse(localStorage.getItem('games.steam.v1')).owned.items.length===3",timeout=20000)
  check('Popup, verified callback and PKCE exchange work with mocked Steam','Signed in through Steam' in page.locator('.steam-account-state').inner_text())
  check('Automatic sync has a visible opt-out',page.locator('#steam-auto-refresh').is_checked())
  page.locator('#steam-auto-refresh').uncheck()
  automatic_before=len(sync_requests)
  page.clock.fast_forward(310000)
  page.evaluate("window.dispatchEvent(new Event('focus'))")
  check('Disabled automatic sync makes no requests',len(sync_requests)==automatic_before)
  page.locator('#steam-auto-refresh').check()
  page.evaluate("window.dispatchEvent(new Event('focus'))")
  page.wait_for_function("!document.querySelector('[data-steam-action=sync]').disabled")
  check(f'Returning to Games refreshes an enabled session ({len(sync_requests)} requests; expected {automatic_before+1})',len(sync_requests)==automatic_before+1)
  page.evaluate("for(let i=0;i<20;i++)window.dispatchEvent(new Event('focus'))")
  check('Repeated focus events respect cooldown',len(sync_requests)==automatic_before+1)
  check('Tokens are not persisted',page.evaluate("!Object.hasOwn(JSON.parse(localStorage.getItem('games.steam.v1')),'token')"))
  check('Steam sync preserves personal notes and favorites',page.evaluate("prefs.notes['steam:504230']==='Personal note kept' && prefs.favorites.includes('steam:504230')"))
  page.locator('[data-steam-action=close]').click();page.locator('#steam-filter').select_option('unplayed');check('Explicit zero minutes matches',page.evaluate('GamesTest.filtered')==['steam:504230'])
  page.locator('#steam-filter').select_option('wishlist');page.locator('#sort').select_option('steam-priority');check('Priority zero sorts first',page.evaluate('GamesTest.filtered')[0]=='steam:2365810')
  page.locator('#steam-filter').select_option('all');page.locator('.heading-actions [data-steam-action=open]').click()
  urllib.request.urlopen('http://127.0.0.1:8792/test/privacy').read();page.locator('[data-steam-action=sync]').click();page.wait_for_function("JSON.parse(localStorage.getItem('games.steam.v1')).owned.stale===true")
  check('Failed refresh retains last-known library',page.evaluate("JSON.parse(localStorage.getItem('games.steam.v1')).owned.items.length===3"))
  page.locator('[data-steam-action=close]').click();page.locator('#steam-filter').select_option('all')
  link=page.locator('[data-steam-store-wishlist="1533420"]').first
  check('Wishlist action goes to the exact official Steam app',link.get_attribute('href')=='https://store.steampowered.com/app/1533420/')
  check('Wishlist handoff cannot claim a remote write',page.locator('[data-steam-wishlist]').count()==0)
  before=page.evaluate("localStorage.getItem('games.steam.v1')")
  with page.expect_popup() as popup:link.click()
  popup.value.close();check('Opening Steam does not alter membership',page.evaluate("localStorage.getItem('games.steam.v1')")==before)
  check('Handoff feedback explains the remaining Steam confirmation','No Steam change is assumed' in page.locator('.steam-action-feedback').inner_text())
  page.locator('.heading-actions [data-steam-action=open]').click();page.screenshot(path=str(Q/'steam-sync-desktop.png'))
  page.locator('[data-steam-action=close]').click();page.locator('#steam-filter').select_option('owned');page.screenshot(path=str(Q/'steam-owned-desktop.png'))
  page.set_viewport_size({'width':390,'height':844});page.locator('.heading-actions [data-steam-action=open]').click();page.screenshot(path=str(Q/'steam-sync-mobile.png'))
  check('Mobile dialog fits viewport',page.evaluate("document.querySelector('#steam-sync-panel').getBoundingClientRect().width<=innerWidth && document.querySelector('#steam-sync-panel').scrollWidth<=document.querySelector('#steam-sync-panel').clientWidth+1"))
  page.locator('[data-steam-action=close]').click();page.reload(wait_until='domcontentloaded');page.wait_for_selector('#steam-filter');check('Snapshot survives reload',page.evaluate("JSON.parse(localStorage.getItem('games.steam.v1')).owned.items.length===3"))
  page.locator('.heading-actions [data-steam-action=open]').click();check('Session is not invented after reload',page.locator('[data-steam-action=sync]').is_disabled())
  page.on('dialog',lambda d:d.accept());page.locator('[data-steam-action=disconnect]').click();check('Disconnect clears only Steam data',page.evaluate("!localStorage.getItem('games.steam.v1') && prefs.notes['steam:504230']==='Personal note kept' && prefs.favorites.includes('steam:504230')"))
  check('No JavaScript runtime errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 for server in servers:server.terminate()
 for server in servers:server.wait(timeout=5)
 (Q/'steam-sync-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
