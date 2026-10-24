"""Review only the new survival study's recent-date slice against official Steam HTML.
The store API's release date can be a later 1.0 milestone. Preserve that date,
record the separately labelled Early Access date, and never infer history from
an absent label or a blocked response. No unrelated game facts are refreshed.
"""
import concurrent.futures,datetime as dt,hashlib,json,pathlib,re,threading,time,urllib.parse,urllib.request
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
NOW=dt.datetime.now(dt.timezone.utc).isoformat()
LOCK=threading.Lock();NEXT=0.0

def iso(text):
 for fmt in ['%b %d, %Y','%d %b, %Y','%B %d, %Y','%d %B, %Y']:
  try:return dt.datetime.strptime(text.strip(),fmt).date().isoformat()
  except ValueError:pass
 return None

def fetch(url):
 global NEXT
 with LOCK:
  delay=max(0,NEXT-time.monotonic());NEXT=max(NEXT,time.monotonic())+1.1
 if delay:time.sleep(delay)
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; GamesLibrary/1.5; +https://github.com/Herbertofury/Games)','Accept-Language':'en-US,en;q=0.9'})
 with urllib.request.urlopen(req,timeout=22) as r:return r.read(7000000).decode('utf-8',errors='replace'),r.url

def review(g):
 url='https://store.steampowered.com/app/'+str(g['appid'])+'/?l=english&cc=us'
 try:
  raw,final=fetch(url);s=BeautifulSoup(raw,'html.parser');title=s.select_one('#appHubAppName,.apphub_AppName')
  if title is None:raise ValueError('Exact game heading unavailable; no chronology inferred')
  label=next((b for b in s.select('.details_block b') if b.get_text(' ',strip=True).lower().rstrip(':')=='early access release date'),None)
  row={'id':g['id'],'name':g['name'],'officialTitle':title.get_text(' ',strip=True),'sourceUrl':url,'finalUrl':final,'checkedAt':NOW,'pageSha256':hashlib.sha256(raw.encode()).hexdigest(),'storeReleaseDate':g.get('releaseDate')}
  if label:
   parts=[]
   for n in label.next_siblings:
    if getattr(n,'name',None)=='br':break
    parts.append(n.get_text(' ',strip=True) if hasattr(n,'get_text') else str(n))
   literal=' '.join(parts).strip();date=iso(literal)
   if not date:raise ValueError('Unrecognized official Early Access date: '+literal)
   assert not g.get('releaseDate') or date<=g['releaseDate'],'Early Access date follows displayed full release; manual review required'
   row.update(state='earlier-access-confirmed',earlyAccessReleaseDate=date,evidence='Steam explicitly labels Early Access Release Date: '+literal)
   earliest=min(int(date[:4]),int(g.get('originalReleaseYear') or date[:4]))
   override={'earlyAccessReleaseDate':date,'originalReleaseYear':earliest,'releaseChronology':{'earlyAccess':date,'storeMilestone':g.get('releaseDate'),'sourceUrl':url,'evidence':row['evidence'],'checkedAt':NOW},'sources':[{'url':url,'provider':'Steam','kind':'source','verified':True,'lastChecked':NOW,'evidence':row['evidence']}]}
   return row,override
  row.update(state='no-separate-early-access-label',evidence='No separately labelled Early Access date was present in the readable official details block. This is not proof of no earlier non-Steam release.')
  return row,None
 except Exception as e:return {'id':g['id'],'name':g['name'],'sourceUrl':url,'checkedAt':NOW,'state':'unresolved-active','error':str(e)},None

def main():
 catalog=json.loads((ROOT/'data/catalog.json').read_text())
 rows=[g for g in catalog['items'] if g.get('appid') and any(h in g.get('hubs',[]) for h in ['Survival','Minecraft-like worlds']) and not g.get('comingSoon') and (g.get('releaseDate') or '')>='2025-01-01']
 results=[];overrides={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for row,extra in pool.map(review,rows):
   results.append(row)
   if extra:overrides[row['id']]=extra
   print(row['state'],row['name'],row.get('earlyAccessReleaseDate',''),flush=True)
 assert len(results)==len(rows)
 report={'checkedAt':NOW,'scope':'Only recent-dated Steam entries in the two requested survival hubs. Steam 1.0/store milestones remain intact; earlier access dates are independently labelled.','reviewed':len(results),'confirmedEarlierAccess':len(overrides),'unresolved':[r for r in results if r['state']=='unresolved-active'],'checks':results}
 (ROOT/'data/survival-chronology.json').write_text(json.dumps({'schemaVersion':1,'generatedAt':NOW,'overrides':overrides},ensure_ascii=False,indent=2)+'\n')
 (ROOT/'data/survival-chronology-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
