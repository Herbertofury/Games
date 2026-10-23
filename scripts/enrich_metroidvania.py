#!/usr/bin/env python3
"""Source-grounded Metroidvania expansion. Missing evidence is retained for review."""
import argparse,concurrent.futures,datetime as dt,hashlib,html,json,pathlib,re,threading,time,urllib.parse
from bs4 import BeautifulSoup
import collect_metroidvania as core,refresh,collect_external_media as media,discover_storefronts as net
from source_links import normalized_links
ROOT=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat();HUB='Metroidvanias'
def load(name,default):
 p=ROOT/'data'/name;return json.loads(p.read_text()) if p.exists() else default

def save(name,data):
 p=ROOT/'data'/name;tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)

def source(url,provider,kind='project',note=None):return {'url':url,'provider':provider,'kind':kind,'verified':True,'lastChecked':NOW,**({'editionNote':note} if note else {})}
def provider(u):
 h=urllib.parse.urlsplit(u).hostname or ''
 if h.endswith('nintendo.com'):return 'Nintendo'
 if h.endswith('playstation.com'):return 'PlayStation'
 if h.endswith('konami.com'):return 'Konami'
 if h.endswith('xbox.com'):return 'Xbox'
 return net.provider(u) or 'Official site'

# A provider-wide pace prevents the initial burst from becoming repeated 429s.
_original_get=refresh.get;_pace_lock=threading.Lock();_next=0.0

def paced_get(url):
 global _next
 if urllib.parse.urlsplit(url).hostname=='store.steampowered.com':
  with _pace_lock:
   delay=max(0,_next-time.monotonic());_next=max(_next,time.monotonic())+0.55
  if delay:time.sleep(delay)
 return _original_get(url)
refresh.get=paced_get
_original_norm=core.norm
core.norm=lambda s:_original_norm((s or '').replace('\u2122','').replace('\u00ae','').replace('\u2120',''))


def steam_phase(config,force=False):
 candidates,dupes,excluded,external=core.seeds();old=load('metroidvania-steam.json',{}).get('items',[]);bykey={core.key(x['name']):x for x in candidates}
 for x in candidates:
  fix=config['corrections'].get(x['name'])
  if fix:x.update(fix)
 for title in config['additionalSteam']:
  if title in config['supplementExclusions']:excluded.append({'candidate':title,'state':'excluded','reason':'Explicit genre/identity review; not promoted merely to increase the count.'});continue
  if core.key(title) not in bykey:
   x={'name':title,'collection':'Indie deep cuts & unusual mechanics','fit':8,'scope':'Traditional Metroidvania','discoverySource':'Supplemental classics and creator research'};candidates.append(x);bykey[core.key(title)]=x
 index=load('metroidvania-discovery-index.json',{})
 for row in index.get('links',[]):
  if '/Game/' not in row.get('url',''):continue
  for image in row.get('images',[]):
   title=image.get('alt','')
   if title and core.key(title) not in bykey:
    x={'name':title,'collection':'Fresh discoveries & emerging worlds','fit':8,'scope':'Traditional Metroidvania','discoverySource':row['url']};candidates.append(x);bykey[core.key(title)]=x
 accepted=[]
 for x in candidates:
  if x['name'] in config['excludeCandidates']:excluded.append({'candidate':x['name'],'state':'excluded','reason':config['excludeCandidates'][x['name']]})
  else:accepted.append(x)
 # Reuse exact IDs already returned for pending searches, not another search for the same title.
 pending=load('metroidvania-steam.json',{}).get('unresolved',[])
 for x in accepted:
  if x.get('appid'):continue
  p=next((p for p in pending if core.key(p['candidate'])==core.key(x['name'])),None)
  found=next((m for m in (p or {}).get('matches',[]) if core.key(m['name'])==core.key(x['name'])),None)
  if found:x['appid']=found['appid']
 resolved=[];unresolved=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for g in pool.map(lambda x:core.resolve(x,old,force),accepted):
   (resolved if g.get('id') else unresolved).append(g);print('STEAM',g.get('verification'),g.get('name',g.get('candidate')),flush=True)
   # A checkpoint survives interruption without repeating successful provider calls.
   if (len(resolved)+len(unresolved))%40==0:
    prior={g['id']:g for g in old};prior.update({g['id']:g for g in resolved});save('metroidvania-steam-progress.json',{'generatedAt':NOW,'items':list(prior.values()),'unresolved':unresolved})
 unique={}
 for g in resolved:
  if g['id'] in unique:
   p=unique[g['id']];p['aliases']=list(dict.fromkeys(p.get('aliases',[])+[g['seedName']]));dupes.append({'candidate':g['seedName'],'id':g['id'],'canonicalCandidate':p['name']})
  else:unique[g['id']]=g
 d={'schemaVersion':1,'generatedAt':NOW,'inputCount':len(accepted),'items':sorted(unique.values(),key=lambda g:g['name'].casefold()),'unresolved':unresolved,'duplicates':dupes,'dispositions':excluded+external,'coverageNote':config['coverageNote']}
 save('metroidvania-steam.json',d);return d['items']


def page_media(url):
 raw,final,_=net.read(url);p=media.parse(raw,final);s=BeautifulSoup(raw,'html.parser')
 for node in list(s.select('#comments,.comments,.comment_list,.community_posts,.post_grid,.review_list,footer,nav')):node.decompose()
 main=s.select_one('.formatted_description') or s.select_one('article') or s
 clean=html.unescape(str(main).replace('\\/','/'))
 vids=list(dict.fromkeys(p['youtube']+re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})',clean)))
 if not p['image'] and not p['pictures']:
  for img in main.select('img[src],img[data-src]'):
   u=urllib.parse.urljoin(final,img.get('data-src') or img.get('src',''))
   if net.safe(u) and not any(t in u.lower() for t in ['logo','icon','avatar','rating','badge','button','pixel.gif','spacer']):p['pictures'].append(u)
 p.update(youtube=vids,sourceUrl=final,pageHash=hashlib.sha256(raw.encode()).hexdigest(),description=main.get_text(' ',strip=True)[:10000],outbound=[])
 for a in main.select('a[href]'):
  u=urllib.parse.urljoin(final,a['href']);h=urllib.parse.urlsplit(u).hostname or ''
  if net.safe(u) and any(h==d or h.endswith('.'+d) for d in ['store.steampowered.com','itch.io','gog.com','store.epicgames.com','patreon.com','nintendo.com','playstation.com','xbox.com','gamejolt.com','newgrounds.com']):p['outbound'].append({'url':u,'label':a.get_text(' ',strip=True)})
 return p


def external_phase(seed,old):
 ident='external:'+seed['slug'];prior=old.get(ident)
 if prior and prior.get('image') and prior.get('trailers'):return prior
 url=seed['url'];g={'id':ident,'name':seed['name'],'seedName':seed['name'],'collection':'Console origins & genre landmarks' if seed.get('platforms') else 'Freeware & creator-hosted worlds','collections':[],'hubs':[HUB],'fit':seed['fit'],'summary':seed['why'],'curatorWhy':seed['why'],'genreScope':seed['scope'],'requirements':seed.get('requirements','See the exact creator release for supported systems.'),'provider':provider(url),'primaryUrl':url,'status':seed.get('status','Released'),'kind':'Console game' if seed.get('platforms') else 'Browser / desktop game','free':seed['free'],'comingSoon':False,'genres':['Adventure'],'tags':[HUB,seed['scope']],'platforms':seed.get('platforms',[]),'developers':[],'features':[],'rating':None,'reviewCount':0,'releaseDate':None,'releaseLabel':str(seed.get('releaseYear') or 'See creator release'),'releaseYear':seed.get('releaseYear'),'originalReleaseYear':seed.get('originalReleaseYear'),'aliases':seed.get('aliases',[]),'storefronts':[],'sources':[],'screenshots':[],'trailers':[],'warnings':[],'mediaEvidence':[]}
 g['collections']=[g['collection']];errors=[]
 for page in [url]+seed.get('extraUrls',[]):
  try:
   p=page_media(page);u=p['sourceUrl'];label=provider(u)
   if page==url or not g.get('verification'):g.update(verification='verified',verifiedAt=NOW)
   if p.get('image') and not g.get('image'):g['image']=p['image']
   if not g.get('image') and p['pictures']:g['image']=p['pictures'][0]
   g['screenshots'] += [{'src':x,'thumbnail':x,'sourceUrl':u,'credit':'Creator / '+label,'alt':g['name']+' official image','verified':True} for x in p['pictures'] if x!=g.get('image')]
   for v in p['youtube']:g['trailers'].append({'youtube':v,'name':'Creator-published video','sourceUrl':u,'watchUrl':'https://www.youtube.com/watch?v='+v,'poster':g.get('image')})
   if p.get('nativeRating'):g['externalRating']=p['nativeRating']
   g['sources'].append(source(u,label));g['storefronts'].append(source(u,label,'support' if label=='Patreon' else 'store' if label in ['Nintendo','PlayStation'] else 'demo' if g['status']=='Demo' else 'prototype' if g['status']=='Prototype' else 'project'))
   g['mediaEvidence'].append({k:v for k,v in p.items() if k not in ['pictures','image']})
  except Exception as e:errors.append({'url':page,'error':str(e)})
 if seed.get('youtube'):g['trailers'].insert(0,{'youtube':seed['youtube'],'name':'Official trailer','sourceUrl':seed.get('extraUrls',[url])[-1],'watchUrl':'https://www.youtube.com/watch?v='+seed['youtube'],'poster':g.get('image')})
 g['screenshots']=list({x['src']:x for x in g['screenshots']}.values());g['trailers']=list({x['youtube']:x for x in g['trailers']}.values());g.setdefault('verification','unresolved');g['mediaErrors']=errors;g['mediaCheckedAt']=NOW
 print('EXTERNAL',g['name'],bool(g.get('image')),len(g['trailers']),flush=True);return g


def store_phase(g,old,itch_ready):
 if old and old.get('storeCoverage',{}).get('checkedAt'):return g['id'],old
 links=[];pending=[];checks=[]
 methods=[('GOG',lambda:net.gog(g,'https://catalog.gog.com/v1/catalog?limit=48&productType=in:game,pack&query=')),('Official website',lambda:net.owned_site(g))]
 if itch_ready:methods.append(('itch.io',lambda:net.itch(g)))
 else:checks.append({'provider':'itch.io','state':'provider-unavailable','reason':'Search response did not expose game results; known creator pages are checked separately.'})
 for label,fn in methods:
  try:
   found,candidates,url=fn();links+=found;pending+=candidates;checks.append({'provider':label,'state':'matched' if found else 'no-confirmed-match','sourceUrl':url,'matches':len(found)})
  except Exception as e:checks.append({'provider':label,'state':'unresolved','error':str(e)})
 links=normalized_links(links)
 for l in links:
  if l['provider']=='itch.io':
   try:
    p=page_media(l['url']);text=p['description']
    if re.search(r'\b(?:free demo|demo version|play the demo|download.{0,20}demo|this demo)\b',text,re.I):l.update(kind='demo',editionNote='This creator page offers a demo; check its available files before buying.')
    l['descriptionEvidence']=text[:2500]
   except Exception as e:l['editionCheckError']=str(e)
 return g['id'],{'storefronts':links,'storeCoverage':{'checkedAt':NOW,'checks':checks,'candidates':pending,'scope':'Exact GOG and itch.io catalog matches plus title-matched publisher links. Unmatched stores remain unknown.'}}


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');ap.add_argument('--skip-steam',action='store_true');a=ap.parse_args();cfg=load('metroidvania-expansion.json',{})
 old={g['id']:g for g in load('metroidvania-external.json',{'items':[]})['items']}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:ext=list(pool.map(lambda s:external_phase(s,old),cfg['external']))
 save('metroidvania-external.json',{'schemaVersion':1,'generatedAt':NOW,'items':ext})
 steam=load('metroidvania-steam.json',{'items':[]})['items'] if a.skip_steam else steam_phase(cfg,a.force)
 target=load('metroidvania-storefronts.json',{'overrides':{}});overrides=target['overrides']
 try:
  raw,_,_=net.read('https://itch.io/search?q=Hollow%20Knight');itch_ready=bool(BeautifulSoup(raw,'html.parser').select('.game_cell'))
 except Exception:itch_ready=False
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for i,(ident,extra) in enumerate(pool.map(lambda g:store_phase(g,overrides.get(g['id']),itch_ready),steam)):
   overrides[ident]=extra
   if i%40==0:save('metroidvania-storefronts.json',{'generatedAt':NOW,'overrides':overrides})
 for name,url,kind in cfg.get('creatorLinks',[]):
  g=next((g for g in steam if core.key(g['name'])==core.key(name) or core.key(g.get('seedName',''))==core.key(name)),None)
  if not g:continue
  try:
   p=page_media(url);overrides.setdefault(g['id'],{}).setdefault('storefronts',[]).append(source(p['sourceUrl'],'itch.io',kind,'Creator edition; demos and prototypes are distinct from the full Steam game.'));overrides[g['id']]['creatorEvidence']={k:v for k,v in p.items() if k not in ['pictures']}
  except Exception as e:overrides.setdefault(g['id'],{})['creatorCheckError']=str(e)
 save('metroidvania-storefronts.json',{'generatedAt':NOW,'overrides':overrides})
 report={'generatedAt':NOW,'steam':len(steam),'external':len(ext),'sourceLinks':sum(len(x.get('storefronts',[])) for x in overrides.values()),'missingArtwork':[{'id':g['id'],'name':g['name'],'url':g.get('primaryUrl')} for g in steam+ext if not g.get('image')],'missingVideo':[{'id':g['id'],'name':g['name'],'url':g.get('primaryUrl')} for g in steam+ext if not g.get('trailers')],'unresolved':load('metroidvania-steam.json',{}).get('unresolved',[]),'itchSearchAvailable':itch_ready}
 save('metroidvania-enrichment-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
