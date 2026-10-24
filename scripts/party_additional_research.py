#!/usr/bin/env python3
"""Targeted additions, official Nintendo video reuse, and reviewable media candidates."""
import concurrent.futures,datetime as dt,json,pathlib,re,urllib.parse
from bs4 import BeautifulSoup
import collect_party as core,discover_storefronts as net
from resolve_platformer_videos import nintendo_product
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
def load(n,d):
 p=R/'data'/n;return json.loads(p.read_text()) if p.exists() else d
def save(n,d):(R/'data'/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def search_video(q):
 url='https://www.youtube.com/results?search_query='+urllib.parse.quote(q);raw,_,_=net.read(url);m=re.search(r'(?:var\s+)?ytInitialData\s*=\s*',raw)
 if not m:raise ValueError('No public video metadata; no bypass attempted')
 data=json.JSONDecoder().raw_decode(raw[m.end():])[0];out=[]
 def text(v):return v.get('simpleText') or ''.join(x.get('text','') for x in v.get('runs',[]))
 def walk(x):
  if isinstance(x,dict):
   if 'videoRenderer' in x:
    v=x['videoRenderer'];out.append({'id':v.get('videoId'),'title':text(v.get('title',{})),'author':text(v.get('ownerText',{})),'length':text(v.get('lengthText',{}))})
   else:
    for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(data);return {'query':q,'sourceUrl':url,'results':out}
def main():
 cfg=load('party-additions.json',{});old=load('party-extra.json',{}).get('items',[]);existing=load('catalog.json',{}).get('items',[]);seeds=[]
 for name,col,fit,cap,mode,part,aid,note in cfg['steam']:
  seeds.append(dict(name=name,collection=col,fit=str(fit),countHint=str(cap),modeHint=mode,participation=part,appid=str(aid) if aid else '',note=note))
 items=[];pending=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for g in pool.map(lambda s:core.collect(s,old,existing,False),seeds):
   (items if g.get('id') else pending).append(g);print('EXTRA',g.get('name',g.get('candidate')),flush=True)
 save('party-extra.json',{'schemaVersion':1,'generatedAt':NOW,'items':items,'dispositions':pending})
 stores=load('party-extra-stores.json',{'overrides':{}})
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for ident,extra in pool.map(lambda g:core.alternatives(g,stores['overrides'].get(g['id']),True),items):stores['overrides'][ident]=extra
 save('party-extra-stores.json',stores)
 ext=load('party-external.json',{}).get('items',[]);media=load('party-video-candidates.json',{'nintendo':{},'searches':{},'metadata':{},'sourcePages':{}})
 def resolve(g):
  try:
   if 'nintendo.com' in g['primaryUrl']:
    v,proof=nintendo_product(g);return g['id'],{'video':v,'proof':proof},None
   queries={'external:supertuxkart':'SuperTuxKart official trailer 1.5','external:puff-puff-push':'Puff Puff Push Typimals game gameplay','external:mutiny-bomb':'MUTINY zsfer local multiplayer bomb game','external:duck-cover-2':'Duck and Cover 2 Siddikinz gameplay','external:pshnggg':'PSHNGGG Zephyrware game','external:square-off-shiba':'Square Off Shiba Dog Studios gameplay','external:duck-and-gun':'Duck and Gun chelbling game jam','external:sumaburu':'Sumaburu JakeyMG gameplay','external:sumo-dumo':'Sumo Dumo sparacios game'}
   if g['id'] in queries:return g['id'],None,search_video(queries[g['id']])
   return g['id'],None,None
  except Exception as e:return g['id'],{'error':str(e)},None
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for ident,nintendo,search in pool.map(resolve,ext):
   if nintendo:media['nintendo'][ident]=nintendo
   if search:media['searches'][ident]=search
 ids=list(dict.fromkeys(t['youtube'] for g in ext for t in g.get('trailers',[]) if t.get('youtube')))
 def oembed(vid):
  url='https://www.youtube.com/oembed?'+urllib.parse.urlencode({'url':'https://www.youtube.com/watch?v='+vid,'format':'json'})
  try:return vid,net.api(url)
  except Exception as e:return vid,{'error':str(e)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for vid,m in pool.map(oembed,ids):media['metadata'][vid]=m
 for url in cfg['sourcePages']:
  try:
   raw,final,_=net.read(url);s=BeautifulSoup(raw,'html.parser');media['sourcePages'][url]={'url':final,'title':s.title.get_text(' ',strip=True) if s.title else '', 'text':s.get_text(' ',strip=True),'links':[{'url':urllib.parse.urljoin(final,a['href']),'text':a.get_text(' ',strip=True)} for a in s.select('a[href]') if any(t in a['href'] for t in ['jackbox','steampowered','epicgames','youtu','gog.com'])]}
  except Exception as e:media['sourcePages'][url]={'error':str(e)}
 media['checkedAt']=NOW;save('party-video-candidates.json',media);print(json.dumps({'extraGames':len(items),'unresolved':pending,'externalVideoQueries':len(media['searches']),'nintendoVideoResults':{k:bool(v.get('video')) for k,v in media['nintendo'].items()}},indent=2))
if __name__=='__main__':main()
