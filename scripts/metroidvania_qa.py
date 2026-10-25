"""Real Chrome acceptance for the complete Metroidvania hub, not a sampled catalog."""
from image_decode_qa import decode_primary_images
import contextlib,json,os,pathlib,shutil,socket,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'qa';OUT.mkdir(exist_ok=True)
catalog=json.loads((R/'data/catalog.json').read_text());rows=[g for g in catalog['items'] if 'Metroidvanias' in g.get('hubs',[])];by={g['id']:g for g in rows};N=len(rows)
report={'sourceRevision':os.environ.get('GITHUB_SHA'),'datasetHash':catalog['build']['datasetHash'],'records':N,'checks':[],'details':[],'images':[],'playback':[],'errors':[]}
def check(name,condition):
 if not condition:raise AssertionError(name)
 report['checks'].append(name)
port=8787;server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(40):
  with contextlib.closing(socket.socket()) as sock:
   if sock.connect_ex(('127.0.0.1',port))==0:break
  time.sleep(.1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1536,'height':1100},accept_downloads=True,reduced_motion='reduce');page=ctx.new_page();page.set_default_timeout(15000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
  url=f'http://127.0.0.1:{port}/';page.goto(url,wait_until='domcontentloaded');page.wait_for_function('window.GamesTest')
  for hub,n in list(json.loads((R/'data/metroidvania-protected.json').read_text())['hubCounts'].items())+[('Metroidvanias',N)]:
   page.locator('[data-hub="'+hub+'"]').click();check(hub+' complete visible count',page.locator('.game-card').count()==n)
  check('The sidebar contains only this genres curated shelves',page.locator('#collections [data-collection]').count()==len({g.get('metroidvaniaCollection',g['collection']) for g in rows}))
  page.locator('[data-action=filters]').click();page.locator('#f-scope').select_option('Traditional Metroidvania');chosen=page.evaluate('GamesTest.filtered');check('Traditional style uses the active genre classification',bool(chosen) and all(by[i]['metroidvaniaInfo']['structure']=='Traditional Metroidvania' for i in chosen));page.locator('[data-action=filters]').click();page.locator('[data-hub="Metroidvanias"]').click()
  check('Distinct exploration theme',page.locator('body').get_attribute('data-hub')=='metroidvanias');check('Enormous collection, not a short sample',N>=300)
  for preset in ['torment','mv-dark','mv-puzzle','mv-3d','mv-free','mv-hidden','mv-watchlist','new','demos']:
   page.locator('[data-preset="'+preset+'"]').click();ids=page.evaluate('GamesTest.filtered');check(preset+' shelf is functional',bool(ids))
   if preset=='torment':check('Core shelf excludes adjacent formats',all('MV core' in by[i]['tags'] and not by[i].get('comingSoon') for i in ids))
   if preset=='mv-watchlist':check('Future full games stay separate',all(by[i].get('comingSoon') for i in ids))
   if preset=='mv-free':check('Free shelf does not pretend paid purchases are freeware',all(by[i].get('free') for i in ids))
   if preset=='new':check('Recent shelf uses verified release dates',all('Recent Metroidvania release' in by[i]['tags'] and not by[i].get('comingSoon') for i in ids))
   if preset=='demos':check('Demos reference actual demo editions',all(by[i].get('demoAppids') or by[i]['status']=='Demo' or any(l['kind']=='demo' for l in by[i]['storefronts']) for i in ids))
  page.locator('[data-hub="Metroidvanias"]').click();page.locator('#search').fill('"Aria of Sorrow"');check('Collection contents searchable by original game title',bool(page.evaluate('GamesTest.filtered')));page.locator('#search').fill('')
  page.locator('[data-action=filters]').click();page.locator('#f-provider').select_option('GOG');ids=page.evaluate('GamesTest.filtered');check('Provider filter matches exact source buttons',bool(ids) and all(any(x['provider']=='GOG' for x in by[i]['storefronts']) for i in ids));page.locator('[data-action=filters]').click();page.locator('[data-hub="Metroidvanias"]').click()
  page.locator('[data-view=table]').click();check('Sortable table contains every record',page.locator('tbody tr').count()==N);page.locator('[data-view=gallery]').click();check('Gallery contains every record',len(page.evaluate('GamesTest.filtered'))==N);page.locator('[data-view=grid]').click()
  report['renderMs']=page.evaluate('()=>{const a=[];for(let i=0;i<5;i++){const t=performance.now();render();a.push(performance.now()-t)}return a}');check('Measured render never culls results',page.locator('.game-card').count()==N)
  for i,g in enumerate(rows):
   page.evaluate('(id)=>openGame(id)',g['id']);page.locator('.mv-brief').wait_for();links=page.locator('.storefronts a').evaluate_all('(xs)=>xs.map(x=>x.href)')
   # URL() adds the canonical root slash and encodes paths. Compare complete
   # destinations, including query and fragment, not raw spelling differences.
   expected=page.evaluate('(urls)=>urls.map(u=>new URL(u).href)',[x['url'] for x in g['storefronts']]);assert set(links)==set(expected),(g['name'],'source mismatch',links,expected)
   assert page.locator('#media-video,.youtube-consent').count()==1,(g['name'],'missing embedded player');source=page.locator('.media-source-line a').get_attribute('href');expected_source=page.evaluate('(u)=>new URL(u).href',g['trailers'][0].get('watchUrl') or g['trailers'][0]['sourceUrl']);assert source==expected_source,(g['name'],'wrong source',source,expected_source)
   if g.get('requirements'):assert page.locator('.requirements').count()==1
   report['details'].append({'id':g['id'],'sources':links,'videoSource':source,'brief':True});page.evaluate('closeModal()')
   if i%50==0:print('DETAILS',i+1,'/',N,flush=True)
  check('Every Metroidvania detail and source panel verified',len(report['details'])==N)
  report['images']=decode_primary_images(page, [{'id':g['id'],'image':g['image']} for g in rows], timeout_ms=25000)
  check('All primary artworks decode from actual provider bytes',all(x['ok'] for x in report['images']))
  for name in ['Hollow Knight','Moadra','Nine Sols']:
   game=next(g for g in rows if g['name']==name);page.evaluate('(id)=>openGame(id)',game['id']);page.wait_for_function("document.querySelector('#media-video')?.currentSrc.length>0",timeout=35000);page.evaluate("document.querySelector('#media-video').muted=true;document.querySelector('#media-video').play().catch(e=>window.mvPlayError=String(e))");page.wait_for_function("document.querySelector('#media-video')?.currentTime>1",timeout=35000)
   p=page.locator('#media-video').evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,src:v.currentSrc})');p['name']=name;report['playback'].append(p);check(name+' actual video has decoded advancing frames',p['time']>1 and p['width']>0);page.evaluate('closeModal()')
  creator=next(g for g in rows if g['id']=='external:mini-falafel-adventure');page.evaluate('(id)=>openGame(id)',creator['id']);vid=page.locator('[data-youtube]').get_attribute('data-youtube');check('Creator embeds are opt-in',page.locator('.trailer-frame').count()==0);page.locator('[data-youtube]').click();check('Exact creator video reaches privacy-enhanced player',page.locator('.trailer-frame').get_attribute('src').startswith('https://www.youtube-nocookie.com/embed/'+vid));page.evaluate('closeModal()')
  ident=next(g['id'] for g in rows if g['name']=='Hollow Knight');page.evaluate('(id)=>openGame(id)',ident);page.locator('#game-notes').fill('Metroidvania persistence check');page.locator('#personal-rating').select_option('10');page.locator('.detail-save').click();page.reload(wait_until='domcontentloaded');check('Notes and personal ratings persist after a real reload',page.locator('#game-notes').input_value()=='Metroidvania persistence check' and page.locator('#personal-rating').input_value()=='10');check('Saved game survives reload',ident in page.evaluate('GamesTest.personal.favorites'));page.screenshot(path=str(OUT/'metroidvania-detail.png'));page.evaluate('closeModal()')
  page.locator('[data-hub="Metroidvanias"]').click();page.locator('[data-action=export]').click()
  with page.expect_download() as dl:page.locator('[data-export=json]').click()
  dest=OUT/'metroidvania-export.json';dl.value.save_as(str(dest));data=json.loads(dest.read_text());check('Export retains the complete filtered set',len(data.get('items',[]) if isinstance(data,dict) else data)==N);page.keyboard.press('Escape')
  page.locator('[data-hub="Metroidvanias"]').click();page.evaluate('scrollTo(0,0)');page.wait_for_timeout(800);page.screenshot(path=str(OUT/'metroidvania-desktop.png'));page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'metroidvania-mobile.png'));check('Mobile layout stays inside viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.set_viewport_size({'width':1536,'height':1100});page.evaluate('(id)=>openGame(id)',creator['id']);page.screenshot(path=str(OUT/'metroidvania-creator.png'));page.evaluate('closeModal()')
  portable=ctx.new_page();portable.on('pageerror',lambda e:report['errors'].append(str(e)));portable.goto((R/'release/Games - Explorer.html').as_uri()+'#hub=Metroidvanias',wait_until='domcontentloaded');portable.wait_for_function('window.GamesTest');check('Exact portable artifact opens the entire hub',len(portable.evaluate('GamesTest.filtered'))==N);portable.close();check('No uncaught JavaScript errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(OUT/'metroidvania-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['details','images']},indent=2))

