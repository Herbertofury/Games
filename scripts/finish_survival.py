#!/usr/bin/env python3
"""Finish only the reviewed source slices. Research gaps never become invented media."""
import copy,datetime as dt,hashlib,json,pathlib,re,shutil,urllib.parse
from bs4 import BeautifulSoup
import collect_survival as core,collect_survival_sources as sources,discover_storefronts as net
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat();E=R/'qa/survival-source-review'
def load(n,d):return core.load(n,d)
def save(n,d):core.save(n,d)
def source(u,p=None,k='project',note=None,origin=None):return dict(url=u,provider=p or sources.label(u),kind=k,verified=True,lastChecked=NOW,sourceUrl=origin or u,**({'editionNote':note} if note else {}))
def key(s):return re.sub('[^a-z0-9]','',(s or '').lower())
def main():
 plan=load('survival-finish-plan.json',{});review=json.loads((E/'report.json').read_text());pages={p['id']:p for p in review['pages']};videos={p['id']:p for p in review['videos']};sd=load('survival-steam.json',{});ed=load('survival-external.json',{});store=load('survival-storefronts.json',{'overrides':{}});cur=load('survival-curation.json',{'overrides':{}})['overrides'];med=load('survival-media.json',{'overrides':{}})['overrides'];proof=load('survival-media-reviewed.json',{'videos':{},'images':{},'sources':{}})
 for p in review['pages']:
  proof['sources'][p['id']]={k:p.get(k) for k in ['sourceUrl','title','pageHash','error']}
 # Keep new exact discoveries in future-refresh inputs as well as this snapshot.
 additions=load('survival-additions.json',{'steam':[]});new_seeds=[{'name':'Haven & Hearth','appid':3051280,'hub':'Survival','collection':'Persistent servers & competitive survival','fit':8,'scope':'Hardcore online survival crafting','aliases':[]},{'name':'Wild West Legacy','appid':1329880,'hub':'Survival','collection':'Tribes, settlements & historical frontiers','fit':7,'scope':'Survival / settlement building','aliases':['Wild West Dynasty']},{'name':'Derelicts','appid':1572000,'hub':'Survival','collection':'Horror, strange worlds & expeditions','fit':9,'scope':'Survival crafting / horror','aliases':[]},{'name':'DUCKSIDE','appid':2682580,'hub':'Survival','collection':'Persistent servers & competitive survival','fit':8,'scope':'Online survival crafting','aliases':[]}]
 for seed in new_seeds:
  additions['steam']=[x for x in additions['steam'] if x.get('appid')!=seed['appid']]+[seed]
  g=next((x for x in review['steamAdditions']+sd['items'] if x.get('appid')==seed['appid'] and x.get('verification')=='verified'),None) or core.resolve(seed,{},False)
  assert g.get('id') and g.get('verification')=='verified',g
  sd['items']=[x for x in sd['items'] if x['id']!=g['id']]+[g]
 save('survival-additions.json',additions)
 cfg=load('survival-expansion.json',{});cfg['corrections']['Wild West Dynasty']['aliases']=['Wild West Legacy'];save('survival-expansion.json',cfg)
 for ident,reason in plan['exclude'].items():cur.setdefault(ident,{}).update(excludeFromPublication=True,publicationReason=reason)
 for ident,row in plan['corrections'].items():cur.setdefault(ident,{}).update(row)
 for ident,text in plan['why'].items():cur.setdefault(ident,{})['curatorWhy']=text
 # All previous primary IDs stay intact; these are two distinct creator-authored browser games.
 ext_cfg=load('survival-external-seeds.json',{});mine=pages['mine-blocks'];assert not mine.get('error')
 for n in [1,2]:
  ident='external:mine-blocks'+('-2' if n==2 else '');name='Mine Blocks'+(' 2' if n==2 else '');u='https://mineblocks.com/'+str(n)
  seed={'id':ident,'name':name,'hub':'Minecraft-like worlds','collection':'Free & tiny crafting worlds','scope':'2D sandbox survival crafting','url':u,'extraUrls':['https://mineblocks.com/'],'fit':8,'status':'Playable alpha' if n==2 else 'Released','free':True,'platforms':['Web browser'],'why':'A free creator-made 2D Minecraft-inspired browser game with mining, crafting and building. '+('This is the separate HTML5 alpha sequel, not the cancelled third project.' if n==2 else 'The original is now playable in HTML5; it is a fan game, not a Mojang product.'),'requirements':'Play in a modern browser from the original creator. Optional Patreon support is not a required game purchase.'}
  ext_cfg['items']=[x for x in ext_cfg['items'] if x['id']!=ident]+[seed]
  g={k:copy.deepcopy(v) for k,v in seed.items() if k not in ['url','hub','scope','why','extraUrls']};g.update(seedName=name,hubs=[seed['hub']],collections=[seed['collection']],genreScope=seed['scope'],summary=seed['why'],curatorWhy=seed['why'],provider='Official site',primaryUrl=u,kind='Browser game',comingSoon=False,rating=None,reviewCount=0,genres=['Survival','Sandbox'],tags=['Minecraft-like worlds','Terraria-like worlds'],features=[],developers=['Zanzlanz'],verification='verified',verifiedAt=NOW,releaseDate=None,releaseLabel='See creator update history',storefronts=[source(u,'Official site','browser',origin=mine['sourceUrl']),source(u+'/download','Official site','download',origin=mine['sourceUrl']),source('https://patreon.com/Zanzlanz','Patreon','support','Optional support for the creator, not a game license.',mine['sourceUrl'])],sources=[source(mine['sourceUrl'])],screenshots=[],trailers=[])
  pics=[l['url'] for l in mine['allLinks'] if '/screenshots/mb'+str(n)+'/' in l['url']];assert pics
  g['image']=pics[0];g['screenshots']=[dict(src=p,thumbnail=p,sourceUrl=mine['sourceUrl'],credit='Zanzlanz / official Mine Blocks gallery',alt=name+' screenshot',verified=True) for p in pics]
  ed['items']=[x for x in ed['items'] if x['id']!=ident]+[g]
 save('survival-external-seeds.json',ext_cfg)
 allgames={g['id']:g for g in sd['items']+ed['items']}
 # Verified official web retrieval is a separate route from the runner's blocked HTTP request.
 for ident in ['external:minecraft','external:lego-fortnite-odyssey']:
  g=allgames[ident];med.setdefault(ident,{}).update(verification='verified',verifiedAt=NOW)
  med[ident].setdefault('_replace',{})['storefronts']=[source(g['primaryUrl'],g['provider'],'store' if ident.endswith(':minecraft') else 'project','Exact official product page read via the web retrieval route; runner HTTP access was restricted.')]
  med[ident]['sources']=[source(g['primaryUrl'],g['provider'],'source',origin=g['primaryUrl'])]
 # Each video has an exact independently checked title and creator. Wrong IDs are not accepted.
 for ident,(vid,contains,author,official,name) in plan['videos'].items():
  m=videos.get(vid)
  if not m or m.get('error'):m=net.api('https://www.youtube.com/oembed?url='+urllib.parse.quote('https://www.youtube.com/watch?v='+vid,safe='')+'&format=json')
  assert key(contains) in key(m['title']) and m['author_name']==author,(ident,m)
  url='https://www.youtube.com/watch?v='+vid;g=allgames[ident];proof['videos'][vid]={**m,'watchUrl':url,'checkedAt':NOW,'gameId':ident}
  patch=med.setdefault(ident,{}).setdefault('_replace',{});patch['trailers']=[{'youtube':vid,'name':name,'official':official,'credit':author,'watchUrl':url,'sourceUrl':g['primaryUrl'],'poster':m.get('thumbnail_url')}]
  if ident in ['external:voxelibre','external:mineclonia','external:terasology','external:minicraft-plus','external:survivalcraft-2','external:hytale']:
   patch['image']=m['thumbnail_url'];proof['images'][ident]={'role':'Official trailer thumbnail' if official else 'Credited community gameplay thumbnail','sourceUrl':url,'credit':author}
 for ident,row in plan['images'].items():
  patch=med.setdefault(ident,{}).setdefault('_replace',{});patch['image']=row['image'];proof['images'][ident]=row
  if row.get('gallery'):patch['screenshots']=[{'src':u,'thumbnail':u,'sourceUrl':row['sourceUrl'],'credit':row['credit'],'alt':allgames[ident]['name']+' official screenshot','verified':True} for u in row['gallery']]
 # Keep genuine creator galleries, not repository badges, avatars, store logos or ads.
 for g in ed['items']:
  ident=g['id'];patch=med.setdefault(ident,{}).setdefault('_replace',{})
  if 'screenshots' in patch:continue
  pics=g.get('screenshots',[]);good=[]
  for x in pics:
   u=x['src'];low=u.lower()
   if any(s in low for s in ['github.com','githubusercontent.com','shields.io','logo','badge','avatar','license','humblestore','anegostudios','ilha.','vintagecc','flag','button','youtube','patreon']):continue
   if ident=='external:hytale' and 'cdn.hytale.com/' not in u:continue
   if ident=='external:vintage-story' and 'img.itch.zone/' not in u:continue
   if ident=='external:stranded-2' and '/screens/stranded2' not in u:continue
   if ident=='external:veloren' and 'gallery-' not in u:continue
   if ident=='external:path-of-titans' and 'web-cdn.pathoftitans.com/' not in u:continue
   good.append(x)
  patch['screenshots']=good
 # Required engines and project repositories must not be labelled as purchases.
 for g in ed['items']:
  ident=g['id'];patch=med.setdefault(ident,{}).setdefault('_replace',{});links=patch.get('storefronts',g.get('storefronts',[]));kept=[];citations=[]
  for l in links:
   l=copy.deepcopy(l);u=l['url']
   if 'luanti.org' in u:l['kind']='engine';citations.append(l);continue
   if l['provider']=='GitHub':l['kind']='project'
   kept.append(l)
  patch['storefronts']=kept
  med[ident].setdefault('sources',[]).extend(citations)
 # Verified active purchase/download routes replace broken auxiliary pages.
 med['external:vintage-story'].setdefault('storefronts',[]).extend([source('https://www.vintagestory.at/store/category/1-single-game-account/','Vintage Story','store',origin='https://www.vintagestory.at/'),source('https://www.humblebundle.com/store/vintage-story','Humble Store','store',origin='https://www.vintagestory.at/')])
 med['external:path-of-titans'].setdefault('storefronts',[]).append(source('https://alderongames.com/store/path-of-titans','Alderon Games','store',origin='https://pathoftitans.com/'))
 med['external:luun'].setdefault('storefronts',[]).append(source('https://countsie.itch.io/luun','itch.io','prototype','Paid unfinished build and free demo are separately offered on the creator page.','https://luungame.com/index.html'))
 med['external:luun']['_replace']['screenshots']=[{'src':u,'thumbnail':u,'sourceUrl':'https://countsie.itch.io/luun','credit':'countsie / original creator gameplay animation','alt':'LUUN gameplay','verified':True} for u in pages['luun-itch'].get('pictures',[]) if 'img.itch.zone/' in u]
 for ident,provider,u,kind,note in plan['verifiedWebLinks']:med.setdefault(ident,{}).setdefault('storefronts',[]).append(source(u,provider,kind,note))
 # Do not publish an apparently matching store owned by an unconfirmed uploader.
 quarantined=[]
 remove=['casey-lisa.itch.io/humanitz','Lucid-Blocks-Chinese-Localization','stardeus-mod-template']
 for ident,row in store['overrides'].items():
  kept=[]
  for l in row.get('storefronts',[]):
   if any(s in l['url'] for s in remove) or (ident=='steam:340050' and 'survivalist-invisible-strain' in l['url']):quarantined.append({'id':ident,'source':l,'state':'not-published','reason':'Uploader/edition mismatch or auxiliary repository, not a confirmed game distribution.'});continue
   if 'raft.itch.io/raft' in l['url']:l.update(kind='prototype',editionNote='Original free prototype, not the current commercial Steam game.')
   if 'mindleak.itch.io/survival-vacancy' in l['url']:l.update(kind='demo',editionNote='Creator explicitly describes an alpha demo, not the full Steam edition.')
   if l['provider']=='GitHub':l['kind']='project'
   kept.append(l)
  row['storefronts']=kept
 # Deeper edition checks for the remaining small itch storefront set, preserving earlier discovery.
 for ident,row in store['overrides'].items():
  for l in row.get('storefronts',[]):
   if l['provider']!='itch.io' or l.get('kind') in ['demo','prototype','archive']:continue
   try:
    raw,final,_=net.read(l['url']);s=BeautifulSoup(raw,'html.parser');area=s.select_one('.game_info_panel_widget');uploads=' '.join(x.get_text(' ',strip=True) for x in s.select('.upload_list_widget .upload'));text=(s.select_one('.formatted_description') or s).get_text(' ',strip=True)
    if re.search(r'\bdemo\b',uploads,re.I) and not any(re.search(r'\.(?:zip|exe|tar)',x.get_text(),re.I) and not re.search(r'demo',x.get_text(),re.I) for x in s.select('.upload_list_widget .upload')):l.update(kind='demo',editionNote='Available download files are explicitly demo editions.')
    if re.search(r'purchasing.{0,15}disabled|no longer available',text,re.I):l.update(kind='archive',editionNote='Creator archive; current purchase/download availability is restricted.')
    proof['sources'][l['url']]={'title':s.title.get_text(' ',strip=True) if s.title else '', 'uploads':uploads,'metadata':area.get_text(' ',strip=True) if area else ''}
   except Exception as e:proof['sources'][l['url']]={'error':str(e)}
 # Native community scores remain separate from Steam percentages.
 p=pages['luun-itch'];g=allgames['external:luun'];med['external:luun']['sources']=[source(p['sourceUrl'],'itch.io')]
 for ident in ['external:minecraft','external:vintage-story','external:hytale','external:lego-fortnite-odyssey']:
  patch=cur.setdefault(ident,{});patch['tags']=sorted(set(patch.get('tags',[])+['Co-op','Modding mentioned'] if ident!='external:lego-fortnite-odyssey' else patch.get('tags',[])+['Co-op']))
  patch['survivalInfoOverride']={'solo':'Solo play supported by the creator; exact offline/authentication rules vary by edition','coop':'Multiplayer/co-op described by the creator; do not infer cross-play between editions','terrain':'Block or construction systems are a central part of the game'}
  if ident=='external:minecraft':patch['survivalInfoOverride'].update(modding='Java mods and Bedrock add-ons are distinct ecosystems',hosting='Official Java and Bedrock server downloads and optional Realms; editions are separate')
 # Per-entry review caveats keep obscure small-sample releases from masquerading as proven classics.
 for g in sd['items']:
  patch=cur.setdefault(g['id'],{});r=g.get('rating');n=g.get('reviewCount',0)
  if not g.get('comingSoon') and n<100:patch['recommendationCaution']='Small review sample. An exploratory discovery, not a well-established quality consensus.'
  if r is not None and n>=100 and r<70:patch['recommendationCaution']='Mixed or weak aggregate reception. Included for breadth and specific mechanics, not among the safest purchases; inspect recent reviews before buying.'
  if r is not None and n>=100 and r<50:patch['fit']=min(g['fit'],6)
 for ident in ['steam:2330750']:
  cur.setdefault(ident,{})['requirements']='The Steam edition is a paid distribution of a free open-source project. Official free builds are a separate route; do not confuse this with the Bright Nights fork.'
 # Clean obsolete hub tags after editorial rerouting; the same source ID remains unchanged.
 for g in sd['items']:
  patch=cur.get(g['id'],{});hub=(patch.get('hubs') or g['hubs'])[0];g['tags']=[t for t in g['tags'] if t not in ['Survival','Minecraft-like worlds'] or t==hub]
 sd['generatedAt']=NOW;ed['generatedAt']=NOW
 save('survival-steam.json',sd);save('survival-external.json',ed);save('survival-curation.json',{'generatedAt':NOW,'overrides':cur});save('survival-media.json',{'generatedAt':NOW,'overrides':med});save('survival-storefronts.json',store);save('survival-media-reviewed.json',{'checkedAt':NOW,**proof,'quarantinedLinks':quarantined})
 ledger=load('survival-reconciliation.json',{});resolved={core.norm(g['name']) for g in sd['items']}|{core.norm(a) for g in sd['items'] for a in g.get('aliases',[])}
 ledger['unresolved']=[x for x in ledger.get('unresolved',[]) if core.norm(x.get('candidate','')) not in resolved];ledger.setdefault('dispositions',[]).extend({'id':ident,'state':'not-promoted','reason':reason} for ident,reason in plan['exclude'].items());save('survival-reconciliation.json',ledger)
 # Correct the only causal integration edge cases before checkpoint tests.
 p=R/'scripts/survival_model.py';s=p.read_text();needle="    from source_links import normalized_links\n";addition="    from source_links import normalized_links\n    # Reconstruct this overlay from canonical sources so exclusions cannot leave stale rows.\n    for ident,previous in list(games.items()):\n        if previous.get('hubs') and set(previous['hubs'])<=set(HUBS):del games[ident]\n        elif any(h in HUBS for h in previous.get('hubs',[])):previous['hubs']=[h for h in previous['hubs'] if h not in HUBS]\n"
 # The module uses one-space indentation, preserve that rather than introducing mixed blocks.
 needle=' from source_links import normalized_links\n';addition=' from source_links import normalized_links\n for ident,previous in list(games.items()):\n  if previous.get("hubs") and set(previous["hubs"])<=set(HUBS):del games[ident]\n  elif any(h in HUBS for h in previous.get("hubs",[])):previous["hubs"]=[h for h in previous["hubs"] if h not in HUBS]\n'
 if addition not in s:assert needle in s;s=s.replace(needle,addition,1);p.write_text(s)
 print(json.dumps({'steamRecords':len(sd['items']),'creatorRecords':len(ed['items']),'mediaOverrides':len(med),'quarantinedSourceLinks':len(quarantined),'notPromoted':plan['exclude'],'remainingCandidates':len(ledger['unresolved'])},indent=2))
if __name__=='__main__':main()
