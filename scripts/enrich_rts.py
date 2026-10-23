#!/usr/bin/env python3
"""Incremental RTS enrichment. Source failures stay explicit, never guessed."""
import concurrent.futures,datetime as dt,hashlib,html,json,pathlib,re,urllib.parse
from bs4 import BeautifulSoup
import collect_rts,collect_external_media as media,discover_storefronts as stores
from source_links import normalized_links
ROOT=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
EXTRA=('beyondallreason.info','openra.net','openhv.net','play0ad.com','blizzard.com','battle.net','littlewargame.com','patreon.com','faforever.com','eugensystems.com')
media.ALLOWED=tuple(set(media.ALLOWED+EXTRA));media.NOW=NOW

def src(url,label,kind='project',evidence=None):return {'url':url,'provider':label,'kind':kind,'verified':True,'lastChecked':NOW,**({'evidence':evidence} if evidence else {})}
def label(url):
    host=urllib.parse.urlsplit(url).hostname or ''
    if 'battle.net' in host or 'blizzard.com' in host:return 'Battle.net'
    if 'gog.com' in host:return 'GOG'
    return stores.provider(url) or 'Official site'
def parse_rich(raw,url):
    p=media.parse(raw,url);s=BeautifulSoup(raw,'html.parser')
    for x in list(s.select('#comments,.comments,.comment_list,.community_posts,.post_grid,footer,nav')):x.decompose()
    body=html.unescape(str(s).replace('\\/','/'))
    vids=re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})',body)
    p['youtube']=list(dict.fromkeys(p['youtube']+vids))
    if 'moddb.com' not in url and '.itch.io' not in url:
        for a in s.select('video,video source'):
            u=urllib.parse.urljoin(url,a.get('src',''));typ=a.get('type','')
            if a.get('src') and media.valid_url(u) and re.search(r'\.(?:mp4|webm|m3u8)(?:\?|$)',u):p.setdefault('files',[]).append(u)
        for node in s.select('img[src],img[data-src]'):
            u=urllib.parse.urljoin(url,node.get('data-src') or node.get('src',''))
            if media.valid_url(u) and not any(x in u.lower() for x in ['icon','logo','avatar','flag','badge','payment','rating','button']):
                if u not in p['pictures'] and u!=p.get('image'):p['pictures'].append(u)
    p['outbound']=[]
    for a in s.select('a[href]'):
        u=urllib.parse.urljoin(url,a['href']);h=urllib.parse.urlsplit(u).hostname or ''
        if not media.valid_url(u):continue
        if any(h==v or h.endswith('.'+v) for v in ['itch.io','moddb.com','indiedb.com','patreon.com','store.steampowered.com','store.epicgames.com','gog.com','shop.battle.net']):
            p['outbound'].append({'url':u,'text':a.get_text(' ',strip=True)})
    # Keep exact scraped source metadata for review, not the entire page in the client.
    p['description']=next((n.get('content') for n in s.select('meta[property="og:description"],meta[name="description"]') if n.get('content')),None)
    if 'gog.com' in url:
        for n in s.select('script[type="application/ld+json"]'):
            try:
                data=json.loads(n.string or n.get_text());data=data if isinstance(data,list) else [data]
                for d in data:
                    if isinstance(d,dict) and 'aggregateRating' in d:
                        r=d['aggregateRating'];p['nativeRating']={'provider':'GOG','value':float(r['ratingValue']),'max':float(r.get('bestRating',5)),'count':int(r.get('ratingCount',r.get('reviewCount',0))),'checkedAt':NOW,'sourceUrl':url}
            except (ValueError,TypeError,KeyError):pass
    return p

def external(seed,old):
    ident='external:'+seed['slug'];prior=old.get(ident)
    if prior and prior.get('mediaCheckedAt') and prior.get('image') and prior.get('trailers'):return prior
    url=seed['url'];provider=label(url);kind=seed.get('kind','Standalone game')
    g=dict(prior or {});g.update(id=ident,name=seed['name'],provider=provider,primaryUrl=url,collection=seed['collection'],collections=[seed['collection']],hubs=['Real-time strategy'],fit=seed['fit'],summary=seed['why'],curatorWhy=seed['why'],requirements=seed['requirements'],kind=kind,status=seed.get('status','Released'),comingSoon=False,free=seed['free'],reviewCount=0,rating=None,genres=['Strategy'],tags=['RTS',seed['collection'],'Base building'] if seed['slug']!='world-in-conflict' else ['RTS','Tactical RTS / no base building'],platforms=[],features=[],confidence='Established',releaseYear=seed.get('releaseYear'),releaseDate=None,releaseLabel=str(seed.get('releaseYear') or 'Community release; see project'),genreScope='Tactical RTS / limited base building' if seed['slug']=='world-in-conflict' else 'Traditional base-building RTS')
    g.setdefault('storefronts',[]);g.setdefault('sources',[]);g.setdefault('screenshots',[]);g.setdefault('trailers',[])
    errors=[];evidence=[]
    for pageurl in [url]+seed.get('extraUrls',[]):
        try:
            raw,final=media.fetch(pageurl);p=parse_rich(raw,final);evidence.append({'url':final,'title':p['title'],'youtube':p['youtube'],'files':p.get('files',[]),'outbound':p['outbound'],'description':p.get('description'),'image':p.get('image'),'pictureCount':len(p['pictures']),'hash':hashlib.sha256(raw.encode()).hexdigest()})
            if pageurl==url:g.update(verification='verified',verifiedAt=NOW)
            if p.get('image') and not g.get('image'):g['image']=p['image']
            if not g.get('image') and p['pictures']:g['image']=p['pictures'][0]
            for pic in p['pictures']:
                if pic!=g.get('image'):g['screenshots'].append({'src':pic,'thumbnail':pic,'sourceUrl':final,'alt':g['name']+' creator artwork','credit':'Creator / '+label(final),'verified':True})
            for v in p['youtube']:g['trailers'].append({'youtube':v,'name':'Video published on '+label(final),'sourceUrl':final,'watchUrl':'https://www.youtube.com/watch?v='+v,'poster':g.get('image')})
            for u in p.get('files',[]):g['trailers'].append({'name':'Official site video','sourceUrl':final,'poster':g.get('image'),('hls' if '.m3u8' in u else 'webm' if '.webm' in u else 'mp4'):u})
            if p.get('nativeRating'):g['externalRating']=p['nativeRating']
            g['sources'].append(src(final,label(final)))
            # Only explicit seed URLs are published now. Outbound discoveries await exact-edition review.
            g['storefronts'].append(src(final,label(final),'support' if 'patreon.com' in final else 'store' if label(final) in ['GOG','Battle.net'] else 'browser' if seed['slug']=='littlewargame' else 'project'))
        except Exception as e:errors.append({'url':pageurl,'error':str(e)})
    g['screenshots']=list({x['src']:x for x in g['screenshots']}.values());g['trailers']=list({x.get('youtube') or x.get('hls') or x.get('mp4') or x.get('webm'):x for x in g['trailers']}.values());g['sources']=list({x['url']:x for x in g['sources']}.values());g['storefronts']=list({x['url']:x for x in g['storefronts']}.values())
    g['mediaCheckedAt']=NOW;g['mediaEvidence']=evidence;g['mediaErrors']=errors;g.setdefault('verification','unresolved')
    print('EXTERNAL',g['name'],g['verification'],bool(g.get('image')),len(g['trailers']),flush=True)
    return g

def alternate(g,old,route):
    if g['id'] in old:return g['id'],old[g['id']]
    links=[];checks=[];candidates=[]
    for provider,fn in [('GOG',lambda:stores.gog(g,route)),('itch.io',lambda:stores.itch(g)),('Official website',lambda:stores.owned_site(g))]:
        try:
            found,pending,u=fn();links+=found;candidates+=pending;checks.append({'provider':provider,'sourceUrl':u,'state':'matched' if found else 'no-confirmed-match','matches':len(found)})
        except Exception as e:checks.append({'provider':provider,'state':'unresolved','error':str(e)})
    links=normalized_links(links)
    # Store description evidence catches the common exact-title-but-demo issue.
    for l in links:
        if l['provider']=='itch.io':
            try:
                body,_,_=stores.read(l['url']);s=BeautifulSoup(body,'html.parser');area=s.select_one('.formatted_description') or s
                info=area.get_text(' ',strip=True)
                if re.search(r'\b(?:demo version|free demo|play the demo|download.{0,20}demo|this demo)\b',info,re.I):l.update(kind='demo',editionNote='Creator page describes a demo; full-game purchase is a separate link.')
                l['descriptionEvidence']=info[:5000]
            except Exception as e:l['editionCheckError']=str(e)
    return g['id'],{'storefronts':links,'storeCoverage':{'checkedAt':NOW,'checks':checks,'candidates':candidates,'scope':'Exact official GOG, itch.io, and game-site destinations; no-match does not prove absence.'}}

def main():
    config=json.loads((ROOT/'data/rts-expansion.json').read_text());seeds=json.loads((ROOT/'data/rts-seeds.json').read_text())
    target=ROOT/'data/rts-steam.json';data=json.loads(target.read_text());old=data['items'];rows=[];ledger=[]
    for row in seeds['steam']:
        if row[0] in config['dispositions']:ledger.append({'candidate':row[0],**config['dispositions'][row[0]]});continue
        rows.append(row[:3]+[config['steamIds'][row[0]]] if row[0] in config['steamIds'] else row)
    rows+=config['additionalSteam']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:results=list(p.map(lambda r:collect_rts.resolve(r,old,False),rows))
    data.update(items=[g for g in results if g.get('id')],unresolved=[g for g in results if not g.get('id')],dispositions=ledger,generatedAt=NOW)
    assert len({g['id'] for g in data['items']})==len(data['items'])
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    path=ROOT/'data/rts-external.json';prev={g['id']:g for g in json.loads(path.read_text())['items']} if path.exists() else {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:items=list(p.map(lambda s:external(s,prev),config['external']))
    path.write_text(json.dumps({'generatedAt':NOW,'items':items},ensure_ascii=False,indent=2)+'\n')
    path=ROOT/'data/rts-storefronts.json';prev=json.loads(path.read_text()).get('overrides',{}) if path.exists() else {};route='https://catalog.gog.com/v1/catalog?limit=48&productType=in:game,pack&query='
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:
        for ident,x in p.map(lambda g:alternate(g,prev,route),data['items']):prev[ident]=x
    path.write_text(json.dumps({'generatedAt':NOW,'overrides':prev},ensure_ascii=False,indent=2)+'\n')
    allgames=data['items']+items
    report={'checkedAt':NOW,'steam':len(data['items']),'external':len(items),'missingArtwork':[{'id':g['id'],'name':g['name']} for g in allgames if not g.get('image')],'missingVideo':[{'id':g['id'],'name':g['name']} for g in allgames if not g.get('trailers')],'unresolved':data['unresolved'],'dispositions':ledger,'alternateLinks':sum(len(v.get('storefronts',[])) for v in prev.values())}
    (ROOT/'data/rts-enrichment-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
