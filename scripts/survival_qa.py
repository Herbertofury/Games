"""Production browser acceptance for both complete survival collections."""
import contextlib,json,os,pathlib,shutil,socket,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'qa';OUT.mkdir(exist_ok=True);HUBS=('Survival','Minecraft-like worlds')
catalog=json.loads((R/'data/catalog.json').read_text());rows=[g for g in catalog['items'] if any(h in g['hubs'] for h in HUBS)];by={g['id']:g for g in rows};protected=json.loads((R/'data/survival-protected.json').read_text())
report={'sourceRevision':os.environ.get('GITHUB_SHA'),'datasetHash':catalog['build']['datasetHash'],'uniqueStudyRecords':len(rows),'hubCounts':{h:sum(h in g['hubs'] for g in rows) for h in HUBS},'checks':[],'details':[],'images':[],'playback':[],'renderMs':{},'errors':[]}
def check(name,condition):
 if not condition:raise AssertionError(name)
 report['checks'].append(name)
server=subprocess.Popen([sys.executable,'-m','http.server','8787','--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(40):
  with contextlib.closing(socket.socket()) as sock:
   if sock.connect_ex(('127.0.0.1',8787))==0:break
  time.sleep(.1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1536,'height':1100},accept_downloads=True,reduced_motion='reduce');page=ctx.new_page();page.set_default_timeout(15000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
  page.goto('http://127.0.0.1:8787/',wait_until='domcontentloaded');page.wait_for_function('window.GamesTest')
  for h,n in protected['hubCounts'].items():
   page.locator('[data-hub="'+h+'"]').click();check('Preserved hub: '+h,page.locator('.game-card').count()==n)
  for hub in HUBS:
   subset={g['id']:g for g in rows if hub in g['hubs']};n=len(subset);page.locator('[data-hub="'+hub+'"]').click();check(hub+' renders every record',page.locator('.game-card').count()==n);check(hub+' distinct theme',page.locator('body').get_attribute('data-hub')==('survival' if hub=='Survival' else 'voxel'));check(hub+' primary collections match the data',page.locator('#collections [data-collection]').count()==len({g['survivalCollection'] for g in subset.values()}))
   for route in ['core','playable','coop','solo','new','gems','free','outside','demos','upcoming']+(['2d','blocks','mods'] if hub==HUBS[1] else []):
    page.locator('[data-survival-route="'+route+'"]').click();ids=page.evaluate('GamesTest.filtered');check(hub+' route: '+route,bool(ids) and all(i in subset for i in ids))
    if route in ['core','playable','coop','solo','new','gems','free','2d','blocks','mods']:check(hub+' '+route+' excludes unreleased full games',all(not by[i].get('comingSoon') for i in ids))
    if route=='upcoming':check(hub+' future shelf is not released',all(by[i].get('comingSoon') for i in ids))
    if route=='free':check(hub+' free filter respects actual price model',all(by[i]['free'] for i in ids))
    if route=='demos':check(hub+' demos are real editions',all(by[i].get('demoAppids') or by[i]['status']=='Demo' or any(s['kind']=='demo' for s in by[i]['storefronts']) for i in ids))
    if route=='2d':check('Terraria appears in its dedicated 2D route','steam:105600' in ids)
   page.locator('[data-hub="'+hub+'"]').click();page.locator('[data-action=filters]').click();page.locator('#f-provider').select_option('GOG');ids=page.evaluate('GamesTest.filtered');check(hub+' provider facet matches source buttons',bool(ids) and all(any(s['provider']=='GOG' for s in by[i]['storefronts']) for i in ids));page.locator('[data-action=filters]').click();page.locator('[data-hub="'+hub+'"]').click()
   for sort in ['recommended','rating','reviews','newest','oldest','name','price','personal','host']:
    page.locator('#sort').select_option(sort);check(hub+' sort preserves the complete matching set: '+sort,len(page.evaluate('GamesTest.filtered'))==n)
   page.locator('#sort').select_option('recommended');page.locator('[data-view=table]').click();check(hub+' complete table',page.locator('tbody tr').count()==n);page.locator('[data-view=gallery]').click();check(hub+' complete gallery',page.locator('.game-card').count()==n);page.locator('[data-view=grid]').click()
   report['renderMs'][hub]=page.evaluate('()=>{const a=[];for(let i=0;i<5;i++){const t=performance.now();render();a.push(performance.now()-t)}return a}');check(hub+' measured full render, no culling',page.locator('.game-card').count()==n)
   page.locator('[data-action=export]').click()
   with page.expect_download() as dl:page.locator('[data-export=json]').click()
   dest=OUT/('survival-export.json' if hub==HUBS[0] else 'minecraft-like-export.json');dl.value.save_as(str(dest));d=json.loads(dest.read_text());check(hub+' export has every filtered record',len(d.get('items',[]) if isinstance(d,dict) else d)==n);page.keyboard.press('Escape')
   page.locator('[data-hub="'+hub+'"]').click();page.evaluate('scrollTo(0,0)');page.wait_for_timeout(600);prefix='survival' if hub==HUBS[0] else 'minecraft-like';page.screenshot(path=str(OUT/(prefix+'-desktop.png')));page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/(prefix+'-mobile.png')));check(hub+' mobile fits the viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.set_viewport_size({'width':1536,'height':1100})
  page.locator('[data-hub="Minecraft-like worlds"]').click();page.locator('#search').fill('"Vintage Story"');check('Exact creator-title search',page.evaluate('GamesTest.filtered')==['external:vintage-story']);page.locator('#search').fill('');page.locator('#search').fill('"Minecraft Java"');check('Edition aliases are searchable','external:minecraft' in page.evaluate('GamesTest.filtered'));page.locator('#search').fill('')
  for i,g in enumerate(rows):
   page.evaluate('(id)=>openGame(id)',g['id']);page.locator('.survival-brief').wait_for();links=page.locator('.storefronts a').evaluate_all('(xs)=>xs.map(x=>x.href)');expected=page.evaluate('(us)=>us.map(u=>new URL(u).href)',[s['url'] for s in g['storefronts']]);assert set(links)==set(expected),(g['name'],'source destinations',links,expected)
   assert page.locator('#media-video,.youtube-consent').count()==1,(g['name'],'missing player');actual=page.locator('.media-source-line a').get_attribute('href');expected_video=page.evaluate('(u)=>new URL(u).href',g['trailers'][0].get('watchUrl') or g['trailers'][0]['sourceUrl']);assert actual==expected_video,(g['name'],'wrong video source')
   if g.get('requirements'):assert page.locator('.requirements').count()==1
   assert page.locator('.survival-facts>div').count()==6
   report['details'].append({'id':g['id'],'sources':links,'videoSource':actual,'fieldNotes':True});page.evaluate('closeModal()')
   if (i+1)%50==0:print('SURVIVAL PANELS',i+1,'/',len(rows),flush=True)
  check('Every survival and Minecraft-like detail/source panel checked',len(report['details'])==len(rows))
  report['images']=page.evaluate('''async rows=>{const out=[];let next=0;async function worker(){while(next<rows.length){const g=rows[next++];out.push(await new Promise(resolve=>{const im=new Image(),timer=setTimeout(()=>resolve({id:g.id,url:g.image,ok:false,error:'timeout'}),25000);im.onload=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:im.naturalWidth>0,width:im.naturalWidth,height:im.naturalHeight})};im.onerror=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:false,error:'network/decode'})};im.src=g.image}))}}await Promise.all(Array.from({length:5},worker));return out;}''',[{'id':g['id'],'image':g['image']} for g in rows]);check('Every primary artwork decoded from actual remote bytes',all(x['ok'] for x in report['images']))
  for ident in ['steam:3041230','steam:1203620','steam:105600','steam:1621690']:
   page.evaluate('(id)=>openGame(id)',ident);page.wait_for_function("document.querySelector('#media-video')?.currentSrc.length>0",timeout=35000);page.evaluate("document.querySelector('#media-video').muted=true;document.querySelector('#media-video').play().catch(e=>window.survivalPlayError=String(e))");page.wait_for_function("document.querySelector('#media-video')?.currentTime>1",timeout=35000);p=page.locator('#media-video').evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,src:v.currentSrc})');p['id']=ident;report['playback'].append(p);check(by[ident]['name']+' decoded advancing video frames',p['time']>1 and p['width']>0);page.evaluate('closeModal()')
  for ident in ['external:minecraft','external:hytale','external:vintage-story','external:mine-blocks']:
   page.evaluate('(id)=>openGame(id)',ident);vid=page.locator('[data-youtube]').get_attribute('data-youtube');check(ident+' exact video selected',vid==by[ident]['trailers'][0]['youtube']);check(ident+' external player is opt-in',page.locator('.trailer-frame').count()==0);page.locator('[data-youtube]').click();check(ident+' privacy-enhanced embed',page.locator('.trailer-frame').get_attribute('src').startswith('https://www.youtube-nocookie.com/embed/'+vid));page.evaluate('closeModal()')
  ident='external:vintage-story';page.locator('[data-hub="Minecraft-like worlds"]').click();page.evaluate('(id)=>openGame(id)',ident);page.locator('#game-notes').fill('My persistent survival world');page.locator('#personal-rating').select_option('10');page.locator('.detail-save').click();page.reload(wait_until='domcontentloaded');check('Survival notes and personal rating persist after reload',page.locator('#game-notes').input_value()=='My persistent survival world' and page.locator('#personal-rating').input_value()=='10');check('Favorite survives real reload',ident in page.evaluate('GamesTest.personal.favorites'));check('Inactive itch purchase is labelled as archived','Archived listing' in page.locator('.storefronts').inner_text());page.screenshot(path=str(OUT/'minecraft-like-detail.png'));page.evaluate('closeModal()')
  page.locator('[data-hub="Survival"]').click();page.evaluate('(id)=>openGame(id)','steam:3041230');page.screenshot(path=str(OUT/'survival-detail.png'));page.evaluate('closeModal()')
  for hub in HUBS:
   portable=ctx.new_page();portable.on('pageerror',lambda e:report['errors'].append(str(e)));portable.goto((R/'release/Games - Explorer.html').as_uri()+'#hub='+urllib_quote(hub) if False else (R/'release/Games - Explorer.html').as_uri()+'#hub='+hub,wait_until='domcontentloaded');portable.wait_for_function('window.GamesTest');check(hub+' exact portable artifact opens complete hub',len(portable.evaluate('GamesTest.filtered'))==report['hubCounts'][hub]);portable.close()
  check('No uncaught JavaScript errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(OUT/'survival-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['details','images']},indent=2))
