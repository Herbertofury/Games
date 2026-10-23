#!/usr/bin/env python3
"""Read-only media audit. Candidate IDs are evidence to review, not auto-approval."""
from __future__ import annotations
import concurrent.futures,hashlib,json,pathlib,re,urllib.request
from bs4 import BeautifulSoup
R=pathlib.Path(__file__).resolve().parents[1];O=R/'qa/platformer-video-audit';O.mkdir(parents=True,exist_ok=True)
extras={
 'external:super-mario-odyssey':['https://play.nintendo.com/media/videos/super-mario-odyssey-nintendo-switch-trailer/'],
 'external:super-mario-bros-wonder':['https://www.nintendo.com/my/switch/aqmx/movie/index.html','https://supermariobroswonder.nintendo.com/'],
 'external:yoshi-mysterious-book':['https://www.nintendo.com/sg/news/article/7tnSs18hMgO4O9y3gUpluL'],
 'steam:2661310':['https://www.yachtclubgames.com/games/shovel-knight-shovel-of-hope-dx/'],
}
def scan(pair):
 ident,url=pair;key=ident.replace(':','-')+'-'+hashlib.sha256(url.encode()).hexdigest()[:10];row={'id':ident,'url':url,'file':key+'.html'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; GamesLibrary source audit)'})
  with urllib.request.urlopen(req,timeout=25) as response:
   raw=response.read(6000000);row['resolvedUrl']=response.url;row['httpStatus']=response.status
  text=raw.decode('utf-8','replace');(O/row['file']).write_text(text);soup=BeautifulSoup(text,'html.parser');row['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
  row['embeds']=[dict(tag.attrs) for tag in soup.find_all(['iframe','video','source'])]
  row['youtubeCandidates']=list(dict.fromkeys(re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([a-zA-Z0-9_-]{11})',text)))
  row['mediaContexts']=[m.group(0) for m in re.finditer(r'.{0,140}(?:videoId|youtube|brightcove|m3u8|videoUrl|video_url|video/|VideoPlayer).{0,250}',text,re.I)][:120]
  row['metadataObjects']=[]
  for tag in soup.find_all('script',attrs={'type':'application/json'}):
   try:
    obj=json.loads(tag.get_text())
    def walk(x,path):
     if isinstance(x,dict):
      if any('video' in str(k).lower() or 'video' in str(v).lower()[:30] for k,v in x.items() if not isinstance(v,(list,dict))):row['metadataObjects'].append({'path':path,'value':x})
      for k,v in x.items():walk(v,path+'/'+k)
     elif isinstance(x,list):
      for n,v in enumerate(x):walk(v,path+'/'+str(n))
    walk(obj,tag.get('id','script'))
   except Exception:pass
 except Exception as e:row['error']=str(e)
 print(json.dumps({k:v for k,v in row.items() if k in ['id','url','title','youtubeCandidates','error']}),flush=True);return row
report=json.loads((R/'data/platformers-study-report.json').read_text());jobs=[]
for g in report['mediaGaps']:
 jobs.extend((g['id'],u) for u in [g['source']]+extras.get(g['id'],[]))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(scan,jobs))
(O/'audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print('Audited',len(rows),'exact pages; no catalog facts changed.')
