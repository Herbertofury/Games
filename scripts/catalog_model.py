"""Merge genre sources without replacing original identities or user-facing provenance."""
import copy,csv,hashlib,json,pathlib,urllib.parse
from source_links import normalized_links
from platformer_model import merge_platformers,complete_platformer_metadata
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(path,default):
    p=ROOT/path
    return json.loads(p.read_text()) if p.exists() else default

def score(g):
    if g.get('verification')!='verified' or g.get('fit') is None or g.get('comingSoon'):return None
    n=int(g['fit']);r=g.get('rating');count=g.get('reviewCount',0)
    if not g.get('steamUrl'):
        return min(n,7) if g.get('confidence')=='Exploratory' else n
    if count<30:n=min(n,7)
    if r is not None and count>=30:
        if r<50:n=min(n,5)
        elif r<70:n=min(n,6)
        elif r<80:n=min(n,7)
    return n

def game_key(g):
    import re
    ident=str(g['appid']) if g.get('appid') else g['id'].replace(':','-')
    return 'Game-'+ident+'-'+re.sub('[^A-Za-z0-9]+','-',g['name']).strip('-')

def primary(g):return g.get('primaryUrl') or g.get('steamUrl')
def validate(g):
    assert g.get('id') and g.get('name') and primary(g), 'Missing identity or project home'
    u=urllib.parse.urlsplit(primary(g));assert u.scheme=='https' and u.netloc,'Unsafe project URL'
    if g.get('steamUrl'):
        assert g.get('appid') and g['steamUrl']==f"https://store.steampowered.com/app/{g['appid']}/",'Steam identity mismatch'
    else:assert g['id'].startswith('external:'),'External games need stable provider-independent IDs'
    for s in g.get('storefronts',[]):
        u=urllib.parse.urlsplit(s['url']);assert u.scheme=='https' and u.netloc,'Unsafe storefront'
    assert g.get('fit') is None or 1<=g['fit']<=10
    assert g.get('rating') is None or 0<=g['rating']<=100

def assemble(catalog):
    baseids={r['appid'] for r in csv.DictReader((ROOT/'data/seeds.tsv').read_text().splitlines(),delimiter='\t')}
    games={g['id']:copy.deepcopy(g) for g in catalog['items']}
    for g in games.values():
        if str(g.get('seedId')) in baseids or str(g.get('appid')) in baseids:
            g['hubs']=list(dict.fromkeys(['Roguelites']+g.get('hubs',[])))
        g.setdefault('primaryUrl',g.get('steamUrl'))
        g.setdefault('provider','Steam' if g.get('steamUrl') else 'Official site')
        g.setdefault('kind','Standalone game')
        g.setdefault('collections',[g['collection']])
        g.setdefault('storefronts',[{'provider':'Steam','url':g['steamUrl'],'kind':'store','verified':g.get('verification')=='verified','lastChecked':g.get('verifiedAt')}] if g.get('steamUrl') else [])
    shooters=load('data/shooters-steam.json',{'items':[],'unresolved':[]})
    external=load('data/shooters-external.json',{'items':[]})
    rts=load('data/rts-steam.json',{'items':[],'unresolved':[]})
    rts_external=load('data/rts-external.json',{'items':[]})
    for source,hub in [(shooters,'Boomer shooters'),(external,'Boomer shooters'),(rts,'Real-time strategy'),(rts_external,'Real-time strategy')]:
        for item in source['items']:
            g=copy.deepcopy(item);g.setdefault('hubs',[hub]);g.setdefault('collections',[g['collection']])
            if g['id'] in games:
                old=games[g['id']]
                if 'Roguelites' in old.get('hubs',[]):
                    old['hubs']=list(dict.fromkeys(old['hubs']+g['hubs']))
                    old['collections']=list(dict.fromkeys(old['collections']+g['collections']))
                    old['tags']=sorted(set(old.get('tags',[])+g.get('tags',[])))
                    continue
            games[g['id']]=g
    for overlay in ['data/shooters-curation.json','data/storefront-discovery.json','data/media-completion.json','data/rts-storefronts.json','data/rts-curation.json','data/rts-media-completion.json']:
        overrides=load(overlay,{'overrides':{}})
        for ident,extra in overrides.get('overrides',{}).items():
            if ident not in games:continue
            g=games[ident]
            replacements=extra.get('_replace',{})
            assert set(replacements)<=set(['image','background','screenshots','trailers','storefronts','sources','primaryUrl','website']), 'Unapproved replacement field'
            for field,value in replacements.items():g[field]=copy.deepcopy(value)
            for k,v in extra.items():
                if k=='_replace':continue
                if k in ['storefronts','sources']:
                    if k=='storefronts' and overlay in ['data/storefront-discovery.json','data/rts-storefronts.json']:v=normalized_links(v)
                    def link_key(x):
                        u=urllib.parse.urlsplit(x['url'])
                        return ((u.hostname or '').removeprefix('www.'),u.path.rstrip('/'),u.query)
                    g[k]=list({link_key(x):x for x in g.get(k,[])+v}.values())
                elif k=='trailers':
                    def media_key(x):return x.get('youtube') or x.get('mp4') or x.get('webm') or x.get('hls') or x.get('sourceUrl')
                    g[k]=list({media_key(x):x for x in g.get(k,[])+v}.values())
                elif k=='tags':g[k]=sorted(set(g.get(k,[])+v))
                else:g[k]=v
    games=merge_platformers(games,ROOT)
    from metroidvania_model import integrate
    mv=integrate(ROOT,games)
    from survival_model import integrate as integrate_survival
    survival=integrate_survival(ROOT,games)
    from party_model import integrate as integrate_party
    party=integrate_party(ROOT,games)
    out=sorted(games.values(),key=lambda g:g['name'].casefold())
    for g in out:
        g.setdefault("appid",None)
        if g.get("verification")!="verified":g["fit"]=None
        validate(g)
    assert len({g['id'] for g in out})==len(out),'Duplicate game identities'
    assert len([g for g in out if 'Roguelites' in g.get('hubs',[])])>=len(baseids),'Original recommendations lost'
    c=copy.deepcopy(catalog);c['items']=out
    dates=[x for x in [c.get('generatedAt'),shooters.get('generatedAt'),external.get('generatedAt'),rts.get('generatedAt'),rts_external.get('generatedAt'),load('data/rts-curation.json',{}).get('generatedAt'),load('data/rts-media-completion.json',{}).get('generatedAt'),load('data/media-completion.json',{}).get('generatedAt'),load('data/storefront-discovery.json',{}).get('generatedAt')] if x]
    if mv.get('generatedAt'):dates.append(mv['generatedAt'])
    if survival.get('generatedAt'):dates.append(survival['generatedAt'])
    if party.get('generatedAt'):dates.append(party['generatedAt'])
    c['generatedAt']=max(dates) if dates else None
    c['sources']=[{'provider':'Steam','kind':'canonical-facts','description':'Official metadata and all-language review totals.'},{'provider':'Creator and community hosts','kind':'curated-facts','description':'Exact creator pages, download records, and dated developer updates. Support links are not licenses.'}]
    b=c.setdefault('build',{});b.update(generator='games-catalog/1.3.0',inputCount=len(out),verifiedCount=sum(g.get('verification')=='verified' for g in out),unresolvedCount=sum(g.get('verification')!='verified' for g in out),candidateUnresolved=shooters.get('unresolved',[])+rts.get('unresolved',[]),candidateDispositions=rts.get('dispositions',[]),mediaCount=sum(bool(g.get('image'))+len(g.get('screenshots',[]))+len(g.get('trailers',[])) for g in out))
    b['generator']='games-catalog/1.4.0'
    b['candidateUnresolved']+=mv['unresolved']
    b['candidateDispositions']+=mv['dispositions']
    b['metroidvaniaCount']=len(mv['ids'])
    b['generator']='games-catalog/1.5.0'
    b['candidateUnresolved']+=survival['unresolved']
    b['candidateDispositions']+=survival['dispositions']
    b['survivalStudyCount']=len(survival['ids'])
    b['partyStudyCount']=len(party['ids'])
    b['generator']='games-catalog/1.6.0'
    b['candidateUnresolved']+=party['unresolved']
    b['candidateDispositions']+=party['dispositions']
    b['hubCounts']={hub:sum(hub in g.get('hubs',[]) for g in out) for hub in sorted({h for g in out for h in g.get('hubs',[])})}
    b['datasetHash']=hashlib.sha256(json.dumps(out,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return complete_platformer_metadata(c,ROOT)
