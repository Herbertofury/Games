#!/usr/bin/env python3
"""Creator pages, alternative storefronts and bounded discovery; facts remain source-specific."""
import argparse,concurrent.futures,datetime as dt,hashlib,html,json,pathlib,re,urllib.parse
from bs4 import BeautifulSoup
import discover_storefronts as net,collect_external_media as media
from source_links import normalized_links
ROOT=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
net.PROVIDERS.update({'store.onstove.com':'STOVE','minecraft.net':'Minecraft','hytale.com':'Hytale','vintagestory.at':'Vintage Story','github.com':'GitHub','fortnite.com':'Epic Games'})
def load(n,d):
 p=ROOT/'data'/n;return json.loads(p.read_text()) if p.exists() else d
def save(n,d):
 p=ROOT/'data'/n;t=p.with_suffix('.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def label(u):return net.provider(u) or 'Official site'
def source(u,kind='project',**kw):return dict(provider=label(u),url=u,kind=kind,verified=True,lastChecked=NOW,**kw)
def page(u):
 raw,final,typ=net.read(u)
 if re.search(r'<title>\s*(?:Making sure|Just a moment)',raw,re.I):raise ValueError('Provider challenge; use an alternate authoritative source, no bypass')
 p=media.parse(raw,final);s=BeautifulSoup(raw,'html.parser')
 for n in list(s.select('#comments,.comments,.comment_list,.community_posts,.review_list,.post_grid,footer,nav')):n.decompose()
 main=s.select_one('.formatted_description') or s.select_one('main') or s.select_one('article') or s
 body=html.unescape(str(main).replace('\\/','/'));p.update(sourceUrl=final,title=s.title.get_text(' ',strip=True) if s.title else '',pageHash=hashlib.sha256(raw.encode()).hexdigest(),outbound=[],files=[],description=main.get_text(' ',strip=True)[:3500])
 p['youtube']=list(dict.fromkeys(p.get('youtube',[])+re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})',body)))
 for node in main.select('video,video source'):
  value=node.get('src') or node.get('data-src')
  if value:
   url=urllib.parse.urljoin(final,value)
   if net.safe(url) and re.search(r'\.(mp4|webm|m3u8)(?:\?|$)',url):p['files'].append(url)
 for n in main.select('img[src],img[data-src]'):
  value=n.get('data-src') or n.get('src');pic=urllib.parse.urljoin(final,value)
  if net.safe(pic) and not any(x in pic.lower() for x in ['logo','avatar','icon','badge','flag','payment','gravatar','pixel.gif','spacer']):
   if pic not in p['pictures']:p['pictures'].append(pic)
 for a in main.select('a[href]'):
  value=urllib.parse.urljoin(final,a['href']);provider=net.provider(value)
  if provider and net.safe(value):p['outbound'].append({'provider':provider,'url':value,'label':a.get_text(' ',strip=True)})
 return p

def yt_search(query):
 url='https://www.youtube.com/results?search_query='+urllib.parse.quote(query);raw,_,_=net.read(url);m=re.search(r'(?:var\s+)?ytInitialData\s*=\s*',raw)
 if not m:return {'query':query,'url':url,'error':'No public result data; no bypass attempted'}
 data=json.JSONDecoder().raw_decode(raw[m.end():])[0];rows=[]
 def text(v):return v.get('simpleText') or ''.join(r.get('text','') for r in v.get('runs',[]))
 def walk(x):
  if isinstance(x,dict):
   if 'videoRenderer' in x:
    v=x['videoRenderer'];rows.append({'youtube':v.get('videoId'),'title':text(v.get('title',{})),'author':text(v.get('ownerText',{})),'length':text(v.get('lengthText',{}))})
   else:
    for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(data);return {'query':query,'url':url,'results':rows}

def creator(seed,old):
 if old and old.get('mediaCheckedAt') and (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(old['mediaCheckedAt'])).total_seconds()<86400:return old
 g={'id':seed['id'],'name':seed['name'],'seedName':seed['name'],'aliases':seed.get('aliases',[]),'hubs':[seed['hub']],'collection':seed['collection'],'collections':[seed['collection']],'fit':seed['fit'],'summary':seed['why'],'curatorWhy':seed['why'],'genreScope':seed['scope'],'requirements':seed.get('requirements'),'provider':label(seed['url']),'primaryUrl':seed['url'],'website':seed['url'],'kind':'Luanti game' if seed['id'] in ['external:voxelibre','external:mineclonia'] else 'Standalone game','status':seed['status'],'comingSoon':seed['status']=='Upcoming','free':seed['free'],'genres':['Survival','Sandbox'],'tags':[seed['hub'],seed['scope']],'platforms':seed.get('platforms',[]),'features':[],'reviewCount':0,'rating':None,'confidence':seed.get('confidence','Established'),'releaseDate':seed.get('releaseDate'),'releaseLabel':seed.get('releaseDate') or 'See creator release','originalReleaseYear':seed.get('originalReleaseYear'),'storefronts':[],'sources':[],'screenshots':[],'trailers':[],'warnings':[],'mediaEvidence':[],'mediaErrors':[]}
 for u in [seed['url']]+seed.get('extraUrls',[]):
  try:
   p=page(u);final=p['sourceUrl'];kind=seed.get('sourceKinds',{}).get(u,'project')
   g['sources'].append(source(final,kind));g['storefronts'].append(source(final,kind));g['mediaEvidence'].append(p)
   if u==seed['url']:g.update(verification='verified',verifiedAt=NOW)
   if p.get('image') and not g.get('image') and 'github.com' not in final:g['image']=p['image']
   for pic in p['pictures']:
    if pic!=g.get('image'):g['screenshots'].append({'src':pic,'thumbnail':pic,'sourceUrl':final,'credit':'Creator / '+label(final),'alt':g['name']+' source image','verified':True})
   for vid in p['youtube']:g['trailers'].append({'youtube':vid,'name':'Video linked by the creator','sourceUrl':final,'watchUrl':'https://www.youtube.com/watch?v='+vid,'credit':'Creator-linked video; exact title reviewed before publication'})
   for file in p['files']:g['trailers'].append({'name':'Creator website footage','sourceUrl':final,'credit':'Creator / official site',('hls' if '.m3u8' in file else 'webm' if '.webm' in file else 'mp4'):file})
   if p.get('nativeRating'):g['externalRating']=p['nativeRating']
  except Exception as e:g['mediaErrors'].append({'url':u,'error':str(e)})
 g['screenshots']=list({x['src']:x for x in g['screenshots']}.values());g['trailers']=list({x.get('youtube') or x.get('hls') or x.get('mp4') or x.get('webm'):x for x in g['trailers']}.values());g.setdefault('verification','unresolved');g['mediaCheckedAt']=NOW
 # Search results are research evidence, not auto-selected or auto-labelled official trailers.
 if not g['trailers']:
  try:g['videoCandidates']=yt_search(g['name']+' game gameplay trailer')
  except Exception as e:g['videoCandidates']={'error':str(e)}
 print('CREATOR',g['name'],g['verification'],bool(g.get('image')),len(g['trailers']),flush=True);return g

def stores(g,old,itch):
 if old and old.get('checkedAt') and (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(old['checkedAt'])).total_seconds()<604800:return g['id'],old
 links=[];checks=[];pending=[]
 methods=[('GOG',lambda:net.gog(g,'https://catalog.gog.com/v1/catalog?limit=48&productType=in:game,pack&query=')),('Official website',lambda:net.owned_site(g))]
 if itch:methods.append(('itch.io',lambda:net.itch(g)))
 else:checks.append({'provider':'itch.io','state':'unavailable-search','reason':'Known creator pages can still be verified independently.'})
 for provider,fn in methods:
  try:
   found,candidates,u=fn();links+=found;pending+=candidates;checks.append({'provider':provider,'state':'matched' if found else 'no-confirmed-match','sourceUrl':u,'matches':len(found)})
  except Exception as e:checks.append({'provider':provider,'state':'unresolved','error':str(e)})
 for item in links:
  if item['provider']=='itch.io':
   try:
    p=page(item['url']);d=p['description']
    if re.search(r'\b(?:free demo|demo version|play the demo|this demo|download.{0,20}demo)\b',d,re.I):item.update(kind='demo',editionNote='Creator page describes a demo; full-game edition is separate.')
    if re.search(r'purchas(?:e|ing).{0,15}disabled|currently unavailable',d,re.I):item.update(kind='archive',editionNote='Listing retained for provenance; purchase/download is currently disabled.')
    item['editionEvidence']=d[:700]
   except Exception as e:item['editionCheckError']=str(e)
 return g['id'],{'checkedAt':NOW,'storefronts':normalized_links(links),'storeCoverage':{'checkedAt':NOW,'checks':checks,'candidates':pending,'scope':'Exact GOG and itch.io matches and game-site outbound links. Unknown does not mean absent; this is not all worldwide key resellers.'}}

def index():
 start='https://wildforge.news/en/release-calendar/';queue=[start];seen=set();records={};pages=[]
 while queue:
  u=queue.pop(0)
  if u in seen:continue
  seen.add(u)
  try:
   raw,final,_=net.read(u);s=BeautifulSoup(raw,'html.parser');rows=[]
   for a in s.select('a[href]'):
    v=urllib.parse.urljoin(final,a['href']);text=a.get_text(' ',strip=True);m=re.search(r'store\.steampowered\.com/app/(\d+)',v)
    if m and text not in ['Steam','Steam \u2197']:
     row={'appid':int(m[1]),'name':text,'discoverySource':u};records[m[1]]=row;rows.append(row)
    if v.startswith(start) and (text in ['All','Released','Next \u2192'] or 'Next'==text.strip()):
     if v not in seen and v not in queue:queue.append(v)
   pages.append({'url':u,'records':rows,'hash':hashlib.sha256(raw.encode()).hexdigest()})
  except Exception as e:pages.append({'url':u,'error':str(e)})
 return {'checkedAt':NOW,'pages':pages,'items':list(records.values()),'terminal':not queue,'scope':'All linked pages in the small publisher/discovery calendar, followed to terminal Next. Primary Steam facts are required before recommendation.'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--external-only',action='store_true');a=ap.parse_args();cfg=load('survival-external-seeds.json',{});old={g['id']:g for g in load('survival-external.json',{'items':[]})['items']}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:ext=list(pool.map(lambda s:creator(s,old.get(s['id'])),cfg['items']))
 save('survival-external.json',{'schemaVersion':1,'generatedAt':NOW,'items':ext,'dispositions':cfg.get('dispositions',[])})
 if not (ROOT/'data/survival-discovery-index.json').exists():save('survival-discovery-index.json',index())
 old=load('survival-storefronts.json',{'overrides':{}})['overrides'];games=load('survival-steam.json',{'items':[]})['items']
 if not a.external_only and games:
  try:body,_,_=net.read('https://itch.io/search?q=Terraria');itch=bool(BeautifulSoup(body,'html.parser').select('.game_cell'))
  except Exception:itch=False
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   for i,(ident,extra) in enumerate(pool.map(lambda g:stores(g,old.get(g['id']),itch),games)):
    old[ident]=extra
    if (i+1)%30==0:save('survival-storefronts.json',{'generatedAt':NOW,'overrides':old});print('STORE COVERAGE',i+1,'/',len(games),flush=True)
  save('survival-storefronts.json',{'generatedAt':NOW,'overrides':old})
 save('survival-source-report.json',{'checkedAt':NOW,'external':len(ext),'steamStoreChecks':len(old),'alternateLinks':sum(len(x['storefronts']) for x in old.values()),'mediaGaps':[{'id':g['id'],'name':g['name'],'image':bool(g.get('image')),'video':bool(g.get('trailers'))} for g in games+ext if not g.get('image') or not g.get('trailers')]})
if __name__=='__main__':main()
