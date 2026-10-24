#!/usr/bin/env python3
"""Targeted source cross-checks. Reference results are candidates, never auto-published facts."""
import concurrent.futures,datetime as dt,hashlib,json,pathlib,re,unicodedata,urllib.parse
from bs4 import BeautifulSoup
import discover_storefronts as net
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
IDS={609110,1686940,737890,745790,357340,268910,809880,686200,3104670,3012220,252350,311690,1054430,285900,1499700,571740,431240,477160,598550,375750,341800,1242980,2445690,2753970,296470,441010,2017080,1620040,242680,400080,1243830,1260320,1211110,108600,1111940,2129530,517710,2217000,1920480,252950,1599660,1397790,1286580,468670,1329500,277850,413150,1913740,341550,1487210,1253680,1515740,1050510,833500,1004490,437920,2211170,1225570,785790,1114290,217200,327030,362380,1004620,580890,3199470,4106530,5054700,2414270,572890,2312160,35130,570460,1451810,2051120,2165810,452060,418530,247080,636100,2305840,2996040,2215260,435150,1086940,1094870,238530,525510}
SLUGS={1086940:'baldurs-gate-3',435150:'divinity-original-sin-2',2215260:'scott-pilgrim-vs-the-world-the-game-complete-edition',2051120:'hot-wheels-unleashed-2-turbocharged',1451810:'lego-2k-drive',833500:'thunder-rally',1913740:'super-bomberman-r-2',296470:'mount-your-friends',441010:'mount-your-friends-3d-a-hard-man-is-good-to-climb'}
PAGES={'thunder-author':'https://www.indiedb.com/company/typical-entertainment','fakin-xl':'https://www.jackboxgames.com/games/fakin-it-xl','golf-it-dev':'https://steamcommunity.com/app/571740/discussions/1/1368380934251337610/','baldur-split':'https://baldursgate3.game/news/community-update-22-power-of-a-mind-flayer_74','cuphead-faq':'https://www.cupheadgame.com/faq','lost-castle-local':'https://store.steampowered.com/news/app/2445690','stardew-coop':'https://www.stardewvalley.net/stardew-valley-1-5-update-full-changelog/','gang-faq':'https://gangbeasts.game/faq','human-faq':'https://www.nobrakesgames.com/human-fall-flat','sackboy-main':'https://www.playstation.com/en-us/games/sackboy-a-big-adventure/','spider-epic':'https://store.epicgames.com/id/p/spiderheck-0fb81d','necro-multi':'https://braceyourselfgames.com/crypt-of-the-necrodancer/faq/','quiplash2':'https://www.jackboxgames.com/games/quiplash-2-interlashional'}
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def inspect(key,url,name=None):
 try:
  raw,final,_=net.read(url);s=BeautifulSoup(raw,'html.parser');title=s.title.get_text(' ',strip=True) if s.title else '';tables=[t.get_text(' ',strip=True) for t in s.select('table')]
  for n in list(s.select('nav,footer,#comments,.comments')):n.decompose()
  text=s.get_text(' ',strip=True);return {'id':key,'sourceUrl':final,'title':title,'titleMatches':norm(name) in norm(title) if name else None,'text':text,'tables':tables,'pageHash':hashlib.sha256(raw.encode()).hexdigest(),'checkedAt':NOW}
 except Exception as e:return {'id':key,'sourceUrl':url,'state':'unresolved-active','error':str(e)}
def main():
 rows={g['id']:g for f in ['party-steam.json','party-extra.json','party-recovered.json'] for g in json.loads((R/'data'/f).read_text())['items']}
 tasks=[]
 for ident,g in rows.items():
  if g.get('appid') not in IDS:continue
  name=g.get('seedName',g['name']);slug=SLUGS.get(g['appid']) or re.sub('-+','-',re.sub('[^a-z0-9 -]','',unicodedata.normalize('NFKD',name.replace('\u2122','').replace('\u00ae','').replace('&','and')).encode('ascii','ignore').decode().lower()).replace(' ','-')).strip('-')
  tasks.append((ident,'https://playco-opgame.com/'+slug+'/',name))
 tasks.extend((k,u,None) for k,u in PAGES.items())
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:report=list(p.map(lambda x:inspect(*x),tasks))
 vids=['MoLm2nS0hsY','H1Lo7PlTGBk','-Pnl_EEaX-M']
 for f in ['party-missing-video-candidates.json']:
  d=json.loads((R/'data'/f).read_text())['records']
  for ident,r in d.items():
   good=[x for x in r.get('results',[]) if x.get('author') in ['Nintendo of America','Nintendo UK','Team17','Paradox Interactive','ParadoxExtra','Red Beard Games','Hex Party']]
   vids.extend(x['id'] for x in good)
 def video(v):
  u='https://www.youtube.com/oembed?'+urllib.parse.urlencode({'url':'https://www.youtube.com/watch?v='+v,'format':'json'})
  try:return {'id':v,**net.api(u)}
  except Exception as e:return {'id':v,'error':str(e)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:metadata=list(p.map(video,dict.fromkeys(vids)))
 out={'generatedAt':NOW,'records':report,'videos':metadata};(R/'data/party-mode-references.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'references':len(report),'readable':sum('text' in x for x in report),'identityMatched':sum(x.get('titleMatches') is True for x in report),'videos':metadata},indent=2))
if __name__=='__main__':main()
