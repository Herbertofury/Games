"""Diagnostic only: mocked provider, no real Steam credentials or account writes."""
import contextlib,json,pathlib,shutil,socket,subprocess,sys,time,os,urllib.parse
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];Q=R/'qa';Q.mkdir(exist_ok=True)
trace=[];processes=[]
def path(url):
 u=urllib.parse.urlsplit(url);return u.netloc+u.path
try:
 processes=[subprocess.Popen([sys.executable,'-m','http.server','8791','--bind','127.0.0.1','--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL),subprocess.Popen(['node',str(R/'tests/steam-browser-service.mjs')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)]
 for port in [8791,8792]:
  for _ in range(60):
   with contextlib.closing(socket.socket()) as sock:
    if sock.connect_ex(('127.0.0.1',port))==0:break
   time.sleep(.1)
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context()
  def bind(page):
   page.on('pageerror',lambda e:trace.append({'pageerror':str(e)}))
   page.on('console',lambda m:trace.append({'console':m.text}) if any(x in m.text.lower() for x in ['content security','refused','blocked','opener','nonce']) else None)
  ctx.on('page',bind)
  ctx.on('request',lambda r:trace.append({'request':path(r.url),'method':r.method}) if '/auth/' in r.url or '/sync' in r.url or '/openid/' in r.url else None)
  ctx.on('response',lambda r:trace.append({'response':path(r.url),'status':r.status}) if '/auth/' in r.url or '/sync' in r.url or '/openid/' in r.url else None)
  def route(r):
   if r.request.url.startswith('https://steamcommunity.com/openid/login'):
    q=urllib.parse.parse_qs(urllib.parse.urlsplit(r.request.url).query);back=q['openid.return_to'][0]
    params={'openid.ns':'http://specs.openid.net/auth/2.0','openid.mode':'id_res','openid.op_endpoint':'https://steamcommunity.com/openid/login','openid.identity':'https://steamcommunity.com/openid/id/76561198000000001','openid.claimed_id':'https://steamcommunity.com/openid/id/76561198000000001','openid.return_to':back,'openid.response_nonce':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')+'probe','openid.assoc_handle':'test','openid.signed':'op_endpoint,claimed_id,identity,return_to,response_nonce,assoc_handle','openid.sig':'fixture-signature'}
    r.fulfill(status=302,headers={'Location':back+'&'+urllib.parse.urlencode(params)},body='')
   elif r.request.url.startswith('http://127.0.0.1:'):r.continue_()
   else:r.abort()
  ctx.route('**/*',route);page=ctx.new_page();page.goto('http://127.0.0.1:8791/',wait_until='domcontentloaded');page.wait_for_selector('#steam-filter')
  page.evaluate("window.GAMES_STEAM_CONFIG.serviceUrl='http://127.0.0.1:8792';")
  page.locator('.heading-actions [data-steam-action=open]').click();page.wait_for_timeout(800);page.locator('[data-steam-action=signin]').click();page.wait_for_timeout(8000)
  trace.append({'feedback':page.locator('#steam-sync-feedback').inner_text(),'pages':[path(p.url) for p in ctx.pages],'cookieNames':[x['name'] for x in ctx.cookies()]})
  for i,view in enumerate(ctx.pages):
   if view==page:continue
   trace.append({'popupText':view.locator('body').inner_text()[:1500]})
  page.screenshot(path=str(Q/'steam-auth-probe.png'));b.close()
finally:
 for proc in processes:proc.terminate()
 for proc in processes:proc.wait(timeout=5)
 (Q/'steam-auth-probe.json').write_text(json.dumps(trace,indent=2));print(json.dumps(trace,indent=2))
