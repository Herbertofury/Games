"""Protect deep-linked startup and upstream cache invalidation across hub overlays."""
from __future__ import annotations
import json,os,pathlib,shutil,socket,subprocess,sys,time,urllib.parse
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];Q=R/'qa';Q.mkdir(exist_ok=True)
catalog=json.loads((R/'data/catalog.json').read_text())
report={'sourceRevision':os.environ.get('GITHUB_SHA'),'datasetHash':catalog['build']['datasetHash'],'checks':[],'routes':{},'errors':[]}
server=subprocess.Popen([sys.executable,'-m','http.server','8791','--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def check(name,condition):
 if not condition:raise AssertionError(name)
 report['checks'].append(name)
try:
 for _ in range(40):
  with socket.socket() as sock:
   if sock.connect_ex(('127.0.0.1',8791))==0:break
  time.sleep(.1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
  for hub,field in [('Platformers','platformerCollection'),('Survival','survivalCollection'),('Minecraft-like worlds','survivalCollection')]:
   expected={}
   for g in catalog['items']:
    if hub in g['hubs']:expected[g[field]]=expected.get(g[field],0)+1
   page=browser.new_page(viewport={'width':1536,'height':1100},reduced_motion='reduce');page.on('pageerror',lambda e:report['errors'].append(str(e)))
   page.goto('http://127.0.0.1:8791/#hub='+urllib.parse.quote(hub),wait_until='domcontentloaded');page.wait_for_function('window.GamesTest')
   def routes():return page.locator('#collections [data-collection]').evaluate_all('(xs)=>Object.fromEntries(xs.map(x=>[x.dataset.collection,Number(x.querySelector("b").textContent)]))')
   check(hub+' direct-link counter uses primary routes',int(page.locator('#stat-collections').inner_text())==len(expected))
   check(hub+' direct-link sidebar has exact route memberships',routes()==expected)
   page.evaluate('window.savedHubNode=document.querySelector("#collections").firstElementChild;render()')
   check(hub+' unchanged render reuses existing sidebar DOM',page.evaluate('window.savedHubNode===document.querySelector("#collections").firstElementChild'))
   page.evaluate('renderedHub=undefined;render()')
   check(hub+' upstream invalidation restores exact route count',int(page.locator('#stat-collections').inner_text())==len(expected))
   check(hub+' upstream invalidation restores exact memberships',routes()==expected)
   page.locator('[data-hub="Roguelites"]').click();page.locator('[data-hub="'+hub+'"]').click()
   check(hub+' switching away and back retains the same primary routes',routes()==expected)
   report['routes'][hub]=expected;page.close()
  check('No uncaught startup or invalidation errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(Q/'hub-bootstrap-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
