#!/usr/bin/env python3
"""Reconcile the first research pass without repeating unchanged successful work."""
import argparse,concurrent.futures,datetime as dt,json,pathlib,threading,time,urllib.parse
import collect_survival as core
R=pathlib.Path(__file__).resolve().parents[1]
lock=threading.Lock();next_at=0.0
def paced(url):
 global next_at
 if urllib.parse.urlsplit(url).hostname=='store.steampowered.com':
  with lock:wait=max(0,next_at-time.monotonic());next_at=max(next_at,time.monotonic())+1.1
  if wait:time.sleep(wait)
 return core._original_get(url)
core.refresh.get=paced

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');args=ap.parse_args();cfg=core.load('survival-expansion.json',{});old=core.load('survival-steam.json',{'items':[],'unresolved':[]});prior={g['appid']:g for g in old['items']};seeds,ledger=core.seeds();new={core.norm(s['name']):s for s in seeds};dispositions=cfg.get('dispositions',{});pending={core.norm(x['candidate']):x for x in old.get('unresolved',[])}
 for s in seeds:
  if s['name'] in cfg['corrections']:s.update(cfg['corrections'][s['name']])
 for name,aid,hub,col,fit,scope in cfg.get('additionalSteam',[]):
  if name in cfg.get('supplementExclusions',{}):ledger.append({'candidate':name,'state':'excluded','reason':cfg['supplementExclusions'][name]});continue
  new[core.norm(name)]={'name':name,'appid':aid,'hub':hub,'collection':col,'fit':fit,'scope':scope,'aliases':[]}
 # Followed-to-terminal discovery calendar remains a discovery source, not a release-date authority.
 index=core.load('survival-discovery-index.json',{'items':[]})
 knownids={s.get('appid') for s in new.values() if s.get('appid')}
 for d in index['items']:
  if core.norm(d['name']) in new or d['appid'] in knownids:continue
  s={'name':d['name'],'appid':d['appid'],'hub':'Survival','collection':'Fresh survival discoveries','fit':8,'scope':'Survival crafting','aliases':[],'discoverySource':d['discoverySource']};s.update(cfg.get('calendarOverrides',{}).get(d['name'],{}));new[core.norm(s['name'])]=s;knownids.add(d['appid'])
 resolved=[];unresolved=[];tasks=[]
 for s in new.values():
  name=s['name'];key=core.norm(name)
  if name in dispositions:
   ledger.append({'candidate':name,**dispositions[name]})
   if dispositions[name]['state']=='unresolved-active':unresolved.append(pending.get(key,{'candidate':name,'seed':s,**dispositions[name]}))
   continue
  p=pending.get(key)
  # Do not repeat the same unmodified failed title search. Corrected IDs and rate-limited calls are a new route.
  if p and not args.force and name not in cfg['corrections'] and '429' not in p.get('error','') and key not in {core.norm(x[0]) for x in cfg.get('additionalSteam',[])}:
   unresolved.append(p);continue
  if p and not s.get('appid'):
   exact=next((x for x in p.get('matches',[]) if core.norm(x['name'])==key),None)
   if exact:s['appid']=exact['appid']
  tasks.append(s)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for s,g in zip(tasks,pool.map(lambda s:core.resolve(s,prior,args.force),tasks)):
   if g.get('id'):
    g.update(hubs=[s['hub']],collection=s['collection'],collections=[s['collection']],genreScope=s['scope'],fit=s['fit']);resolved.append(g)
   else:unresolved.append(g)
   print('ENRICH',g.get('name',g.get('candidate')),g.get('verification',g.get('state')),flush=True)
 unique={}
 for g in resolved:
  if g['id'] in unique:ledger.append({'candidate':g['seedName'],'state':'duplicate','canonical':g['id']})
  else:unique[g['id']]=g
 data={'schemaVersion':1,'generatedAt':core.NOW,'inputCount':len(new),'items':sorted(unique.values(),key=lambda g:g['name'].casefold()),'unresolved':unresolved,'dispositions':ledger,'coverageNote':cfg['coverageNote']};core.save('survival-steam.json',data);core.save('survival-reconciliation.json',{'generatedAt':core.NOW,'unresolved':unresolved,'dispositions':ledger,'calendarPages':len(index.get('pages',[])),'calendarTerminal':index.get('terminal',False)})
 report={'records':len(data['items']),'hubCounts':{h:sum(h in g['hubs'] for g in data['items']) for h in ['Survival','Minecraft-like worlds']},'unresolved':unresolved,'missingVideo':[{'id':g['id'],'name':g['name']} for g in data['items'] if not g.get('trailers')]};core.save('survival-enrichment-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
