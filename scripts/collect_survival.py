#!/usr/bin/env python3
"""Incremental survival research. Exact identities, no guessed release dates or ratings."""
import argparse,concurrent.futures,copy,datetime as dt,functools,hashlib,json,pathlib,re,threading,time,unicodedata,urllib.parse
from bs4 import BeautifulSoup
import refresh,discover_storefronts as net
ROOT=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
EXTERNAL={'Minecraft','Hytale','Vintage Story','Veloren','Terasology','VoxeLibre','Mineclonia','Luanti','Survivalcraft 2','Mythruna','Minicraft+','Minicraft','Minetest Game','ClassiCube','Mine Blocks','Orion Sandbox Enhanced','Paper Minecraft','WILDRAFT','Vintage Story Classic','Path of Titans','Haven & Hearth'}
EXCLUDE={'Shipwrecked 64':'Narrative/ARG horror, not the requested survival-crafting loop.','The Beast Inside':'Narrative horror, not open-world survival crafting.','Dead District: Survival':'Low-confidence discovery retained in the source ledger, not a quality recommendation.','Crash Dive':'Submarine combat, not survival crafting.','Rising Front':'Battle simulator, not the requested survival crafting.','Cast n Chill':'Relaxed fishing, not survival crafting.','Terra Nil':'Ecological puzzle strategy, not Minecraft-like survival.','Hytale: Adventure':'An unfinished mode/feature of Hytale, not a separate released game.','Necesse 2':'Unconfirmed sequel identity, not promoted.','Muck 2':'Unconfirmed sequel identity, not promoted.','Subsistence: River Basin':'Unconfirmed separate game identity; not duplicated from Subsistence.','The Planet Crafter: Eden Crafters':'Two distinct projects accidentally combined; both actual games have their own entries.','Planet Crafter: Toxicity':'Expansion/discovery label, not assumed to be a standalone game.','Survival Fountain':'Ambiguous duplicate-like discovery, not promoted.','Survival: The Last Hope':'Unconfirmed ambiguous discovery name, not promoted.','Dead Rising 3 Apocalypse Edition':'Action zombie sandbox without the requested survival-crafting emphasis.','Deadzone: Rogue':'Roguelite shooter, not a survival-crafting world.','Thea: The Awakening':'Turn-based strategy survival neighbor; omitted to keep the added categories focused.','Thea 2: The Shattering':'Turn-based strategy survival neighbor; omitted from this collection.','Dead Age 2':'Turn-based RPG, not the requested survival crafting.','Dead State: Reanimated':'Turn-based survival RPG, not the requested open-world crafting focus.','Blockland':'Creative construction sandbox without survival; not promoted into the survival shelf.','Rokh':'Historical experimental release with weak reception; kept as a research disposition rather than a current recommendation.'}
ORIGINAL={'Valheim':2021,'Palworld':2024,'Conan Exiles':2018,'Windrose':2026,'ARK: Survival Ascended':2023,'ARK: Survival Evolved':2017,'Enshrouded':2024,'Project Zomboid':2013,'7 Days to Die':2013,'Terraria':2011,'Starbound':2016,'Core Keeper':2022,'Necesse':2019,'Rising World':2014,'Creativerse':2014}
def norm(s):
 s=unicodedata.normalize('NFKD',(s or '').replace('\u2122','').replace('\u00ae','')).encode('ascii','ignore').decode().lower().replace('&','and');return re.sub('[^a-z0-9]','',s)
def load(name,default):
 p=ROOT/'data'/name;return json.loads(p.read_text()) if p.exists() else default
def save(name,data):
 p=ROOT/'data'/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def seeds():
 out={};ledger=[];hub=group=scope='';fit=8
 for line in (ROOT/'data/survival-seeds.txt').read_text().splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  if line.startswith('['):hub,group,fit,scope=line[1:-1].split('|');fit=int(fit);continue
  x=line.split('|');name=x[0]
  if name in EXCLUDE:ledger.append({'candidate':name,'state':'excluded','reason':EXCLUDE[name]});continue
  if name in EXTERNAL:ledger.append({'candidate':name,'state':'external-route','reason':'Use exact creator distribution; no unrelated Steam substitute.'});continue
  k=norm(name)
  if k in out:ledger.append({'candidate':name,'state':'duplicate','canonical':out[k]['name']});continue
  out[k]={'name':name,'hub':hub,'collection':group,'fit':int(x[1]) if len(x)>1 else fit,'scope':scope,'appid':int(x[2]) if len(x)>2 and x[2] else None,'aliases':x[3].split(';') if len(x)>3 else []}
 for x in load('survival-additions.json',{'steam':[]}).get('steam',[]):out[norm(x['name'])]=x
 return list(out.values()),ledger
_original_get=refresh.get;pace=threading.Lock();next_at=0.0
def paced(url):
 global next_at
 if urllib.parse.urlsplit(url).hostname=='store.steampowered.com':
  with pace:wait=max(0,next_at-time.monotonic());next_at=max(next_at,time.monotonic())+.58
  if wait:time.sleep(wait)
 return _original_get(url)
refresh.get=paced;refresh.details=functools.lru_cache(maxsize=None)(refresh.details)
def resolve(seed,prior,force=False):
 old=prior.get(seed.get('appid')) or next((x for x in prior.values() if norm(x.get('seedName',x['name'])) in [norm(seed['name'])]+[norm(a) for a in seed.get('aliases',[])]),None)
 if old and not force and old.get('survivalSourceVersion')==1 and old.get('verifiedAt'):
  if (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(old['verifiedAt'])).total_seconds()<86400:return old
 candidates=[]
 try:
  aid=seed.get('appid');names={norm(n) for n in [seed['name']]+seed.get('aliases',[])}
  if not aid:
   u='https://store.steampowered.com/api/storesearch/?'+urllib.parse.urlencode({'term':seed['name'],'l':'english','cc':'us'});candidates=refresh.get(u).get('items',[]);found=next((x for x in candidates if norm(x['name']) in names),None)
   if not found:raise ValueError('Exact title requires reconciliation')
   aid=found['id']
  d=refresh.details(aid)
  if not d or d.get('type')!='game':raise ValueError('Official store did not confirm a standalone game')
  if norm(d['name']) not in names:raise ValueError('Explicit ID/name mismatch: '+d['name'])
  g=refresh.resolve({'appid':aid,'name':d['name'],'fit':seed['fit'],'collection':seed['collection']},{},True)
  if g.get('verification')!='verified':raise ValueError(str(g.get('warnings')))
  u=g['steamUrl'];about=refresh.text(d.get('about_the_game',''));tags=[seed['collection'],seed['scope'],seed['hub']]
  for pattern,label in [(r'\bfarm|agricultur','Farming'),(r'\bfish','Fishing'),(r'tam(?:e|ing)|breed(?:ing)?','Creature taming'),(r'procedural','Procedural worlds'),(r'terraform|deformable|destructible terrain|voxel','Terrain / voxel systems'),(r'dedicated server','Dedicated server mentioned'),(r'\bmodding|\bmods\b|workshop','Modding mentioned'),(r'\bPvE\b','PvE mentioned'),(r'\bPvP\b','PvP mentioned')]:
   if re.search(pattern,about,re.I):tags.append(label)
  if any('co-op' in x.lower() for x in g['features']):tags.append('Co-op')
  if 'Single-player' in g['features']:tags.append('Single-player listed')
  g.update(seedName=seed['name'],hubs=[seed['hub']],collections=[seed['collection']],primaryUrl=u,provider='Steam',kind='Standalone game',genreScope=seed['scope'],aliases=seed.get('aliases',[]),tags=sorted(set(tags+g['genres'])),survivalSourceVersion=1)
  g['storefronts']=[{'provider':'Steam','url':u,'kind':'wishlist' if g['comingSoon'] else 'store','verified':True,'lastChecked':NOW}]
  g['demoAppids']=[x['appid'] for x in d.get('demos',[]) if x.get('appid')]
  g['survivalEvidence']={'sourceUrl':u,'descriptionExcerpt':about[:1400],'singlePlayerListed':'Single-player' in g['features'],'coopListed':any('co-op' in x.lower() for x in g['features']),'dedicatedServerMentioned':'Dedicated server mentioned' in tags,'moddingMentioned':'Modding mentioned' in tags,'terrainMentioned':'Terrain / voxel systems' in tags,'basis':'Store descriptions and feature flags. A mention is not proof of cross-play, offline access, or every server option.'}
  if seed['name'] in ORIGINAL:g['originalReleaseYear']=ORIGINAL[seed['name']]
  if d.get('drm_notice'):g['requirements']=refresh.text(d['drm_notice'])
  if g['comingSoon']:g['recommendationCaution']='Watchlist only. Any offered demo is a separate development build, not the released full game.'
  if 'adjacent' in seed['scope'].lower():g['recommendationCaution']='Explicitly labelled crafting, management or automation neighbor; not a conventional character-survival game.'
  return g
 except Exception as e:
  if old and old.get('survivalSourceVersion')==1:return dict(old,lastRefreshError=str(e))
  return {'candidate':seed['name'],'seed':seed,'error':str(e),'matches':[{'appid':x['id'],'name':x['name']} for x in candidates],'state':'unresolved-active'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');a=ap.parse_args();candidate,ledger=seeds();old=load('survival-steam.json',{'items':[]});progress=load('survival-progress.json',{'items':[]});prior={g['appid']:g for g in old['items']+progress['items'] if g.get('appid')};out=[];pending=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for i,g in enumerate(pool.map(lambda x:resolve(x,prior,a.force),candidate)):
   (out if g.get('id') else pending).append(g);print(g.get('verification',g.get('state')),g.get('name',g.get('candidate')),flush=True)
   if (i+1)%25==0:save('survival-progress.json',{'generatedAt':NOW,'items':out,'unresolved':pending})
 unique={}
 for g in out:
  if g['id'] in unique:ledger.append({'candidate':g['seedName'],'state':'duplicate','canonical':unique[g['id']]['name']})
  else:unique[g['id']]=g
 out=sorted(unique.values(),key=lambda g:g['name'].casefold());data={'schemaVersion':1,'generatedAt':NOW,'inputCount':len(candidate),'items':out,'unresolved':pending,'dispositions':ledger};save('survival-steam.json',data)
 report={'inputs':len(candidate),'publishedCandidates':len(out),'hubCounts':{h:sum(h in g['hubs'] for g in out) for h in ['Survival','Minecraft-like worlds']},'missingVideo':[{'id':g['id'],'name':g['name']} for g in out if not g.get('trailers')],'unresolved':pending,'dispositions':ledger};save('survival-discovery-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
