#!/usr/bin/env python3
"""Discover exact official storefronts without claiming an unmatched store is absent.

Public metadata only. No purchases, logins, or paywalled downloads. Existing
links and curation remain authoritative; candidates are retained for review.
"""
import argparse, concurrent.futures, datetime as dt, functools, hashlib, json, pathlib, re, threading, unicodedata, urllib.error, urllib.parse, urllib.request
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
NOW=dt.datetime.now(dt.timezone.utc).isoformat()
UA='Mozilla/5.0 (compatible; GamesLibrary/1.2; +https://github.com/Herbertofury/Games)'
LOCK=threading.Lock(); CACHE={}
PROVIDERS={'gog.com':'GOG','itch.io':'itch.io','store.epicgames.com':'Epic Games','humblebundle.com':'Humble Store','gamejolt.com':'Game Jolt','newgrounds.com':'Newgrounds','moddb.com':'ModDB','indiedb.com':'IndieDB','patreon.com':'Patreon','slipseer.com':'Slipseer'}

def norm(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]','',s)

def provider(url):
    h=urllib.parse.urlsplit(url).hostname or ''
    return next((label for domain,label in PROVIDERS.items() if h==domain or h.endswith('.'+domain)),None)

def safe(url):
    p=urllib.parse.urlsplit(url)
    return p.scheme=='https' and p.hostname and not p.username and not p.password and not re.match(r'^(?:localhost|127\.|10\.|192\.168\.|169\.254\.)',p.hostname)

def read(url):
    if not safe(url):raise ValueError('Not a public HTTPS URL')
    with LOCK:
        if url in CACHE:
            v=CACHE[url]
            if isinstance(v,Exception):raise v
            return v
    try:
        q=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json,text/html;q=0.9'})
        with urllib.request.urlopen(q,timeout=18) as r:
            raw=r.read(6000001)
            if len(raw)>6000000:raise ValueError('Page exceeds public metadata bound')
            if not safe(r.url):raise ValueError('Unsafe redirect')
            result=(raw.decode('utf-8',errors='replace'),r.url,r.headers.get('Content-Type',''))
        with LOCK:CACHE[url]=result
        return result
    except Exception as e:
        with LOCK:CACHE[url]=e
        raise

def api(url):return json.loads(read(url)[0])
def exact(a,b):return norm(a)==norm(b)
def clean(url):
    p=urllib.parse.urlsplit(url)
    qs=[(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith('utm_') and k not in ['ref','referrer','affiliate','aff','snr']]
    return urllib.parse.urlunsplit((p.scheme,p.netloc,p.path,urllib.parse.urlencode(qs),''))
def record(url,label,source,kind='store',evidence=None):
    return {'provider':label,'url':clean(url),'kind':kind,'verified':True,'lastChecked':NOW,'sourceUrl':source,'evidence':evidence or 'Exact title confirmed by official storefront'}

def gog(g,route):
    url=route+urllib.parse.quote(g['name'])
    d=api(url);products=d.get('products',[])
    links=[];candidates=[]
    for p in products:
        title=p.get('title') or p.get('name') or ''
        u=p.get('storeLink') or p.get('url') or p.get('productUrl')
        if u and u.startswith('/'):u='https://www.gog.com'+u
        if not u or provider(u)!='GOG':continue
        if exact(title,g['name']) or any(exact(title,x) for x in [g.get('seedName','')]+g.get('aliases',[])):
            links.append(record(u,'GOG',url,evidence='Exact title in GOG official catalog: '+title))
        elif norm(g['name']) in norm(title):candidates.append({'title':title,'url':u,'provider':'GOG','reason':'Edition or title differs; manual review required'})
    return links,candidates,url

def itch(g):
    url='https://itch.io/search?q='+urllib.parse.quote(g['name']);body,_,_=read(url);s=BeautifulSoup(body,'html.parser')
    links=[];candidates=[]
    for cell in s.select('.game_cell'):
        a=cell.select_one('a.title')
        if not a or not exact(a.get_text(' ',strip=True),g['name']):continue
        u=a.get('href','')
        if not safe(u) or provider(u)!='itch.io':continue
        b,final,_=read(u)
        # A creator listing that links to the exact Steam app is an ownership/edition anchor.
        same=bool(g.get('appid') and re.search(r'store\.steampowered\.com/app/'+str(g['appid'])+r'(?:/|\b)',b))
        low=BeautifulSoup(b,'html.parser').get_text(' ',strip=True).lower()
        demo=bool(re.search(r'\b(?:demo|prototype)\b',a.get_text(' ',strip=True).lower()))
        if same and not demo:links.append(record(final,'itch.io',url,evidence='Exact title and creator page links to Steam app '+str(g['appid'])))
        else:candidates.append({'title':a.get_text(' ',strip=True),'url':final,'provider':'itch.io','reason':'Exact title found; ownership or edition needs manual confirmation'})
    return links,candidates,url

def owned_site(g):
    url=g.get('website')
    if not url or not safe(url):return [],[],None
    host=urllib.parse.urlsplit(url).hostname or ''
    if any(host==h or host.endswith('.'+h) for h in ['twitter.com','x.com','facebook.com','youtube.com','discord.com','t.co','store.steampowered.com']):return [],[],None
    body,final,_=read(url);s=BeautifulSoup(body,'html.parser');links=[];candidates=[]
    for a in s.select('a[href]'):
        u=urllib.parse.urljoin(final,a['href']);label=provider(u)
        if not label or not safe(u):continue
        p=urllib.parse.urlsplit(u)
        if label=='Patreon':
            if p.path.strip('/') and p.path not in ['/login','/signup']:
                links.append(record(u,label,final,'support','Creator support linked from the game website supplied by Steam'))
            continue
        # Do not import unrelated games from a publisher's generic home page.
        if norm(g['name']) not in norm(p.path) and not exact(a.get_text(' ',strip=True),g['name']):continue
        try:
            b,dest,_=read(u);page=BeautifulSoup(b,'html.parser')
            titles=[x.get_text(' ',strip=True) for x in page.select('h1')]
            og=page.find('meta',property='og:title')
            if og:titles.append(og.get('content',''))
            if page.title:titles.append(page.title.get_text(' ',strip=True))
            anchored=any(norm(g['name']) in norm(x) for x in titles)
            if anchored:links.append(record(dest,label,final,'download' if label in ['ModDB','IndieDB','Slipseer'] else 'store','Game-specific official website link with matching destination title'))
            else:candidates.append({'title':a.get_text(' ',strip=True),'url':dest,'provider':label,'reason':'Official link but destination identity not confirmed'})
        except Exception as e:candidates.append({'url':u,'provider':label,'reason':'Destination not readable: '+str(e)})
    return links,candidates,final

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');ap.add_argument('--ids',nargs='*');a=ap.parse_args()
    catalog=json.loads((ROOT/'data/catalog.json').read_text());games=[g for g in catalog['items'] if 'Boomer shooters' in g.get('hubs',[]) and g.get('steamUrl')]
    if a.ids:games=[g for g in games if g['id'] in a.ids]
    target=ROOT/'data/storefront-discovery.json';old=json.loads(target.read_text()) if target.exists() else {'schemaVersion':1,'overrides':{},'coverage':{}}
    routes=['https://catalog.gog.com/v1/catalog?limit=48&productType=in:game,pack&query=','https://www.gog.com/games/ajax/filtered?mediaType=game&search=']
    route=None;probes=[]
    for candidate in routes:
        try:
            probe=api(candidate+'DUSK');probes.append({'provider':'GOG','route':candidate,'keys':list(probe),'count':len(probe.get('products',[]))})
            if probe.get('products'):route=candidate;break
        except Exception as e:probes.append({'provider':'GOG','route':candidate,'error':str(e)})
    itch_ready=True
    try:
        body,_,_=read('https://itch.io/search?q=Zortch');itch_ready=bool(BeautifulSoup(body,'html.parser').select('.game_cell'));probes.append({'provider':'itch.io','searchAvailable':itch_ready})
    except Exception as e:itch_ready=False;probes.append({'provider':'itch.io','error':str(e)})
    def work(g):
        prev=old['coverage'].get(g['id'])
        if not a.force and prev and (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(prev['checkedAt'])).total_seconds()<604800:return g['id'],old['overrides'].get(g['id'],{}),prev
        links=[];candidates=[];checks=[]
        methods=[]
        if route:methods.append(('GOG',lambda:gog(g,route)))
        else:checks.append({'provider':'GOG','state':'provider-unavailable'})
        if itch_ready:methods.append(('itch.io',lambda:itch(g)))
        else:checks.append({'provider':'itch.io','state':'provider-unavailable'})
        methods.append(('Official website',lambda:owned_site(g)))
        for label,fn in methods:
            try:
                found,pending,url=fn();links+=found;candidates+=pending
                checks.append({'provider':label,'state':'matched' if found else 'no-confirmed-match','sourceUrl':url,'matches':len(found)})
            except Exception as e:checks.append({'provider':label,'state':'unresolved','error':str(e)})
        existing=old['overrides'].get(g['id'],{}).get('storefronts',[])
        unique=list({x['url']:x for x in existing+links}.values())
        coverage={'name':g['name'],'checkedAt':NOW,'checks':checks,'candidates':candidates,'scope':'Official GOG catalog, itch.io title search, and game website outbound links. No-result is not proof a store does not carry the game.'}
        print(g['name'],len(unique),'confirmed alternate links;',len(candidates),'review candidates',flush=True)
        return g['id'],{'storefronts':unique,'storeCoverage':coverage},coverage
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for ident,override,coverage in pool.map(work,games):old['overrides'][ident]=override;old['coverage'][ident]=coverage
    old['generatedAt']=NOW;old['probes']=probes;old['scope']='Verified distribution links, not an exhaustive directory of key resellers. Support is not a license.'
    target.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
    report={'checkedAt':NOW,'gamesChecked':len(games),'recordsWithAlternates':sum(bool(x.get('storefronts')) for x in old['overrides'].values()),'confirmedLinks':sum(len(x.get('storefronts',[])) for x in old['overrides'].values()),'pendingCandidates':sum(len(x.get('candidates',[])) for x in old['coverage'].values()),'probes':probes}
    (ROOT/'data/storefront-discovery-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
