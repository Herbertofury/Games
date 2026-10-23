"""Production Chromium acceptance for every RTS record, real images and media."""
import concurrent.futures,contextlib,json,os,pathlib,shutil,socket,subprocess,sys,time,urllib.parse,urllib.request
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'qa';OUT.mkdir(exist_ok=True)
catalog=json.loads((R/'data/catalog.json').read_text());rows=[g for g in catalog['items'] if 'Real-time strategy' in g.get('hubs',[])];by={g['id']:g for g in rows}
report={'sourceRevision':os.environ.get('GITHUB_SHA'),'datasetHash':catalog['build']['datasetHash'],'records':len(rows),'checks':[],'errors':[],'details':[],'images':[],'playback':[]}
def check(name,condition):
 if not condition:raise AssertionError(name)
 report['checks'].append(name)
port=8785;server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(40):
  with contextlib.closing(socket.socket()) as s:
   if s.connect_ex(('127.0.0.1',port))==0:break
  time.sleep(.1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox'])
  ctx=browser.new_context(viewport={'width':1536,'height':1100},accept_downloads=True,reduced_motion='reduce');page=ctx.new_page();page.set_default_timeout(15000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
  url=f'http://127.0.0.1:{port}/';page.goto(url,wait_until='domcontentloaded');page.wait_for_function('window.GamesTest')
  for hub,count in [('Roguelites',170),('Boomer shooters',150),('Real-time strategy',130)]:
   page.locator('[data-hub="'+hub+'"]').click();check(hub+' count preserved',page.locator('.game-card').count()==count)
  check('Distinct command-center theme',page.locator('body').get_attribute('data-hub')=='rts')
  for preset in ['torment','generals','skirmish','free-rts','watchlist','new','demos']:
   page.locator('[data-preset="'+preset+'"]').click();ids=page.evaluate('GamesTest.filtered');check(preset+' shelf has results',bool(ids))
   if preset=='torment':check('Closest matches exclude no-base tactical neighbors',all('Zero Hour-like' in by[i]['tags'] and not by[i].get('comingSoon') for i in ids))
   if preset=='generals':check('Zero Hour mod shelf contains all four overhauls',set(ids)=={'external:contra-x','external:cc-shockwave','external:rise-of-the-reds','external:end-of-days-zh'})
   if preset=='watchlist':check('All six unreleased projects are separate',len(ids)==6 and all(by[i]['comingSoon'] for i in ids))
   if preset=='new':check('Fresh releases do not relabel old classics',all(by[i].get('originalReleaseYear',2026)>=2025 and not by[i].get('comingSoon') for i in ids))
   if preset=='demos':check('Demo shelf includes exact demo editions',all(by[i].get('demoAppids') or by[i]['status']=='Demo' or any(l['kind']=='demo' for l in by[i]['storefronts']) for i in ids))
  page.locator('[data-hub="Real-time strategy"]').click();page.locator('[data-action=filters]').click();page.locator('#f-provider').select_option('GOG');ids=page.evaluate('GamesTest.filtered');check('GOG filter uses exact distribution links',bool(ids) and all(any(l['provider']=='GOG' for l in by[i]['storefronts']) for i in ids));page.locator('[data-action=filters]').click();page.locator('[data-hub="Real-time strategy"]').click()
  page.locator('#search').fill('"zero hour"');check('Exact-phrase RTS search',bool(page.evaluate('GamesTest.filtered')));page.locator('#search').fill('')
  page.locator('[data-view=table]').click();check('All RTS table rows available',page.locator('tbody tr').count()==130);page.locator('[data-view=gallery]').click();check('Gallery keeps all records',len(page.evaluate('GamesTest.filtered'))==130);page.locator('[data-view=grid]').click()
  report['renderMs']=page.evaluate('() => {const a=[];for(let i=0;i<5;i++){const t=performance.now();render();a.push(performance.now()-t)}return a}')
  check('Measured render does not cull records',page.locator('.game-card').count()==130)
  for g in rows:
   page.evaluate('(id)=>openGame(id)',g['id']);page.locator('.media-source-line a').wait_for()
   hrefs=page.locator('.storefronts a').evaluate_all('(xs)=>xs.map(x=>x.href)');assert set(hrefs)=={x['url'] for x in g['storefronts']},(g['name'],'source links differ')
   assert page.locator('.rts-brief').count()==1,(g['name'],'commander brief missing')
   assert page.locator('#media-video,.youtube-consent').count()==1,(g['name'],'embedded player missing')
   assert page.locator('.media-source-line a').get_attribute('href')==(g['trailers'][0].get('watchUrl') or g['trailers'][0]['sourceUrl']),(g['name'],'wrong video source')
   if g.get('requirements'):assert page.locator('.requirements').count()==1
   if g['trailers'][0].get('editionNote'):assert page.locator('.media-edition-note').inner_text()==g['trailers'][0]['editionNote']
   report['details'].append({'id':g['id'],'sources':hrefs,'videoSource':page.locator('.media-source-line a').get_attribute('href'),'player':'youtube' if page.locator('.youtube-consent').count() else 'native'})
   page.keyboard.press('Escape')
  check('Every RTS detail has complete distribution, media and game-mode information',len(report['details'])==130)
  report['images']=page.evaluate('''async rows=>{const out=[];let next=0;async function work(){while(next<rows.length){const g=rows[next++];out.push(await new Promise(resolve=>{const i=new Image(),timer=setTimeout(()=>resolve({id:g.id,url:g.image,ok:false,error:'timeout'}),18000);i.onload=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:i.naturalWidth>0,width:i.naturalWidth,height:i.naturalHeight})};i.onerror=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:false,error:'network/decode'})};i.src=g.image}))}}await Promise.all(Array.from({length:6},work));return out;}''',[{'id':g['id'],'image':g['image']} for g in rows])
  check('All 130 primary artworks decode from real remote bytes',all(x['ok'] for x in report['images']))
  for ident in ['steam:1486920','steam:9420']:
   page.evaluate('(id)=>openGame(id)',ident);page.wait_for_function("document.querySelector('#media-video')?.currentSrc.length>0",timeout=30000);page.evaluate("document.querySelector('#media-video').muted=true;document.querySelector('#media-video').play().catch(e=>window.rtsPlayError=String(e))");page.wait_for_function("document.querySelector('#media-video')?.currentTime>1",timeout=30000)
   result=page.locator('#media-video').evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,duration:v.duration,src:v.currentSrc})');result['id']=ident;report['playback'].append(result);check(ident+' actual trailer playback advances',result['time']>1 and result['width']>0);page.keyboard.press('Escape')
  page.evaluate("openGame('steam:2732960')");vid=page.locator('[data-youtube]').get_attribute('data-youtube');check('YouTube is opt-in',page.locator('.trailer-frame').count()==0);page.locator('[data-youtube]').click();check('Exact Zero Hour video reaches privacy-enhanced embed',page.locator('.trailer-frame').get_attribute('src').startswith('https://www.youtube-nocookie.com/embed/'+vid))
  page.locator('#game-notes').fill('RTS persistence verification');page.locator('#personal-rating').select_option('9');page.locator('.detail-save').click();page.reload(wait_until='domcontentloaded');check('RTS notes and ratings survive real reload',page.locator('#game-notes').input_value()=='RTS persistence verification' and page.locator('#personal-rating').input_value()=='9');check('RTS favorite persists','steam:2732960' in page.evaluate('GamesTest.personal.favorites'));page.screenshot(path=str(OUT/'rts-detail.png'));page.keyboard.press('Escape')
  page.locator('[data-hub="Real-time strategy"]').click();page.locator('[data-action=export]').click()
  with page.expect_download() as dl:page.locator('[data-export=json]').click()
  dest=OUT/'rts-export.json';dl.value.save_as(str(dest));export=json.loads(dest.read_text());check('Export contains all RTS records',len(export.get('items',[]) if isinstance(export,dict) else export)==130);page.keyboard.press('Escape')
  page.locator('[data-hub="Real-time strategy"]').click();page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(500);page.screenshot(path=str(OUT/'rts-desktop.png'))
  page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'rts-mobile.png'));check('RTS mobile layout does not overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  page.set_viewport_size({'width':1536,'height':1100});page.evaluate("openGame('external:beyond-all-reason')");page.screenshot(path=str(OUT/'rts-free-detail.png'));page.keyboard.press('Escape')
  portable=ctx.new_page();portable.on('pageerror',lambda e:report['errors'].append(str(e)));portable.goto((R/'release/Games - Explorer.html').as_uri()+'#hub=Real-time+strategy',wait_until='domcontentloaded');portable.wait_for_function('window.GamesTest');check('Portable HTML opens with the full RTS snapshot',len(portable.evaluate('GamesTest.filtered'))==130);portable.close()
  check('No uncaught JavaScript errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(OUT/'rts-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['details','images']},indent=2))
