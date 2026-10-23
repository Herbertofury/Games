"""Complete changed source slices using retained evidence, not a repeated full crawl."""
import argparse,concurrent.futures,datetime as dt,hashlib,html,json,pathlib,re,subprocess,urllib.parse,urllib.request
from bs4 import BeautifulSoup
import collect_metroidvania as core,enrich_metroidvania as enrich,discover_storefronts as net
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
def read(name,default):
 p=R/'data'/name;return json.loads(p.read_text()) if p.exists() else default
def save(name,data):(R/'data'/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def source(url,provider,kind='project',**extra):return dict(url=url,provider=provider,kind=kind,verified=True,lastChecked=NOW,**extra)
def title_key(s):return re.sub('[^a-z0-9]','',(s or '').lower())
def clean_url(u):
 p=urllib.parse.urlsplit(html.unescape(u));q=[]
 for k,v in urllib.parse.parse_qsl(p.query):
  while k.startswith('amp;'):k=k[4:]
  if k.lower().startswith(('utm_','hmb_')) or k in ['_xm','ref','referrer','snr']:continue
  q.append((k,v))
 return urllib.parse.urlunsplit((p.scheme,p.netloc,p.path,urllib.parse.urlencode(q),''))
def yt_search(q):
 url='https://www.youtube.com/results?search_query='+urllib.parse.quote(q);raw,_,_=net.read(url);m=re.search(r'(?:var\s+)?ytInitialData\s*=\s*',raw)
 if not m:raise ValueError('No public video metadata')
 d=json.JSONDecoder().raw_decode(raw[m.end():])[0];out=[]
 def text(v):return v.get('simpleText') or ''.join(x.get('text','') for x in v.get('runs',[]))
 def walk(x):
  if isinstance(x,dict):
   if 'videoRenderer' in x:
    v=x['videoRenderer'];out.append({'youtube':v.get('videoId'),'title':text(v.get('title',{})),'author':text(v.get('ownerText',{}))})
   else:
    for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(d);return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence',default='qa/metroidvania-media');a=ap.parse_args();E=R/a.evidence;plan=read('metroidvania-completion-plan.json',{});e=json.loads((E/'report.json').read_text());pages={p['id']:p for p in e['pages']};steam=read('metroidvania-steam.json',{});ext=read('metroidvania-external.json',{});overrides=read('metroidvania-media.json',{'overrides':{}})['overrides'];evidence=read('metroidvania-resolved-media.json',{'videos':{},'sources':{},'searches':{}})
 for p in e['pages']:
  if p.get('error'):continue
  evidence['sources'][p['id']]={k:p.get(k) for k in ['url','final','title','metadata']}
 # Resolve only three already identified Steam titles; current cached entries are reused.
 for seed in plan['steam']:
  g=core.resolve(seed,steam['items'],False)
  if not g.get('id'):raise ValueError('Selected exact Steam identity failed: '+str(g))
  steam['items']=[x for x in steam['items'] if x['id']!=g['id']]+[g]
 steam['items'].sort(key=lambda x:x['name'].casefold())
 # Nintendo's current official storefront supplies artwork/date; a secondary old subdomain is not needed.
 for ident,u in plan['sourceCorrections'].items():
  p=pages[ident];assert not p.get('error'),p
  patch=overrides.setdefault(ident,{});patch.update(primaryUrl=u,verification='verified',verifiedAt=NOW,mediaErrors=[])
  patch.setdefault('_replace',{})['storefronts']=[source(u,enrich.provider(u),'store' if 'nintendo' in u else 'project')];patch['sources']=[source(u,enrich.provider(u))]
 for g in ext['items']:
  p=pages.get(g['id']);patch=overrides.setdefault(g['id'],{})
  if not p or p.get('error'):continue
  og=next((x.get('content') for x in p.get('images',[]) if x.get('property')=='og:image'),None)
  if og:patch.setdefault('_replace',{})['image']=og
  patch.update(verification='verified',verifiedAt=NOW,mediaErrors=[])
  m=re.search(r'Rated ([\d.]+) out of (\d+) stars \((\d+) total',p.get('metadata',''))
  if m:patch['externalRating']={'provider':'itch.io','value':float(m[1]),'max':int(m[2]),'count':int(m[3]),'sourceUrl':p['final'],'checkedAt':NOW}
  platforms=[label for key,label in [('Windows','windows'),('Linux','linux'),('macOS','mac'),('HTML5','Web browser')] if key in p.get('metadata','')]
  if platforms:patch['platforms']=platforms
  if not g.get('storefronts'):patch['storefronts']=[source(p['final'],enrich.provider(p['final']),'prototype' if g['status']=='Prototype' else 'project')]
  if g.get('verification')!='verified':patch['sources']=[source(p['final'],enrich.provider(p['final']))]
  rawfile=E/(re.sub('[^a-zA-Z0-9_-]','_',g['id'])+'.html')
  if rawfile.exists() and '.itch.io/' in g['primaryUrl']:
   soup=BeautifulSoup(rawfile.read_text(),'html.parser');pics=[]
   for n in soup.select('.screenshot_list .screenshot,.screenshot_list a[href],.screenshots .screenshot'):
    u=n.get('href') or n.get('src');srcset=n.get('srcset','')
    if srcset:u=srcset.split(', ')[-1].rsplit(' ',1)[0]
    if u and u.startswith('https://img.itch.zone/'):pics.append(u)
   if pics:patch.setdefault('_replace',{})['screenshots']=[{'src':u,'thumbnail':u,'sourceUrl':p['final'],'credit':'Creator / itch.io','alt':g['name']+' screenshot','verified':True} for u in dict.fromkeys(pics)]
 # Build author/store-hosted additions from exact retained pages. Unknown PC availability is never invented.
 adds=[]
 for seed in plan['externalAdds']:
  ident='external:'+seed['slug'];p=pages.get(seed.get('evidenceKey'))
  if not p:
   raw,final,_=net.read(seed['url']);s=BeautifulSoup(raw,'html.parser');p={'url':seed['url'],'final':final,'title':s.title.get_text(' ',strip=True),'images':[dict(n.attrs) for n in s.select('meta[property="og:image"],img')]};(E/(seed['slug']+'.html')).write_text(raw)
  assert not p.get('error'),(ident,p)
  g={'id':ident,'name':seed['name'],'seedName':seed['name'],'collection':'Console origins & genre landmarks' if 'Nintendo' in ' '.join(seed.get('platforms',[])) else 'Freeware & creator-hosted worlds','hubs':['Metroidvanias'],'fit':seed['fit'],'summary':seed['why'],'curatorWhy':seed['why'],'genreScope':seed['scope'],'provider':enrich.provider(seed['url']),'primaryUrl':seed['url'],'platforms':seed.get('platforms',[]),'genres':['Adventure'],'features':[],'tags':['Metroidvanias',seed['scope']],'status':seed.get('status','Released'),'comingSoon':seed.get('status')=='Upcoming','free':seed['free'],'rating':None,'reviewCount':0,'releaseDate':seed.get('releaseDate'),'releaseYear':seed.get('releaseYear'),'releaseLabel':seed.get('releaseDate') or str(seed.get('releaseYear') or 'See creator release'),'originalReleaseYear':seed.get('originalReleaseYear'),'kind':'Console game' if 'Nintendo' in ' '.join(seed.get('platforms',[])) else 'Standalone game','confidence':'Established','verification':'verified','verifiedAt':NOW,'storefronts':[source(seed['url'],enrich.provider(seed['url']),'wishlist' if seed.get('status')=='Upcoming' else 'subscription' if seed['slug'] in ['super-metroid','metroid-fusion','metroid-zero-mission'] else 'store' if enrich.provider(seed['url']) in ['GOG','Nintendo'] else 'project')],'sources':[source(p['final'],enrich.provider(p['final']))],'screenshots':[],'trailers':[]}
  if seed.get('requirements'):g['requirements']=seed['requirements']
  if seed.get('downloadUrl'):g['storefronts'].append(source(seed['downloadUrl'],'Official site','download'))
  if seed.get('imageContains'):
   g['image']=next(x['src'] for x in p['images'] if seed['imageContains'] in x.get('src',''))
  elif not seed.get('imageFromOfficialVideo'):g['image']=next((x.get('content') for x in p['images'] if x.get('property')=='og:image'),None)
  if seed.get('extraUrl'):
   raw,final,_=net.read(seed['extraUrl']);vids=re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})',html.unescape(raw.replace('\\/','/')))
   evidence['sources'][ident]={'url':final,'title':p['title'],'videoCandidates':list(dict.fromkeys(vids))};g['sources'].append(source(final,'Nintendo'))
   if vids:plan['videos'][ident]={'youtube':vids[0],'titleContains':seed['name'],'official':True,'credit':'Nintendo','name':'Official announcement trailer'}
  adds.append(g)
 ext['items']=[g for g in ext['items'] if g['id'] not in {x['id'] for x in adds}]+adds
 allgames={g['id']:g for g in steam['items']+ext['items']}
 # Exact creator gameplay loop transforms preserve all original frames, with an explicit non-trailer label.
 media_dir=R/'media/metroidvania';media_dir.mkdir(parents=True,exist_ok=True)
 for item in plan['sourceBoundMotion']:
  dest=media_dir/item['filename']
  if not dest.exists():
   req=urllib.request.Request(item['url'],headers={'User-Agent':net.UA})
   with urllib.request.urlopen(req,timeout=30) as resp:raw=resp.read()
   gif=media_dir/(dest.stem+'.gif');gif.write_bytes(raw);subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(gif),'-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2','-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True);gif.unlink()
   evidence['sources'][item['filename']]={'sourceUrl':item['sourceUrl'],'originalAssetUrl':item['url'],'originalSha256':hashlib.sha256(raw).hexdigest(),'videoSha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
  overrides.setdefault(item['id'],{}).setdefault('_replace',{}).setdefault('trailers',[]).append({'mp4':'https://raw.githubusercontent.com/Herbertofury/Games/main/media/metroidvania/'+dest.name,'name':item['name'],'official':True,'credit':'salmoone; loss-preserving GIF-to-MP4 presentation','sourceUrl':item['sourceUrl'],'originalAssetUrl':item['url']})
 # Resolve official publisher video IDs, not the first unrelated search result.
 for ident,query in plan['videoSearches'].items():
  if ident in plan['videos']:continue
  candidates=yt_search(query);evidence['searches'][ident]=candidates
  required='Metroid Dread' if ident.endswith('dread') else 'Metroid Prime 4' if ident.endswith('prime-4') else 'Metroid Ravenous'
  v=next((x for x in candidates if x['author'] in ['Nintendo of America','Nintendo UK','Nintendo'] and title_key(required) in title_key(x['title'])),None)
  if not v:raise ValueError('Official video identity requires manual review: '+ident)
  plan['videos'][ident]={'youtube':v['youtube'],'titleContains':required,'official':True,'credit':v['author'],'name':v['title']}
 for ident,v in plan['videos'].items():
  url='https://www.youtube.com/watch?v='+v['youtube'];m=net.api('https://www.youtube.com/oembed?url='+urllib.parse.quote(url,safe='')+'&format=json');assert title_key(v['titleContains']) in title_key(m['title']),(ident,m['title']);evidence['videos'][v['youtube']]={**m,'watchUrl':url,'checkedAt':NOW}
  trailer={k:value for k,value in v.items() if k!='titleContains'};trailer.update(watchUrl=url,sourceUrl=allgames[ident]['primaryUrl'],poster=m.get('thumbnail_url'))
  overrides.setdefault(ident,{}).setdefault('_replace',{})['trailers']=[trailer]
  if ident in ['external:metroid-fusion','external:metroid-zero-mission']:overrides[ident]['_replace']['image']=m['thumbnail_url']
 for ident,v in plan['nativeVideos'].items():
  if v.get('vimeo'):
   m=net.api('https://vimeo.com/api/oembed.json?url='+urllib.parse.quote(v['sourceUrl'],safe=''));assert 'doomedknight' in title_key(m['title']);evidence['videos']['vimeo:'+v['vimeo']]={**m,'checkedAt':NOW}
  overrides.setdefault(ident,{}).setdefault('_replace',{})['trailers']=[v]
 for ident,v in plan['imageCorrections'].items():
  patch=overrides.setdefault(ident,{}).setdefault('_replace',{});patch['image']=v['image'];patch['screenshots']=[{'src':u,'thumbnail':u,'sourceUrl':v['sourceUrl'],'credit':'Original creator','alt':allgames[ident]['name']+' official image','verified':True} for u in v.get('gallery',[v['image']])]
 for ident,date in plan['consoleDates'].items():overrides.setdefault(ident,{}).update(releaseDate=date,releaseLabel=date,releaseYear=int(date[:4]))
 # Repair double-escaped tracking links and retain edition-specific distinctions.
 stores=read('metroidvania-storefronts.json',{'overrides':{}})
 for ident,row in stores['overrides'].items():
  cleaned={}
  for l in row.get('storefronts',[]):
   l['url']=clean_url(l['url']);u=l['url'].rstrip('/')
   if u in plan['unconfirmedStoreLinks']:row.setdefault('unconfirmedSources',[]).append(l);continue
   if u in plan['editionCorrections']:l.update(plan['editionCorrections'][u],editionNote='Explicit creator demo edition, not a second full game.')
   cleaned[u]=l
  row['storefronts']=list(cleaned.values())
 # Existing community links and direct downloads are not lost just because one provider blocks an automated read.
 necro=allgames['external:necrowave'];raw=(E/'external_necrowave.html').read_text();assert 'patreon.com/Necrowave'.lower() in raw.lower();overrides['external:necrowave'].setdefault('storefronts',[]).append(source('https://www.patreon.com/Necrowave','Patreon','support',sourceUrl=necro['primaryUrl'],editionNote='Creator support linked from the official game website. Membership is not a full-game license.'))
 # Exact archived aliases resolve to existing records, not duplicate rows.
 resolved_keys={core.key(g['name']) for g in steam['items']}|{core.key(x) for g in steam['items'] for x in g.get('aliases',[])}
 dispositions=[];pending=[]
 aliases={'Grime 2':'GRIME II','The Light of the Darkness':'The Light of the Darkness: Renascence','Distant Paradise':'Silent Paradise Anthology','An Untitled Story':'An Untitled Story','Sunset Land':'Sunset Land'}
 for p in steam.get('unresolved',[]):
  if core.key(p['candidate']) in resolved_keys or p['candidate'] in aliases:dispositions.append({'candidate':p['candidate'],'state':'reconciled','canonical':aliases.get(p['candidate'],p['candidate'])})
  else:pending.append(p)
 steam.update(unresolved=pending,generatedAt=NOW);ext['generatedAt']=NOW
 save('metroidvania-steam.json',steam);save('metroidvania-external.json',ext);save('metroidvania-storefronts.json',stores);save('metroidvania-media.json',{'generatedAt':NOW,'overrides':overrides});save('metroidvania-resolved-media.json',evidence);save('metroidvania-reconciliation.json',{'generatedAt':NOW,'dispositions':steam.get('dispositions',[])+dispositions,'duplicateCandidates':steam.get('duplicates',[]),'unresolved':pending})
 report={'steam':len(steam['items']),'external':len(ext['items']),'resolvedMediaOverrides':len(overrides),'remainingSourceCandidates':len(pending),'recordedPreviewsPending':['external:spellsought','external:reawakening','external:mongrel-story']};save('metroidvania-completion-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
