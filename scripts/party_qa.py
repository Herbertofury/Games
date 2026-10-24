"""Exercise every party dossier and image, with an independent mode/capacity oracle."""
import contextlib,csv,json,os,pathlib,re,shutil,socket,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'qa';OUT.mkdir(exist_ok=True);HUB='Couch co-op & party'
catalog=json.loads((R/'data/catalog.json').read_text());rows=[g for g in catalog['items'] if HUB in g.get('hubs',[])];by={g['id']:g for g in rows};N=len(rows)
report={'sourceRevision':os.environ.get('GITHUB_SHA'),'datasetHash':catalog['build']['datasetHash'],'records':N,'checks':[],'details':[],'images':[],'playback':[],'errors':[]}
def check(name,condition):
 if not condition:raise AssertionError(name)
 report['checks'].append(name)
def expected(players='',mode='',setup='',edition='',base=False):
 ids=set()
 for g in rows:
  p=g['partyInfo'];ms=[m for m in p['modesDetail'] if (not mode or m['type']==mode) and (not base or not m.get('requiresDlc'))]
  if (mode or base) and not ms:continue
  if setup and p['participation']!=setup:continue
  pc=bool(re.search('PC|Windows|Linux|macOS',p['platform'],re.I))
  if edition and pc!=(edition=='pc'):continue
  ns={n for m in ms for n in m['counts']}
  if players=='unknown' and ns:continue
  if players=='5plus' and not any(n>=5 for n in ns):continue
  if players=='9plus' and not any(n>=9 for n in ns):continue
  if players.isdigit() and int(players) not in ns:continue
  ids.add(g['id'])
 return ids
server=subprocess.Popen([sys.executable,'-m','http.server','8787','--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(50):
  with contextlib.closing(socket.socket()) as sock:
   if sock.connect_ex(('127.0.0.1',8787))==0:break
  time.sleep(.1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1536,'height':1100},accept_downloads=True,reduced_motion='reduce');page=ctx.new_page();page.set_default_timeout(20000);page.on('pageerror',lambda e:report['errors'].append(str(e)))
  page.goto('http://127.0.0.1:8787/',wait_until='domcontentloaded');page.wait_for_function('window.PartyTest&&window.GamesTest')
  for hub,n in [('Roguelites',198),('Boomer shooters',150),('Real-time strategy',130),('Metroidvanias',430),('Platformers',439),('Survival',299),('Minecraft-like worlds',82)]:
   page.locator('[data-hub="'+hub+'"]').click();check('Prior complete hub: '+hub,page.locator('.game-card').count()==n)
  def reset():page.locator('[data-hub="'+HUB+'"]').click()
  def result():return set(page.evaluate('GamesTest.filtered'))
  reset();check('All party records rendered, no virtualization',page.locator('.game-card').count()==N);check('Distinct party theme',page.locator('body').get_attribute('data-hub')=='party');check('Party lobby installed exactly once',page.locator('.party-lobby').count()==1);check('Primary party shelves do not inherit another hub',page.locator('#collections [data-collection]').count()==len({g['partyCollection'] for g in rows}))
  for mode in ['', 'Co-op','Versus']:
   page.locator('#party-mode').select_option(mode)
   for count in ['','2','3','4','5','6','7','8','5plus','9plus','unknown']:
    page.locator('#party-players').select_option(count);check('Mode/headcount exact intersection: '+(mode or 'all')+' / '+(count or 'all'),result()==expected(count,mode))
  reset()
  for setup in ['simultaneous','phones','hotseat','asymmetric']:
   page.locator('#party-setup').select_option(setup);check('Participation: '+setup,result()==expected(setup=setup))
  reset()
  for edition in ['pc','console']:
   page.locator('#party-edition').select_option(edition);check('Exact edition: '+edition,result()==expected(edition=edition))
  reset();page.locator('#party-players').select_option('4');page.locator('#party-mode').select_option('Co-op');before=result();check('TowerFall expansion supports four-player co-op','steam:251470' in before);check('A larger versus cap does not imply four-player co-op','steam:4489580' not in before and 'steam:585710' not in before);page.locator('#party-base-only').check();check('DLC filter uses the selected mode',result()==expected('4','Co-op',base=True) and 'steam:251470' not in result() and 'steam:247080' not in result())
  reset();page.locator('#party-base-only').check();check('Base-only applies even without numerical/mode filter',result()==expected(base=True));reset()
  page.locator('#search').fill('players:4 mode:coop');check('Structured query uses the same mode/count intersection',result()==expected('4','Co-op'));page.locator('#search').fill('title:"Lethal League Blaze"');check('Exact favorite title search',result()=={'steam:553310'});page.locator('#search').fill('')
  for route in ['favorites','duo','four','crowd','new','hidden','phones','free','upcoming']:
   page.locator('[data-party-route="'+route+'"]').click();ids=result();check('Functional party route: '+route,bool(ids))
   if route not in ['upcoming']:check(route+' excludes unreleased full games',all(not by[i].get('comingSoon') for i in ids))
   if route=='duo':check('Two-person teamwork is native simultaneous co-op',ids<=expected('2','Co-op','simultaneous'))
   if route=='four':check('Four controllers exclude hotseat/phones',ids<=expected('4',setup='simultaneous'))
   if route=='crowd':check('Big-couch route uses actual simultaneous capacities',ids<=expected('5plus',setup='simultaneous'))
   if route=='upcoming':check('Upcoming is separate from playable recommendations',all(by[i].get('comingSoon') for i in ids))
   if route=='phones':check('Phone contestants are separated from controllers',all(by[i]['partyInfo']['participation']=='phones' for i in ids))
  reset();page.locator('#party-players').select_option('4');page.locator('#party-mode').select_option('Versus');page.locator('#party-setup').select_option('simultaneous');page.locator('#party-edition').select_option('pc');page.locator('#party-base-only').check();selected=result();check('Five combined filters match independent oracle',selected==expected('4','Versus','simultaneous','pc',True));page.reload(wait_until='domcontentloaded');check('Deep-link reload preserves all party filters',result()==selected and page.locator('#party-base-only').is_checked())
  page.get_by_role('button',name='Save current filters',exact=True).click();page.locator('#view-name').fill('Four-PC-versus no extra DLC');page.locator('[data-action="commit-view"]').click();reset();page.locator('[data-load-view]').last.click();check('Saved views preserve party modes and counts',result()==selected);page.locator('[data-party-clear="partyPlayers"]').click();check('Individual party chips clear exactly their facet',page.locator('#party-players').input_value()=='' and page.locator('#party-mode').input_value()=='Versus');page.locator('[data-party-reset]').click();check('Lobby reset restores all party records',len(result())==N)
  reset();page.locator('[data-action="filters"]').click();page.locator('#f-provider').select_option('GOG');ids=result();check('Provider filter agrees with exact source destinations',bool(ids) and all(any(s['provider']=='GOG' for s in by[i]['storefronts']) for i in ids));page.locator('[data-action="filters"]').click();reset()
  for sort in ['recommended','rating','reviews','newest','oldest','name','price','personal','host','players']:
   page.locator('#sort').select_option(sort);check('Sort retains every record: '+sort,len(result())==N)
  order=page.evaluate('GamesTest.filtered');check('Most-players sort keeps actual phone participants not spectators',(by[order[0]]['partyInfo']['localMax'] or 0)==max(g['partyInfo']['localMax'] or 0 for g in rows));page.locator('#sort').select_option('recommended')
  page.locator('[data-view=table]').click();check('Every record in mode-aware table',page.locator('tbody tr').count()==N);check('Table exposes local counts and edition',page.locator('thead').inner_text().find('Local people')>=0);page.locator('[data-view=gallery]').click();check('Every record in visual gallery',page.locator('.game-card').count()==N);page.locator('[data-view=grid]').click()
  report['renderMs']=page.evaluate('()=>{const a=[];for(let i=0;i<5;i++){const t=performance.now();render();a.push(performance.now()-t)}return a}');check('Measured full render does not cull records',page.locator('.game-card').count()==N)
  for kind in ['csv','json']:
   page.locator('[data-action="export"]').click()
   with page.expect_download() as dl:page.locator('[data-export="'+kind+'"]').click()
   dest=OUT/('party-export.'+kind);dl.value.save_as(str(dest));page.keyboard.press('Escape')
   if kind=='json':exported=json.loads(dest.read_text())['items'];check('JSON retains every mode and source',len(exported)==N and all(g.get('partyInfo') for g in exported))
   else:
    with dest.open(encoding='utf-8-sig',newline='') as f:data=list(csv.DictReader(f))
    check('CSV includes every game with counts, modes and inputs',len(data)==N and all(k in data[0] for k in ['Local player counts','Local co-op counts','Local versus counts','Mode-specific limits and conditions','Inputs / hardware']))
  reset()
  for ident in ['steam:4489580','steam:251470']:
   page.locator('[data-compare="'+ident+'"]').first.check()
  page.locator('[data-action="compare"]').first.click();check('Comparison includes local edition and mode-specific capacities',page.locator('.party-compare').count()==2 and 'extra DLC' in page.locator('.compare-grid').inner_text());page.keyboard.press('Escape');page.locator('[data-action="clear-compare"]').click()
  for i,g in enumerate(rows):
   page.evaluate('(id)=>openGame(id)',g['id']);page.locator('.party-brief').wait_for();actual=page.locator('.storefronts a').evaluate_all('(xs)=>xs.map(x=>x.href)');wanted=page.evaluate('(us)=>us.map(u=>new URL(u).href)',[s['url'] for s in g['storefronts']]);assert set(actual)==set(wanted),(g['name'],'store destinations')
   assert page.locator('.party-mode-list article').count()==len(g['partyInfo']['modesDetail']),(g['name'],'mode row missing')
   mode_links=page.locator('.party-mode-list a').evaluate_all('(xs)=>xs.map(x=>x.href)');expected_links=page.evaluate('(us)=>us.map(u=>new URL(u).href)',[m['sourceUrl'] for m in g['partyInfo']['modesDetail']]);assert mode_links==expected_links,(g['name'],'count sources')
   assert page.locator('#media-video,.youtube-consent').count()==1,(g['name'],'missing supported player')
   actual_video=page.locator('.media-source-line a').get_attribute('href');expected_video=page.evaluate('(u)=>new URL(u).href',g['trailers'][0].get('watchUrl') or g['trailers'][0]['sourceUrl']);assert actual_video==expected_video,(g['name'],'wrong video identity')
   for mode,article in zip(g['partyInfo']['modesDetail'],page.locator('.party-mode-list article').all()):
    if not mode['counts']:assert 'Count needs confirmation' in article.inner_text(),(g['name'],'unknown count hidden')
    if mode.get('requiresDlc'):assert 'DLC' in article.inner_text() or 'Dark World' in article.inner_text(),(g['name'],'DLC condition hidden')
   report['details'].append({'id':g['id'],'sources':actual,'modeSources':mode_links,'videoSource':actual_video});page.evaluate('closeModal()')
   if (i+1)%50==0:print('PARTY PANELS',i+1,'/',N,flush=True)
  check('Every party dossier and source button set checked',len(report['details'])==N)
  report['images']=page.evaluate('''async rows=>{const out=[];let next=0;async function worker(){while(next<rows.length){const g=rows[next++];out.push(await new Promise(resolve=>{const im=new Image(),timer=setTimeout(()=>resolve({id:g.id,url:g.image,ok:false,error:'timeout'}),25000);im.onload=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:im.naturalWidth>0,width:im.naturalWidth,height:im.naturalHeight})};im.onerror=()=>{clearTimeout(timer);resolve({id:g.id,url:g.image,ok:false,error:'network/decode'})};im.src=g.image}))}}await Promise.all(Array.from({length:5},worker));return out;}''',[{'id':g['id'],'image':g['image']} for g in rows]);check('Every primary image decodes from actual provider bytes',all(x['ok'] for x in report['images']))
  for ident in ['steam:965680','steam:556050','steam:2001120','steam:4489580','external:puff-puff-push']:
   page.evaluate('(id)=>openGame(id)',ident);page.wait_for_function("document.querySelector('#media-video')?.currentSrc.length>0",timeout=35000);page.evaluate("document.querySelector('#media-video').muted=true;document.querySelector('#media-video').play().catch(e=>window.partyPlayError=String(e))");page.wait_for_function("document.querySelector('#media-video')?.currentTime>0.5",timeout=35000);v=page.locator('#media-video').evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,height:v.videoHeight,src:v.currentSrc,duration:v.duration})');report['playback'].append(dict(id=ident,**v));check(by[ident]['name']+' has actual advancing decoded video',v['width']>0 and v['time']>.5);page.evaluate('closeModal()')
  creator=next(g for g in rows if g['id'].startswith('external:') and g['trailers'][0].get('youtube'))
  page.evaluate('(id)=>openGame(id)',creator['id']);vid=page.locator('[data-youtube]').get_attribute('data-youtube');check('External video consent selects exact reviewed identity',vid==creator['trailers'][0]['youtube'] and page.locator('.trailer-frame').count()==0);page.locator('[data-youtube]').click();check('Consent opens privacy-enhanced embedded player',page.locator('.trailer-frame').get_attribute('src').startswith('https://www.youtube-nocookie.com/embed/'+vid));page.evaluate('closeModal()')
  page.evaluate('(id)=>openGame(id)','steam:251470');page.screenshot(path=str(OUT/'party-mode-detail.png'));page.evaluate('closeModal()');page.evaluate('(id)=>openGame(id)','steam:4489580');page.locator('#game-notes').fill('Two for the campaign; more friends for versus.');page.locator('#personal-rating').select_option('9');page.locator('.detail-save').click();page.locator('#detail-status').select_option('Backlog');page.reload(wait_until='domcontentloaded');check('Notes, rating, favorite and backlog persist',page.locator('#game-notes').input_value()=='Two for the campaign; more friends for versus.' and page.locator('#personal-rating').input_value()=='9' and 'steam:4489580' in page.evaluate('GamesTest.personal.favorites') and page.locator('#detail-status').input_value()=='Backlog');page.screenshot(path=str(OUT/'party-detail.png'));page.evaluate('closeModal()')
  reset();page.evaluate('scrollTo(0,0)');page.wait_for_timeout(700);page.screenshot(path=str(OUT/'party-desktop.png'));page.locator('#library').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'party-cards.png'));page.evaluate('scrollTo(0,0)');page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'party-mobile.png'));check('Mobile lobby stays within viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.evaluate('(id)=>openGame(id)','steam:251470');check('Mobile dossier stays within viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(OUT/'party-mobile-detail.png'));page.evaluate('closeModal()');page.set_viewport_size({'width':1536,'height':1100});page.locator('[data-action="theme"]').first.click();check('Light theme works',page.locator('body').get_attribute('class').find('light')>=0);page.locator('[data-action="theme"]').first.click()
  portable=ctx.new_page();portable.on('pageerror',lambda e:report['errors'].append(str(e)));portable.goto((R/'release/Games - Explorer.html').as_uri()+'#hub=Couch%20co-op%20%26%20party&partyPlayers=4&partyMode=Versus',wait_until='domcontentloaded');portable.wait_for_function('window.PartyTest');check('Exact portable artifact opens headcount-filtered party hub',set(portable.evaluate('GamesTest.filtered'))==expected('4','Versus'));portable.close();check('No uncaught JavaScript errors',not report['errors']);browser.close()
 report['passed']=True
finally:
 server.terminate();server.wait(timeout=5);(OUT/'party-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['details','images']},indent=2))
