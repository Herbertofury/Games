#!/usr/bin/env python3
"""Incremental, exact-identity RTS collection. A missing store is unresolved, not absent."""
import argparse,concurrent.futures,datetime as dt,functools,hashlib,json,pathlib,re,unicodedata,urllib.parse
import refresh
ROOT=pathlib.Path(__file__).resolve().parents[1]
refresh.details=functools.lru_cache(maxsize=None)(refresh.details)
def norm(s):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().casefold())
def resolve(row,old,force):
    name,collection,fit,*ids=row
    prior=next((g for g in old if norm(g.get('seedName',''))==norm(name)),None)
    if prior and not force and prior.get('verification')=='verified':
        age=dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(prior['verifiedAt'])
        if age.total_seconds()<86400:return prior
    try:
        aid=ids[0] if ids else None
        if not aid:
            url='https://store.steampowered.com/api/storesearch/?'+urllib.parse.urlencode({'term':name,'l':'english','cc':'us'})
            matches=refresh.get(url).get('items',[])
            found=next((g for g in matches if norm(g['name'])==norm(name)),None)
            if not found:raise ValueError('Identity requires explicit reconciliation: '+json.dumps([(g['id'],g['name']) for g in matches[:8]]))
            aid=found['id']
        d=refresh.details(aid)
        if not d or d.get('type')!='game':raise ValueError('Official metadata did not identify a standalone game')
        if not ids and norm(d['name'])!=norm(name):raise ValueError('Name mismatch: '+d['name'])
        # Explicit IDs are curated; preserve both the requested and current official names.
        g=refresh.resolve({'appid':aid,'name':d['name'],'collection':collection,'fit':fit},{},True)
        if g.get('verification')!='verified':raise ValueError(str(g.get('warnings')))
        u=g['steamUrl'];about=refresh.text(d.get('about_the_game',''))
        scope='Traditional base-building RTS'
        if collection=='Modern warfare & tactics':scope='Tactical RTS / limited base building'
        elif collection=='Space & fleet command':scope='Space and fleet RTS'
        elif collection=='Survival & defense RTS':scope='Survival / defense RTS'
        g.update(hubs=['Real-time strategy'],collections=[collection],seedName=name,primaryUrl=u,provider='Steam',kind='Standalone game',genreScope=scope,fit=fit)
        g['tags']=sorted(set(g.get('genres',[])+[collection,'RTS',scope]+(['Co-op'] if any('co-op' in x.lower() for x in g['features']) else [])))
        g['storefronts']=[{'provider':'Steam','url':u,'kind':'store' if not g['comingSoon'] else 'wishlist','verified':True,'lastChecked':refresh.NOW}]
        g['rtsEvidence']={'sourceUrl':u,'about':about,'skirmishMentioned':bool(re.search(r'\bskirmish\b',about,re.I)),'baseBuildingMentioned':bool(re.search(r'base[- ]building|build.{0,30}bases|construct.{0,30}bases',about,re.I))}
        g['demoAppids']=[x['appid'] for x in d.get('demos',[]) if x.get('appid')]
        g['firstSeenAt']=prior.get('firstSeenAt',refresh.NOW) if prior else refresh.NOW
        return g
    except Exception as e:
        if prior:return dict(prior,lastRefreshError=str(e))
        return {'candidate':name,'collection':collection,'fit':fit,'error':str(e),'verification':'unresolved','nextAction':'Resolve exact official identity or non-Steam creator/store edition.'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');a=ap.parse_args()
    cfg=json.loads((ROOT/'data/rts-seeds.json').read_text());target=ROOT/'data/rts-steam.json'
    old=json.loads(target.read_text()).get('items',[]) if target.exists() else []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:results=list(p.map(lambda r:resolve(r,old,a.force),cfg['steam']))
    games=[g for g in results if 'id' in g];pending=[g for g in results if 'id' not in g]
    assert len(games)+len(pending)==len(cfg['steam'])
    assert len({g['id'] for g in games})==len(games),'Resolved identities collide; reconcile before publication'
    data={'schemaVersion':1,'generatedAt':refresh.NOW,'inputCount':len(results),'items':games,'unresolved':pending}
    data['datasetHash']=hashlib.sha256(json.dumps(games,sort_keys=True).encode()).hexdigest()
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'inputs':len(results),'resolved':len(games),'withoutVideo':[g['name'] for g in games if not any(any(t.get(k) for k in ['hls','mp4','webm','youtube']) for t in g.get('trailers',[]))],'unresolved':pending},indent=2))
if __name__=='__main__':main()
