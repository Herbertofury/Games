"""Consent/identity/browser regression for the official widget. No account writes."""
import contextlib,json,os,pathlib,shutil,socket,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];Q=R/'qa';Q.mkdir(exist_ok=True)
report={'scope':'Real Chromium, fixture widget content; no real Steam account or purchase/wishlist mutation.','checks':[],'errors':[]}
def check(name,value):
 if not value:raise AssertionError(name)
 report['checks'].append(name)
server=subprocess.Popen([sys.executable,'-m','http.server','8793','--bind','127.0.0.1','--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(60):
  with contextlib.closing(socket.socket()) as sock:
   if sock.connect_ex(('127.0.0.1',8793))==0:break
  time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce',service_workers='block')
  widget_requests=[]
  def route(r):
   if r.request.url.startswith('https://store.steampowered.com/widget/'):
    widget_requests.append(r.request.url)
    r.fulfill(status=200,content_type='text/html',body='<!doctype html><title>Test widget only</title><p>Fixture for Valve widget placement. No account action.</p>')
   elif r.request.url.startswith('http://127.0.0.1:8793/') or r.request.url.startswith('file:'):r.continue_()
   else:r.abort()
  context.route('**/*',route)
  page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
  page.goto('http://127.0.0.1:8793/',wait_until='domcontentloaded');page.wait_for_selector('#steam-filter')
  check('No third-party widget loads on startup',not widget_requests)
  copies=page.evaluate("""()=>{const original=GamesSteamContext;let count=0;window.GamesSteamContext=()=>{count++;return original();};render();window.GamesSteamContext=original;return count;}""")
  check('Ownership index is copied once per render, not once per card',copies==1)
  page.goto('http://127.0.0.1:8793/#game=steam%3A504230',wait_until='domcontentloaded')
  # A hash-only navigation is not a fresh boot. Force the actual startup path.
  page.reload(wait_until='domcontentloaded')
  page.wait_for_selector('#modal[open] .steam-wishlist-section')
  check('Initial game deep link includes Steam snapshot and actions',page.locator('#modal .steam-game-brief').count()==1 and page.locator('#modal [data-steam-widget="504230"]').count()==1)
  check('Initial detail deep link still waits for widget consent',not widget_requests)
  page.evaluate('closeModal()');page.evaluate("openGame('steam:504230')")
  check('Detail asks before loading Steam',page.locator('[data-steam-widget="504230"]').count()==1 and not widget_requests)
  before=page.evaluate("localStorage.getItem('games.steam.v1')")
  button=page.locator('[data-steam-widget="504230"]');button.focus();page.keyboard.press('Enter')
  page.wait_for_function("!!document.querySelector('.steam-widget-slot iframe')")
  frame=page.locator('.steam-widget-slot iframe');frame.scroll_into_view_if_needed()
  page.wait_for_timeout(500)
  check('Exact app widget requested only after keyboard activation',widget_requests==['https://store.steampowered.com/widget/504230/?l=english'])
  check('Embed remains isolated and suppresses referrer',frame.get_attribute('referrerpolicy')=='no-referrer' and 'allow-top-navigation-by-user-activation' in frame.get_attribute('sandbox'))
  check('Loading widget never fabricates wishlist membership',page.evaluate("localStorage.getItem('games.steam.v1')")==before)
  check('Reloading button cannot duplicate frames',button.is_disabled() and page.locator('.steam-widget-slot iframe').count()==1)
  page.screenshot(path=str(Q/'steam-widget-desktop.png'));page.evaluate('closeModal()')
  page.evaluate("openGame('external:astro-bot')")
  check('Non-Steam record never receives a guessed Steam widget',page.locator('[data-steam-widget]').count()==0);page.evaluate('closeModal()')
  page.set_viewport_size({'width':390,'height':844});page.evaluate("openGame('steam:504230')")
  page.locator('[data-steam-widget="504230"]').click();frame=page.locator('.steam-widget-slot iframe');frame.scroll_into_view_if_needed()
  check('Mobile widget fits its parent without page overflow',frame.evaluate('(f)=>f.getBoundingClientRect().width<=f.parentElement.getBoundingClientRect().width+1') and page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  page.screenshot(path=str(Q/'steam-widget-mobile.png'));page.evaluate('closeModal()')
  page.set_viewport_size({'width':1440,'height':1000})
  for hub,count in page.evaluate('CATALOG.build.hubCounts').items():
   page.locator('[data-hub="'+hub+'"]').click()
   check('Existing '+hub+' retains every record',len(page.evaluate('GamesTest.filtered'))==count)
  offline=context.new_page();offline.on('pageerror',lambda e:report['errors'].append(str(e)))
  offline.goto((R/'release/Games - Explorer.html').as_uri()+'#game=steam%3A504230',wait_until='domcontentloaded');offline.wait_for_selector('#steam-filter')
  check('Portable initial game deep link includes Steam actions',offline.locator('#modal [data-steam-widget="504230"]').count()==1)
  offline.evaluate('closeModal()');offline.locator('.heading-actions [data-steam-action=open]').click()
  check('Portable HTML retains local imports and disabled online sign-in',offline.locator('#steam-file').is_visible() and offline.locator('[data-steam-action=signin]').is_disabled())
  check('No uncaught errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5)
 (Q/'steam-widget-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
