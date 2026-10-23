#!/usr/bin/env python3
"""Incremental genre discovery using official Steam facts. Never modifies the base catalog."""
import concurrent.futures,datetime as dt,difflib,hashlib,json,pathlib,re,urllib.parse
import refresh
ROOT=pathlib.Path(__file__).resolve().parents[1]
def n(s):return re.sub('[^a-z0-9]','',s.casefold())
def collect(row,old,base):
    name,collection,fit,*ids=row
    prior=next((g for g in old if n(g.get('seedName',''))==n(name) or n(g['name'])==n(name)),None)
    if prior and prior.get('verification')=='verified':
        age=dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(prior['verifiedAt'])
        if age.total_seconds()<86400:return prior
    try:
        aid=ids[0] if ids else None
        if not aid:
            found=next((g for g in base if n(g['name'])==n(name)),None)
            if found:aid=found['appid']
        if not aid:
            q=refresh.get('https://store.steampowered.com/api/storesearch/?'+urllib.parse.urlencode({'term':name,'l':'english','cc':'us'})).get('items',[])
            found=next((g for g in q if n(g['name'])==n(name)),None)
            if not found:
                ranked=sorted(q,key=lambda g:difflib.SequenceMatcher(None,n(name),n(g['name'])).ratio(),reverse=True)
                if ranked and difflib.SequenceMatcher(None,n(name),n(ranked[0]['name'])).ratio()>=0.91:found=ranked[0]
            if not found:raise ValueError('Exact identity needs manual review: '+str([(g['id'],g['name']) for g in q[:5]]))
            aid=found['id']
        existing=next((g for g in base if g.get('appid')==aid and g.get('verification')=='verified'),None)
        g=dict(existing) if existing else refresh.resolve({'appid':aid,'name':name,'collection':collection,'fit':fit},{},True)
        if g['verification']!='verified':raise ValueError('; '.join(g.get('warnings',[])))
        g.update(hubs=['Boomer shooters'],collection=collection,fit=fit,seedName=name,primaryUrl=g['steamUrl'],provider='Steam',kind='Standalone game',genreScope='Adjacent FPS' if collection in ['Immersive & tactical FPS','Arena & roguelite FPS'] else 'Core retro / movement FPS')
        g['storefronts']=[{'provider':'Steam','url':g['steamUrl'],'kind':'store','verified':True,'lastChecked':refresh.NOW}]
        g['tags']=sorted(set(g['tags']+['FPS',collection]))
        return g
    except Exception as e:
        if prior:return dict(prior,lastRefreshError=str(e))
        return {'candidate':name,'collection':collection,'error':str(e),'verification':'unresolved'}
def main():
    cfg=json.loads((ROOT/'data/shooters-seeds.json').read_text())
    target=ROOT/'data/shooters-steam.json'
    old=json.loads(target.read_text()).get('items',[]) if target.exists() else []
    base=json.loads((ROOT/'data/catalog.json').read_text())['items']
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for g in pool.map(lambda r:collect(r,old,base),cfg['steam']):
            results.append(g);print(g.get('name',g.get('candidate')),g['verification'],g.get('status',g.get('error','')),flush=True)
    games=[g for g in results if 'id' in g];pending=[g for g in results if 'id' not in g]
    assert len(games)+len(pending)==len(cfg['steam'])
    assert len({g['id'] for g in games})==len(games),'Duplicate resolved identities need reconciliation'
    data={'schemaVersion':1,'generatedAt':refresh.NOW,'inputCount':len(cfg['steam']),'items':games,'unresolved':pending}
    data['datasetHash']=hashlib.sha256(json.dumps(games,sort_keys=True).encode()).hexdigest()
    target.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'inputs':len(results),'resolved':len(games),'unresolved':pending},indent=2))
if __name__=='__main__':main()
