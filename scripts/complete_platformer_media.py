#!/usr/bin/env python3
"""Bounded exact-page media completion for reviewed non-Steam identities."""
from __future__ import annotations
import concurrent.futures,datetime as dt,html,json,pathlib,re,unicodedata,urllib.parse,urllib.request
from bs4 import BeautifulSoup
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.replace('\u2122','').replace('\u00ae','').casefold()) if c.isascii() and c.isalnum())
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; GamesLibrary exact-media audit)'})
 with urllib.request.urlopen(req,timeout=25) as response:return response.read(5_000_000).decode('utf-8','replace')
def enrich(g):
 page=g['primaryUrl'];host=urllib.parse.urlsplit(page).hostname;result={'id':g['id'],'source':page,'addedScreenshots':0,'addedVideos':0}
 try:
  soup=BeautifulSoup(get(page),'html.parser');screens=[];videos=[]
  title=norm(g['name']);seen=set()
  for image in soup.find_all('img'):
   alt=image.get('alt','');clean=norm(alt);src=image.get('data-src') or image.get('src','');src=html.unescape(urllib.parse.urljoin(page,src))
   if not src.startswith('https://'):continue
   if host=='www.playstation.com':
    matching=('astrobot' in clean and g['id']=='external:astro-bot') or ('astrosplayroom' in clean and g['id']=='external:astros-playroom')
    # The legacy official Playroom gallery uses 'playground' in image alt text.
    shot=('screenshot' in clean and (matching or g['id']=='external:astros-playroom' and 'astrosplayground' in clean))
    if shot and urllib.parse.urlsplit(src).hostname=='gmedia.playstation.com':
     src=urllib.parse.urlunsplit((*urllib.parse.urlsplit(src)[:3],'',''))
     if src not in seen:screens.append((src,alt));seen.add(src)
    match=re.search(r'/(?:vi|vi_webp)/([A-Za-z0-9_-]{11})/',src)
    if matching and 'trailer' in clean and match and match[1] not in {v['youtube'] for v in videos}:
     videos.append({'name':alt,'youtube':match[1],'poster':src,'watchUrl':'https://www.youtube.com/watch?v='+match[1],'sourceUrl':page,'credit':'PlayStation official game page','official':True,'verified':True,'verifiedAt':NOW})
   elif host=='www.nintendo.com':
    # Exact numbered gallery labels only. Product recommendations elsewhere on
    # the page do not have this exact-title-plus-slide-number shape.
    match=re.fullmatch(re.escape(title)+r'\d+',clean)
    if match and urllib.parse.urlsplit(src).hostname=='assets.nintendo.com' and src not in seen:
     screens.append((src,alt));seen.add(src)
  if g['id']=='external:supertux':
   for iframe in soup.find_all('iframe'):
    match=re.search(r'youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]{11})',iframe.get('src',''))
    if match and match[1]=='PQedJ3SX8s0':
     poster='https://i.ytimg.com/vi/'+match[1]+'/hqdefault.jpg'
     videos.append({'name':'SuperTux 0.7.0 official trailer','youtube':match[1],'poster':poster,'watchUrl':'https://www.youtube.com/watch?v='+match[1],'sourceUrl':page,'credit':'The SuperTux Team','official':True,'verified':True,'verifiedAt':NOW})
     # Poster is explicitly labelled as video artwork, not a screenshot.
     if not g.get('image'):g['image']=poster;g['imageCredit']='Official SuperTux 0.7.0 trailer poster'
  if screens:
   g['screenshots']=[{'src':src,'thumbnail':src,'alt':alt,'sourceUrl':page,'credit':g['provider']+' official game page','verified':True} for src,alt in screens];result['addedScreenshots']=len(screens)
  if videos:
   existing={t.get('youtube') or t.get('mp4') or t.get('hls'):t for t in g.get('trailers',[])}
   for video in videos:existing[video['youtube']]=video
   g['trailers']=list(existing.values());result['addedVideos']=len(videos)
  if screens or videos:
   g['sources']=[x for x in g['sources'] if x.get('provider')!='Exact-page media completion']+[{'provider':'Exact-page media completion','url':page,'verified':True,'lastChecked':NOW}]
   g['mediaCheckedAt']=NOW
  if g.get('image'):g['warnings']=[w for w in g.get('warnings',[]) if not w.startswith('Exact artwork not collected')]
  if g.get('trailers'):g['warnings']=[w for w in g.get('warnings',[]) if not w.startswith('No independently parsed embedded trailer')]
 except Exception as exc:result['error']=str(exc)
 print(json.dumps(result),flush=True);return g,result

def main():
 p=R/'data/platformers-external.json';data=json.loads(p.read_text())
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(enrich,data['items']))
 data['items']=[g for g,_ in results];data['generatedAt']=NOW;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 report={'checkedAt':NOW,'results':[r for _,r in results],'records':len(results),'withImages':sum(bool(g.get('image')) for g,_ in results),'withVideos':sum(bool(g.get('trailers')) for g,_ in results),'withScreenshots':sum(bool(g.get('screenshots')) for g,_ in results)}
 (R/'data/platformers-media-completion-report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
