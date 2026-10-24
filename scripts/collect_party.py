#!/usr/bin/env python3
"""Couch multiplayer discovery. Online capacity is never silently used as local capacity."""
import argparse,concurrent.futures,csv,datetime as dt,functools,hashlib,json,pathlib,re,threading,time,unicodedata,urllib.parse
from bs4 import BeautifulSoup
import refresh,discover_storefronts as net
from source_links import normalized_links
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat();HUB='Couch co-op & party'
ALIASES={'n':'nplusplus','nplusplus':'nplusplus','hell diversdiveharderedition':'helldiversdiveharderedition','gauntletslayeredition':'gauntletslayeredition'}
LOCK=threading.Lock();NEXT=0.;ORIGINAL_GET=refresh.get

def norm(s):
 s=unicodedata.normalize('NFKD',(s or '').replace('\u2122','').replace('\u00ae','')).encode('ascii','ignore').decode().lower().replace('&','and');s=re.sub('[^a-z0-9]','',s);return ALIASES.get(s,s)
def paced(url):
 global NEXT
 if urllib.parse.urlsplit(url).hostname=='store.steampowered.com':
  with LOCK:wait=max(0,NEXT-time.monotonic());NEXT=max(NEXT,time.monotonic())+.48
  if wait:time.sleep(wait)
 return ORIGINAL_GET(url)
refresh.get=paced;refresh.details=functools.lru_cache(maxsize=None)(refresh.details)
def load(name,default):
 p=R/'data'/name;return json.loads(p.read_text()) if p.exists() else default
def save(name,data):
 p=R/'data'/name;p.parent.mkdir(exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def normalized_text(s):
 for word,num in [('twenty','20'),('twelve','12'),('eleven','11'),('ten','10'),('nine','9'),('eight','8'),('seven','7'),('six','6'),('five','5'),('four','4'),('three','3'),('two','2')]:s=re.sub(r'\b'+word+r'\b',num,s,flags=re.I)
 return re.sub(r'\s+',' ',s).replace('\u2013','-').replace('\u2014','-')
def evidence(text):
 text=normalized_text(text);out=[]
 patterns=[r'(?:up to\s+)?(?:\d+\s*[-to]+\s*)?\d+\s*(?:-| )*(?:(?:local|couch|simultaneous|human|online)\s+)?players?',r'(?:local|couch|split.screen).{0,90}?\d+',r'(?:two|a|one) friend',r'phones?|smartphones?|tablets?|pass.and.play|hot.seat|controllers? required']
 for pattern in patterns:
  for m in re.finditer(pattern,text,re.I):
   snippet=text[max(0,m.start()-120):min(len(text),m.end()+150)]
   if snippet not in out:out.append(snippet)
 return out

def collect(seed,prior,all_existing,force):
 name=seed['name'];hint=int(seed['countHint'] or 0);old=next((g for g in prior if norm(g.get('seedName',g['name']))==norm(name)),None)
 if old and not force and old.get('verifiedAt') and (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(old['verifiedAt'])).total_seconds()<86400:return old
 if hint==0:return {'candidate':name,'state':'not-promoted','reason':seed.get('note') or 'Does not claim native local multiplayer in this discovery set.'}
 if seed['collection']=='Console party essentials' or name=='SuperTuxKart':return {'candidate':name,'state':'external-route','reason':seed.get('note'),'seed':seed}
 aid=int(seed['appid']) if seed.get('appid') else None;matches=[]
 try:
  aliases=load('party-corrections.json',{}).get('identities',{}).get(name,{})
  if aliases.get('appid'):aid=aliases['appid']
  allowed=[name]+aliases.get('aliases',[])
  if not aid:
   known=next((g for g in all_existing if any(norm(g['name'])==norm(a) for a in allowed) and g.get('appid')),None)
   if known:aid=known['appid']
   else:
    results=refresh.get('https://store.steampowered.com/api/storesearch/?'+urllib.parse.urlencode({'term':aliases.get('search',name),'l':'english','cc':'us'})).get('items',[]);matches=[{'appid':x['id'],'name':x['name']} for x in results]
    exact=next((x for x in results if any(norm(x['name'])==norm(a) for a in allowed)),None)
    if not exact:raise ValueError('No exact identity; reconciliation required')
    aid=exact['id']
  d=refresh.details(aid)
  if not d or d.get('type')!='game' or not any(norm(d['name'])==norm(a) for a in allowed):raise ValueError('Official app identity mismatch: '+str((d or {}).get('name')))
  paragraphs=BeautifulSoup(d.get('about_the_game',''),'html.parser').get_text(' ',strip=True);description=refresh.text(d.get('short_description',''));full=description+' '+paragraphs
  cats=[c['description'] for c in d.get('categories',[])];local=any('Shared/Split Screen' in c for c in cats) or bool(re.search(r'\b(?:local|couch).{0,30}(?:multiplayer|co.op|versus|players)|split.screen',full,re.I))
  if seed['participation'] in ['phones','asymmetric','hotseat']:local=local or bool(re.search(r'phones?|tablets?|hot.seat|pass.and.play|same room',full,re.I))
  if not local:return {'candidate':name,'state':'local-unresolved','appid':aid,'sourceUrl':f'https://store.steampowered.com/app/{aid}/','reason':'Official page does not establish native couch multiplayer; online/Remote Play tags alone are insufficient.','features':cats,'text':full,'seed':seed}
  g=refresh.resolve({'appid':aid,'name':d['name'],'collection':seed['collection'],'fit':seed['fit']},{},True)
  if g['verification']!='verified':raise ValueError(str(g.get('warnings')))
  u=g['steamUrl'];count_snippets=evidence(full);nt=normalized_text(full)
  specific=re.findall(r'(?:up to\s+)?(\d{1,2})\s*(?:-| )?(?:local players|player local|player couch)|(?:local|couch)(?: multiplayer| co.op| versus| play| co op)?\s*(?:for |with |supports? |: |up to |with up to )*(\d{1,2})\s*players?',nt,re.I)
  direct=[int(a or b) for a,b in specific if 2<=int(a or b)<=64]
  general=[]
  for m in re.finditer(r'(?:up to\s+)?(?:(\d{1,2})\s*[-to]+\s*)?(\d{1,2})\s*(?:-| )?(?:players?|people|friends)',nt,re.I):
   n=int(m[2]);context=nt[max(0,m.start()-100):m.end()+100].lower()
   if 2<=n<=64 and ('local' in context or 'couch' in context or not any('Online' in c for c in cats)):general.append(n)
  phonecounts=[int(x) for x in re.findall(r'\((?:\d+\s*[-to]+\s*)?(\d{1,2})\s*players?\)',nt,re.I)] if seed['participation']=='phones' else []
  observed=list(dict.fromkeys(direct+general+phonecounts));verified=(hint in direct) or (hint in general and len(set(general))==1) or bool(phonecounts and hint==max(phonecounts))
  # These cases require a reviewed mode-level cap, not automatic promotion from ambiguous prose.
  complex_case=any(w in seed.get('note','').lower() for w in ['different limits','caps differ','verify','differs','different caps','only','controller mode','per-game','rigid','not every','4 online','online but','4 local','story co-op','standard xinput'])
  if complex_case:verified=False
  if not direct and hint not in observed:verified=False
  mode=[]
  if 'Shared/Split Screen Co-op' in cats:mode.append('Co-op')
  if 'Shared/Split Screen PvP' in cats:mode.append('Versus')
  if not mode and seed['participation'] in ['phones','hotseat']:mode=['Versus']
  localinfo={'countHint':hint,'localMax':hint if verified else None,'playerCounts':list(range(2,hint+1)) if verified else [],'countVerified':verified,'countCandidates':observed,'modes':mode,'modeHint':seed['modeHint'],'participation':seed['participation'],'screen':'Split-screen' if re.search(r'split.screen',full,re.I) else 'Shared / split screen; see mode notes','platform':'PC edition','inputs':'See controller support and exact mode notes.','notes':seed.get('note',''),'sourceUrl':u,'checkedAt':NOW,'evidence':count_snippets,'localSupport':True,'onlineListed':any('Online' in c for c in cats),'remotePlayTogether':'Remote Play Together' in cats,'controllerSupport':d.get('controller_support','Not specified'),'requiresInternet':'Phone-controller games require host/device connectivity; verify exact game requirements.' if seed['participation']=='phones' else 'Not inferred from local support.'}
  g.update(hubs=[HUB],collections=[seed['collection']],partyCollection=seed['collection'],partyFit=int(seed['fit']),primaryUrl=u,provider='Steam',kind='Standalone game',partyInfo=localinfo,partyEvidence={'sourceUrl':u,'about':paragraphs,'description':description,'features':cats,'controllerSupport':d.get('controller_support')},knownFavorite=name in ['Disc Jam','Lethal League','Lethal League Blaze','Thunder Rally','Hyper Jam','Boomerang Fu'])
  g['demoAppids']=[x['appid'] for x in d.get('demos',[]) if x.get('appid')];g['storefronts']=[{'url':u,'provider':'Steam','kind':'wishlist' if g['comingSoon'] else 'store','verified':True,'lastChecked':NOW}]
  # Preserve store/full-release versus earlier playable history where supplied by Steam.
  try:
   raw,_,_=net.read(u+'?l=english');s=BeautifulSoup(raw,'html.parser');txt=s.get_text(' ',strip=True);m=re.search(r'Early Access Release Date:\s*([A-Za-z]+\s+\d{1,2},\s*\d{4})',txt)
   if m:g['earlyAccessReleaseDate']=refresh.date_iso(m[1])
   if 'no longer available on the Steam store' in txt or 'no longer available for purchase' in txt:g['storefronts'][0]['kind']='archive';g['warnings'].append('Steam listing is archived/delisted; use another verified official destination when available.')
  except Exception as error:g['storePageError']=str(error)
  return g
 except Exception as error:
  if old:old['lastRefreshError']=str(error);return old
  return {'candidate':name,'state':'unresolved-active','reason':str(error),'matches':matches,'seed':seed}

def alternatives(g,prev,itch):
 if prev and prev.get('storeCoverage',{}).get('checkedAt'):return g['id'],prev
 links=[];checks=[];candidates=[];methods=[('GOG',lambda:net.gog(g,'https://catalog.gog.com/v1/catalog?limit=48&productType=in:game,pack&query=')),('Official website',lambda:net.owned_site(g))]
 if itch:methods.append(('itch.io',lambda:net.itch(g)))
 for label,fn in methods:
  try:
   found,pending,url=fn();links+=found;candidates+=pending;checks.append({'provider':label,'sourceUrl':url,'state':'matched' if found else 'no-confirmed-match','matches':len(found)})
  except Exception as e:checks.append({'provider':label,'state':'unresolved-active','error':str(e)})
 for l in links:
  if 'demo' in l['url'].lower():l['kind']='demo'
 return g['id'],{'storefronts':normalized_links(links),'storeCoverage':{'checkedAt':NOW,'checks':checks,'candidates':candidates,'scope':'Exact official GOG/itch.io listings and title-bound official website links. A miss is not proof of absence; generic publisher homes and key-reseller search results are not store buttons.'}}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');ap.add_argument('--skip-stores',action='store_true');args=ap.parse_args()
 seeds=list(csv.DictReader((R/'data/party-seeds.tsv').read_text().splitlines(),delimiter='\t'));old=load('party-steam.json',{}).get('items',[]);existing=load('catalog.json',{}).get('items',[]);out=[];pending=[];duplicates=[];names=set();clean=[]
 for row in seeds:
  if norm(row['name']) in names:duplicates.append(row['name']);continue
  names.add(norm(row['name']));clean.append(row)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for g in pool.map(lambda s:collect(s,old,existing,args.force),clean):
   (out if g.get('id') else pending).append(g);print(g.get('name',g.get('candidate')),g.get('state',g.get('partyInfo',{}).get('countVerified')),flush=True)
   if (len(out)+len(pending))%40==0:save('party-progress.json',{'generatedAt':NOW,'items':out,'dispositions':pending})
 unique={}
 for g in out:
  if g['id'] in unique:duplicates.append({'id':g['id'],'name':g['name']})
  else:unique[g['id']]=g
 out=sorted(unique.values(),key=lambda g:g['name'].casefold());save('party-steam.json',{'schemaVersion':1,'generatedAt':NOW,'inputCount':len(seeds),'items':out,'dispositions':pending,'duplicates':duplicates})
 stores=load('party-storefronts.json',{'overrides':{}})
 if not args.skip_stores:
  try:body,_,_=net.read('https://itch.io/search?q=Boomerang%20Fu');itch=bool(BeautifulSoup(body,'html.parser').select('.game_cell'))
  except Exception:itch=False
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   for i,(ident,extra) in enumerate(pool.map(lambda g:alternatives(g,stores['overrides'].get(g['id']),itch),out)):
    stores['overrides'][ident]=extra
    if i%40==0:save('party-storefronts.json',stores)
  stores['generatedAt']=NOW;save('party-storefronts.json',stores)
 report={'generatedAt':NOW,'candidates':len(seeds),'acceptedSteamIdentities':len(out),'countsAutomaticallyMatched':sum(g['partyInfo']['countVerified'] for g in out),'countReview':[{'id':g['id'],'name':g['name'],**g['partyInfo']} for g in out if not g['partyInfo']['countVerified']],'missingMedia':[{'id':g['id'],'name':g['name']} for g in out if not g.get('image') or not g.get('trailers')],'dispositions':pending,'duplicates':duplicates};save('party-research-report.json',report);print(json.dumps({k:v for k,v in report.items() if k!='countReview'},indent=2))
if __name__=='__main__':main()
