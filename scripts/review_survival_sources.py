#!/usr/bin/env python3
"""Targeted media/source evidence. No first-result video is silently promoted."""
import concurrent.futures,hashlib,html,json,pathlib,re,sys,urllib.parse
from bs4 import BeautifulSoup
import collect_survival_sources as sources,collect_survival as steam,discover_storefronts as net
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'qa/survival-source-review';OUT.mkdir(parents=True,exist_ok=True)
VIDEOS=['qNMfF9TYETM','_NNh6Dz7YpA','NJjifFq1NGY','GyQAcUmhV-g','8EMI5CLx2IA','weIK41W3tX0','nv1A8O8WMec','nUTIt5P_K-w','Wpa2aiadwE8','TA__7nTBUHY','HzQnRm3FmOE','TFE9s-psT40','lE7xKsbWD04','Iqr3XIhSnUQ']
PAGES={
 'luun-itch':'https://countsie.itch.io/luun',
 'mine-blocks':'https://mineblocks.com/',
 'hytale-latest':'https://hytale.com/news/2026/10/chapter-i-out-of-the-breach',
 'hytale-download':'https://support.hytale.com/hc/en-us/articles/45305997507739-How-to-Download-and-Play-Hytale',
 'vintage-store':'https://www.vintagestory.at/store/category/1-single-game-account/',
 'vintage-humble':'https://www.humblebundle.com/store/vintage-story',
 'windrose':'https://playwindrose.com/',
 'windrose-epic':'https://store.epicgames.com/en-US/p/windrose-831c86',
 'path-titans-buy':'https://alderongames.com/store/path-of-titans',
 'survivalcraft':'https://kaalus.wordpress.com/survivalcraft/',
 'unrealworld-downloads':'https://www.unrealworld.fi/urw_downloads.html',
 'haven':'https://www.havenandhearth.com/portal/about',
 'minecraft':'https://www.minecraft.net/en-us/store/minecraft-java-bedrock-edition-pc',
 'lego-odyssey':'https://www.fortnite.com/@epic/lego-fortnite-odyssey'
}
QUERIES={'external:minicraft-plus':'"Minicraft Plus" gameplay','external:luun':'"LUUN" survival game gameplay','steam:4861650':'"FrontierCraft" Innershed gameplay','external:mine-blocks':'"Mine Blocks" Zanzlanz update 1.31','external:mine-blocks-2':'"Mine Blocks 2" Zanzlanz 0.8'}
def video(v):
 u='https://www.youtube.com/oembed?url='+urllib.parse.quote('https://www.youtube.com/watch?v='+v,safe='')+'&format=json'
 try:return {'id':v,'sourceUrl':u,**net.api(u)}
 except Exception as e:return {'id':v,'sourceUrl':u,'error':str(e)}
def page(pair):
 key,u=pair
 try:
  raw,final,typ=net.read(u);(OUT/(key+'.html')).write_text(raw);p=sources.page(u);s=BeautifulSoup(raw,'html.parser');main=s.select_one('.formatted_description') or s.select_one('main') or s.select_one('article') or s
  p['id']=key;p['allLinks']=[{'label':a.get_text(' ',strip=True),'url':urllib.parse.urljoin(final,a['href'])} for a in main.select('a[href]')];p['images']=[dict(n.attrs) for n in main.select('img,meta[property="og:image"]')];p['uploads']=[n.get_text(' ',strip=True) for n in s.select('.upload_list_widget .upload')];p['metadata']=s.select_one('.game_info_panel_widget').get_text(' ',strip=True) if s.select_one('.game_info_panel_widget') else '';return p
 except Exception as e:return {'id':key,'sourceUrl':u,'error':str(e)}
def search(pair):
 key,q=pair
 try:return {'id':key,**sources.yt_search(q)}
 except Exception as e:return {'id':key,'query':q,'error':str(e)}
def main():
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:pages=list(p.map(page,PAGES.items()))
 extra=[]
 for r in pages:
  if r['id']=='mine-blocks':
   for l in r.get('allLinks',[]):
    if ('youtube.com' in l['url'] or 'youtu.be' in l['url']) and ('update' in l['label'].lower() or l['label']):
     m=re.search(r'(?:v=|youtu.be/)([A-Za-z0-9_-]{11})',l['url'])
     if m:extra.append(m[1])
 ids=list(dict.fromkeys(VIDEOS+extra+[v for r in pages if r['id'] in ['luun-itch','hytale-latest'] for v in r.get('youtube',[])]))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:videos=list(p.map(video,ids))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:searches=list(p.map(search,QUERIES.items()))
 seeds=[{'name':'Haven & Hearth','appid':3051280,'hub':'Survival','collection':'Persistent servers & competitive survival','fit':8,'scope':'Hardcore online survival crafting','aliases':[]},{'name':'Wild West Legacy','appid':1329880,'hub':'Survival','collection':'Tribes, settlements & historical frontiers','fit':7,'scope':'Survival / settlement building','aliases':['Wild West Dynasty']}]
 games=[steam.resolve(s,{},False) for s in seeds]
 report={'videos':videos,'pages':pages,'searches':searches,'steamAdditions':games};(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'videos':videos,'pages':[{'id':r['id'],'title':r.get('title'),'youtube':r.get('youtube'),'error':r.get('error')} for r in pages],'searches':searches,'steam':[{'id':g.get('id'),'name':g.get('name'),'error':g.get('error')} for g in games]},indent=2))
if __name__=='__main__':main()
