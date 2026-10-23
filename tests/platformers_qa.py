"""Production-browser platformer acceptance with explicit media evidence."""
from __future__ import annotations
import contextlib,csv,json,os,pathlib,shutil,socket,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'qa';OUT.mkdir(exist_ok=True)
catalog=json.loads((R/'data/catalog.json').read_text());by={g['id']:g for g in catalog['items']};rows=[g for g in by.values() if 'Platformers' in g.get('hubs',[])]
report={'sourceRevision':os.environ.get('GITHUB_SHA'),'datasetHash':catalog['build']['datasetHash'],'records':len(rows),'checks':[],'errors':[],'details':[],'images':[],'playback':[]}
def check(name,ok):
 if not ok:raise AssertionError(name)
 report['checks'].append(name)
port=8787;server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(50):
  with contextlib.closing(socket.socket()) as sock:
   if sock.connect_ex(('127.0.0.1',port))==0:break
  time.sleep(.1)
 baseline=OUT/'platformers-baseline.json'
 if baseline.exists():
  old=json.loads(baseline.read_text())['items'];check('Every pre-existing stable identity survives',all(g['id'] in by for g in old))
  fields=['name','image','screenshots','trailers','storefronts','sources','requirements','rtsInfo','curatorWhy']
  for g in old:
   for field in fields:check('Preserved '+g['id']+' '+field,by[g['id']].get(field)==g.get(field))
  report['preservedOriginalRecords']=len(old)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox'])
  ctx=browser.new_context(viewport={'width':1536,'height':1100},reduced_motion='reduce',accept_downloads=True);page=ctx.new_page();page.set_default_timeout(20000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
  url=f'http://127.0.0.1:{port}/';page.goto(url+'#hub=Platformers',wait_until='domcontentloaded');page.wait_for_function('window.GamesTest && document.querySelector(".platformer-guide")')
  check('Direct platformer deep link renders all records',len(page.evaluate('GamesTest.filtered'))==len(rows))
  check('All platformer cards are in the DOM',page.locator('.game-card').count()==len(rows))
  check('Distinct platformer hub and guide',page.locator('body').get_attribute('data-hub')=='platformers' and page.locator('.platformer-guide').is_visible())
  check('Celeste is the movement benchmark',page.locator('#hero-title').inner_text()=='Celeste')
  check('Counter reflects the actual accepted source set',int(page.locator('#stat-games').inner_text())==len(rows))
  for route in ['precision','3d','exploration','puzzles','coop','gems','free','upcoming']:
   page.locator('[data-platformer-route="'+route+'"]').click();selected=page.evaluate('GamesTest.filtered');check(route+' route is populated',bool(selected));check(route+' stays in the platformer hub',page.evaluate('GamesTest.state.hub')=='Platformers')
   if route=='upcoming':check('Watchlist contains only genuinely upcoming records',all(by[i].get('comingSoon') and by[i].get('fit') is None for i in selected))
   if route=='gems':check('Gem route uses the constrained editorial shortlist',all('Platformer gem shortlist' in by[i]['tags'] for i in selected))
  page.locator('[data-hub="Platformers"]').click();page.locator('[data-view=table]').click();check('Table contains every accepted platformer',page.locator('tbody tr').count()==len(rows));page.locator('[data-view=gallery]').click();check('Gallery retains the complete set',len(page.evaluate('GamesTest.filtered'))==len(rows));page.locator('[data-view=grid]').click()
  page.locator('#search').fill('top-down');check('Scope and editorial notes are searchable','steam:2394650' in page.evaluate('GamesTest.filtered'));page.locator('#search').fill('')
  # Production detail rendering for every record. Actual stream playback is a
  # separate sampled test below, not falsely claimed for every video URL.
  for g in rows:
   result=page.evaluate('''id=>{openGame(id);return {title:document.querySelector('.modal-banner h2')?.textContent,brief:!!document.querySelector('.platformer-brief'),text:document.querySelector('.platformer-brief')?.textContent,links:[...document.querySelectorAll('.storefronts a')].map(a=>a.href),hasMedia:!!document.querySelector('#media-section'),rating:document.querySelector('.detail-stats')?.textContent};}''',g['id'])
   assert result['title']==g['name'],g['id'];assert result['brief'] and result['hasMedia'],g['id'];assert set(result['links'])=={s['url'] for s in g['storefronts']},g['id']
   for platform in g.get('platforms',[]):assert platform in result['text'],(g['id'],platform)
   if not g.get('steamUrl'):assert '% positive' not in result['rating'],g['id']
   report['details'].append({'id':g['id'],'sources':result['links'],'scope':g['platformerInfo']['focus']})
   page.evaluate('closeModal()')
  check('Every detail renders correct identity, hardware, scope and source links',len(report['details'])==len(rows))
  image_rows=[{'id':g['id'],'image':g['image']} for g in rows if g.get('image')]
  decode='''async rows=>{const out=[];let next=0;async function work(){while(next<rows.length){const g=rows[next++];out.push(await new Promise(resolve=>{const im=new Image(),timer=setTimeout(()=>resolve({id:g.id,url:g.image,ok:false,error:'timeout'}),18000);im.onload=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:im.naturalWidth>0,width:im.naturalWidth,height:im.naturalHeight})};im.onerror=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:false,error:'network/decode'})};im.src=g.image}))}}await Promise.all(Array.from({length:6},work));return out;}'''
  report['images']=page.evaluate(decode,image_rows)
  failed={x['id'] for x in report['images'] if not x['ok']}
  if failed:
   retried={x['id']:x for x in page.evaluate(decode,[g for g in image_rows if g['id'] in failed])};report['images']=[retried.get(x['id'],x) for x in report['images']]
  report['declaredArtworkGaps']=[g['id'] for g in rows if not g.get('image')]
  check('Every declared primary artwork decodes from real remote bytes',all(x['ok'] for x in report['images']))
  for ident in ['steam:504230','steam:1672810']:
   page.evaluate('(id)=>openGame(id)',ident);page.wait_for_function("document.querySelector('#media-video')?.currentSrc.length>0",timeout=30000)
   page.evaluate("document.querySelector('#media-video').muted=true;document.querySelector('#media-video').play().catch(e=>window.platformerPlaybackError=String(e))")
   page.wait_for_function("document.querySelector('#media-video')?.currentTime>1",timeout=35000)
   result=page.locator('#media-video').evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,duration:v.duration,src:v.currentSrc})');result['id']=ident;result['officialSource']=by[ident]['steamUrl'];report['playback'].append(result);check(ident+' actual trailer advances with decoded frames',result['time']>1 and result['width']>0);page.evaluate('closeModal()')
  # A new hub must not reset the existing personal-library identity.
  for ident,note in [('steam:2218750','Original genre retained during platformer QA'),('steam:504230','Platformer QA private note')]:
   page.evaluate('(id)=>openGame(id)',ident);page.locator('#game-notes').fill(note);page.locator('#personal-rating').select_option('9');page.locator('.detail-save').click();page.evaluate('closeModal()')
  page.reload(wait_until='domcontentloaded')
  for ident,note in [('steam:2218750','Original genre retained during platformer QA'),('steam:504230','Platformer QA private note')]:
   page.evaluate('(id)=>openGame(id)',ident);check(ident+' notes and rating survive reload',page.locator('#game-notes').input_value()==note and page.locator('#personal-rating').input_value()=='9');check(ident+' favorite survives reload',ident in page.evaluate('GamesTest.personal.favorites'));page.evaluate('closeModal()')
  for hub in ['Roguelites','Boomer shooters','Real-time strategy','Platformers']:
   page.locator('[data-hub="'+hub+'"]').click();check(hub+' full count preserved',len(page.evaluate('GamesTest.filtered'))==catalog['build']['hubCounts'][hub])
  page.locator('[data-action=export]').click()
  with page.expect_download() as dl:page.locator('[data-export=csv]').click()
  dest=OUT/'platformers-export.csv';dl.value.save_as(str(dest));export=list(csv.DictReader(dest.open(encoding='utf-8-sig')));check('CSV exports the entire selected platformer hub',len(export)==len(rows));page.keyboard.press('Escape')
  page.locator('[data-hub="Platformers"]').click();page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(500);page.screenshot(path=str(OUT/'platformers-desktop.png'))
  page.evaluate("openGame('steam:1672810')");page.screenshot(path=str(OUT/'platformers-detail.png'));page.evaluate('closeModal()')
  page.set_viewport_size({'width':390,'height':844});page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/'platformers-mobile.png'));check('Mobile platformer hub has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  page.evaluate("openGame('external:donkey-kong-bananza')");check('Mobile console detail keeps hardware requirements','Nintendo Switch 2' in page.locator('.platformer-brief').inner_text());page.screenshot(path=str(OUT/'platformers-console-detail.png'));page.evaluate('closeModal()')
  portable=ctx.new_page();portable.on('pageerror',lambda e:report['errors'].append(str(e)));portable.goto((R/'release/Games - Explorer.html').as_uri()+'#hub=Platformers',wait_until='domcontentloaded');portable.wait_for_function('window.GamesTest && document.querySelector(".platformer-guide")');check('Portable HTML has the complete platformer hub',len(portable.evaluate('GamesTest.filtered'))==len(rows));portable.close()
  check('No uncaught JavaScript errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(OUT/'platformers-qa.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['details','images','checks']},indent=2));print('Checks:',len(report['checks']))
