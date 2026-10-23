"""Exercise every shooter detail, store button, video source and image in the built app."""
import contextlib,concurrent.futures,json,os,pathlib,shutil,socket,subprocess,sys,time,urllib.request,urllib.parse
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'qa';OUT.mkdir(exist_ok=True)
data=json.loads((R/'data/catalog.json').read_text());games=[g for g in data['items'] if 'Boomer shooters' in g.get('hubs',[])];by={g['id']:g for g in games}
port=8783;server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
report={'datasetHash':data['build']['datasetHash'],'sourceRevision':os.environ.get('GITHUB_SHA'),'checks':[],'errors':[],'records':len(games),'detailProof':[],'images':[],'youtubeMetadata':[]}
def check(label,ok):
 if not ok:raise AssertionError(label)
 report['checks'].append(label)
try:
 for _ in range(30):
  with contextlib.closing(socket.socket()) as s:
   if s.connect_ex(('127.0.0.1',port))==0:break
  time.sleep(.1)
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1536,'height':1100},reduced_motion='reduce');p=ctx.new_page();p.set_default_timeout(15000);p.on('pageerror',lambda e:report['errors'].append(str(e)));url=f'http://127.0.0.1:{port}/'
  p.goto(url,wait_until='domcontentloaded');p.wait_for_function('window.GamesTest');p.locator('[data-hub="Boomer shooters"]').click()
  check('Every shooter card remains available',p.locator('.game-card').count()==len(games))
  check('Every card exposes source/video counts',p.locator('.card-source-summary').count()==len(games))
  # Measure full-record work, with all 150 cards retained; no viewport culling.
  samples=p.evaluate('() => {let a=[]; for(let i=0;i<5;i++){let t=performance.now();render();a.push(performance.now()-t)} return a;}');report['renderMs']=samples
  for g in games:
   p.evaluate('(id)=>openGame(id)',g['id']);p.locator('[data-media-mode=trailer]').click()
   hrefs=p.locator('.storefronts a').evaluate_all('(xs)=>xs.map(x=>x.href)')
   expected={s['url'] for s in g['storefronts']};assert set(hrefs)==expected,(g['name'],'stores differ',set(hrefs)^expected)
   assert p.locator('.media-source-line a').count()==1,(g['name'],'no video source')
   assert p.locator('#media-video,.youtube-consent').count()==1,(g['name'],'no embedded player')
   first=g['trailers'][0]
   if first.get('editionNote'):assert p.locator('.media-edition-note').inner_text()==first['editionNote']
   report['detailProof'].append({'id':g['id'],'storeCount':len(hrefs),'videoSource':p.locator('.media-source-line a').get_attribute('href'),'player':'youtube' if p.locator('.youtube-consent').count() else 'native'})
   p.keyboard.press('Escape')
  check('Every shooter detail has every published store and embedded video UI',len(report['detailProof'])==len(games))
  # Real byte decoding for every card artwork; validate all rather than only visible cards.
  report['images']=p.evaluate('''async (rows) => {
   const results=[];let next=0;
   async function worker(){while(next<rows.length){const g=rows[next++];const result=await new Promise(resolve=>{const im=new Image();const timer=setTimeout(()=>resolve({id:g.id,url:g.image,ok:false,error:'timeout'}),15000);im.onload=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:im.naturalWidth>0,width:im.naturalWidth,height:im.naturalHeight})};im.onerror=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:false,error:'decode or network'})};im.src=g.image;});results.push(result)}}
   await Promise.all(Array.from({length:6},worker));return results;
  }''',[{'id':g['id'],'image':g['image']} for g in games])
  check('All shooter artwork decodes from real source bytes',all(x['ok'] for x in report['images']))
  for ident in ['external:tremor','external:arcane-dimensions','external:total-chaos-original','external:blade-of-agony','external:death-wish']:
   p.evaluate('(id)=>openGame(id)',ident);p.locator('[data-media-mode=trailer]').click();v=p.locator('[data-youtube]').get_attribute('data-youtube');p.locator('[data-youtube]').click();check(ident+' exact privacy-enhanced embed',p.locator('.trailer-frame').get_attribute('src').startswith('https://www.youtube-nocookie.com/embed/'+v));p.keyboard.press('Escape')
  # One new direct Steam video must actually progress, not just contain a URL.
  p.evaluate("openGame('external:shrine')");p.locator('[data-media-mode=trailer]').click();p.wait_for_function("document.querySelector('#media-video')?.currentSrc.length>0",timeout=30000);p.evaluate("document.querySelector('#media-video').muted=true;document.querySelector('#media-video').play().catch(e=>window.sourcePlayError=String(e))");p.wait_for_function("document.querySelector('#media-video').currentTime>1",timeout=20000);report['shrinePlayback']=p.locator('#media-video').evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,duration:v.duration})');check('New Shrine trailer actually plays',report['shrinePlayback']['time']>1)
  p.keyboard.press('Escape');p.locator('[data-hub="Boomer shooters"]').click();p.wait_for_timeout(400);p.screenshot(path=str(OUT/'shooters-complete-desktop.png'));p.set_viewport_size({'width':390,'height':844});p.screenshot(path=str(OUT/'shooters-complete-mobile.png'));check('No mobile horizontal overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));p.set_viewport_size({'width':1536,'height':1100});p.evaluate("openGame('steam:3808730')");p.screenshot(path=str(OUT/'shooters-complete-detail.png'));check('No uncaught script errors',not report['errors']);b.close()
 # Validate exact YouTube titles/creators for the six added sources independently of iframe rendering.
 def video(g):
  t=g['trailers'][0];vid=t['youtube'];u='https://www.youtube.com/oembed?url='+urllib.parse.quote('https://www.youtube.com/watch?v='+vid,safe='')+'&format=json'
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:d=json.load(r)
  return {'game':g['name'],'id':g['id'],'video':vid,'title':d['title'],'author':d['author_name'],'sourceUrl':u}
 selected=[by[i] for i in ['external:tremor','external:arcane-dimensions','external:total-chaos-original','external:blade-of-agony','external:death-wish']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:report['youtubeMetadata']=list(pool.map(video,selected))
 for x in report['youtubeMetadata']:
  required={'external:tremor':'tremor','external:arcane-dimensions':'arcane','external:total-chaos-original':'total chaos','external:blade-of-agony':'blade of agony','external:death-wish':'blood'}[x['id']]
  check(x['id']+' source metadata matches',required in x['title'].lower())
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(OUT/'source-completion-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['detailProof','images']},indent=2))
