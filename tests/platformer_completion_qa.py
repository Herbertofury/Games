"""Completion browser gate: actual direct playback, opt-in embeds, ten routes."""
from __future__ import annotations
import json,os,pathlib,shutil,socket,subprocess,sys,time,urllib.parse,urllib.request
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];Q=R/'qa';Q.mkdir(exist_ok=True);shots=Q/'platformer-completion-frames';shots.mkdir(exist_ok=True)
catalog=json.loads((R/'data/catalog.json').read_text());by={g['id']:g for g in catalog['items']};extra=json.loads((R/'data/platformers-media-reviewed.json').read_text())['overrides']
report={'sourceRevision':os.environ.get('GITHUB_SHA'),'datasetHash':catalog['build']['datasetHash'],'checks':[],'playback':[],'embeds':[],'errors':[]}
def check(name,passed):
 if not passed:raise AssertionError(name)
 report['checks'].append(name)
server=subprocess.Popen([sys.executable,'-m','http.server','8788','--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(50):
  with socket.socket() as s:
   if s.connect_ex(('127.0.0.1',8788))==0:break
  time.sleep(.1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox'])
  ctx=browser.new_context(viewport={'width':1536,'height':1100},reduced_motion='reduce');page=ctx.new_page();page.set_default_timeout(30000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
  page.goto('http://127.0.0.1:8788/#hub=Platformers',wait_until='domcontentloaded');page.wait_for_function('window.GamesTest && document.querySelector(".platformer-guide")')
  check('Platformer hub counter reports ten primary routes',page.locator('#stat-collections').inner_text()=='10')
  sidebar=page.locator('#collections [data-collection]').evaluate_all('(xs)=>xs.map(x=>({name:x.dataset.collection,count:Number(x.querySelector("b").textContent)}))')
  expected={}
  for g in by.values():
   if 'Platformers' in g.get('hubs',[]):expected[g['platformerCollection']]=expected.get(g['platformerCollection'],0)+1
  check('Every sidebar count matches its primary route',{s['name']:s['count'] for s in sidebar}==expected)
  check('Every game appears exactly once across the primary routes',sum(s['count'] for s in sidebar)==439)
  for ident,addition in extra.items():
   page.evaluate('(id)=>openGame(id)',ident);v=addition['trailers'][0]
   target=v.get('youtube') or v.get('mp4') or v.get('webm') or v.get('hls')
   index=next(i for i,t in enumerate(by[ident]['trailers']) if target in [t.get('youtube'),t.get('mp4'),t.get('webm'),t.get('hls')])
   page.evaluate('(i)=>{mediaMode="trailer";mediaIndex=i;renderMedia();}',index)
   check(ident+' source credit visible',v['credit'] in page.locator('.media-source-line').inner_text())
   if v.get('youtube'):
    api='https://www.youtube.com/oembed?'+urllib.parse.urlencode({'url':'https://www.youtube.com/watch?v='+v['youtube'],'format':'json'})
    with urllib.request.urlopen(api,timeout=25) as response:metadata=json.load(response)
    check(ident+' exact credited uploader',metadata['author_name'] in v['credit']);check(ident+' exact video title',metadata['title']==v['name'])
    check(ident+' YouTube remains opt-in',page.locator('.trailer-frame').count()==0)
    page.locator('[data-youtube]').click();check(ident+' exact privacy-enhanced embed',('/embed/'+v['youtube']) in page.locator('.trailer-frame').get_attribute('src'))
    report['embeds'].append({'id':ident,'youtube':v['youtube'],'title':metadata['title'],'author':metadata['author_name'],'official':v['official'],'evidence':'oEmbed title/uploader and exact opt-in player URL; not a claim of end-to-end YouTube playback'})
   else:
    page.wait_for_function('document.querySelector("#media-video")?.currentSrc.length>0',timeout=30000)
    page.locator('#media-video').evaluate('(v)=>{v.muted=true;v.play().catch(()=>{});}')
    page.wait_for_function('document.querySelector("#media-video")?.currentTime>1.2 && document.querySelector("#media-video").videoWidth>0',timeout=40000)
    info=page.locator('#media-video').evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,height:v.videoHeight,duration:v.duration,src:v.currentSrc})');info.update(id=ident,official=v['official'],credit=v['credit']);report['playback'].append(info)
    check(ident+' actual frames advance',info['time']>1.2 and info['width']>0)
    page.locator('#media-video').evaluate('(v)=>{if(Number.isFinite(v.duration))v.currentTime=Math.min(15,v.duration*.6);}')
    page.wait_for_timeout(900);page.locator('.media-stage').screenshot(path=str(shots/(ident.replace(':','-')+'.png')))
   page.evaluate('closeModal()')
  check('All twenty resolved records tested',len(report['playback'])+len(report['embeds'])==20)
  for hub in catalog['build']['hubCounts']:
   page.locator('button[data-hub="'+hub+'"]').click();check(hub+' full membership survives',len(page.evaluate('GamesTest.filtered'))==catalog['build']['hubCounts'][hub])
  page.locator('button[data-hub="Platformers"]').click();check('Returning from another hub restores ten primary routes',page.locator('#stat-collections').inner_text()=='10')
  page.wait_for_timeout(3500);page.evaluate('scrollTo(0,0)');page.screenshot(path=str(Q/'platformers-complete-desktop.png'))
  page.set_viewport_size({'width':390,'height':844});page.evaluate('scrollTo(0,0)');check('Completed mobile hub has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(Q/'platformers-complete-mobile.png'))
  check('No uncaught JavaScript errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(Q/'platformers-completion-qa.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
