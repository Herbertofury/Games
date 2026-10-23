#!/usr/bin/env python3
"""Collect public publisher media with exact project/edition ownership checks."""
import argparse,concurrent.futures,datetime as dt,hashlib,json,pathlib,re,time,urllib.error,urllib.parse,urllib.request
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
NOW=dt.datetime.now(dt.timezone.utc).isoformat()
PARSER_VERSION=2
UA='Mozilla/5.0 (compatible; GamesLibrary/1.1; +https://github.com/Herbertofury/Games)'
ALLOWED=('itch.io','moddb.com','realm667.com','slipseer.com','amelieclanglois.com','gog.com','epicgames.com','newgrounds.com','indiedb.com')
def valid_url(u):
    p=urllib.parse.urlsplit(u)
    return p.scheme=='https' and bool(p.hostname) and not p.username and not p.password

def fetch(url):
    host=urllib.parse.urlsplit(url).hostname or ''
    if not valid_url(url) or not any(host==h or host.endswith('.'+h) for h in ALLOWED):raise ValueError('Unapproved public media host')
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req,timeout=25) as r:
                data=r.read(5_000_001)
                if len(data)>5_000_000:raise ValueError('Oversized metadata page; retain previous snapshot')
                return data.decode('utf-8',errors='replace'),r.url
        except urllib.error.HTTPError as e:
            if attempt or e.code!=429:raise
            wait=e.headers.get('Retry-After','10');time.sleep(min(30,int(wait) if wait.isdigit() else 10))

def owner_key(url):
    m=re.search(r'/images/(mods|downloads)/(\d+/\d+/\d+)/',url or '')
    return '/'.join(m.groups()) if m else None

def full_image(url):
    candidate=re.sub(r'/cache/images/((?:mods|downloads)/\d+/\d+/\d+)/(?:crop|thumb)_[^/]+/',r'/images/\1/',url)
    if candidate==url:return url
    try:
        req=urllib.request.Request(candidate,method='HEAD',headers={'User-Agent':UA})
        with urllib.request.urlopen(req,timeout=12) as r:
            if r.headers.get('Content-Type','').startswith('image/'):return candidate
    except (urllib.error.URLError,TimeoutError):pass
    return url

def parse(page,url):
    soup=BeautifulSoup(page,'html.parser')
    for x in list(soup.select('#comments,.comments,.comment_list,.community_posts,.review_list,.comments_widget,.post_grid')):x.decompose()
    for x in list(soup.find_all(attrs={'class':re.compile(r'^(?:comment|commentrow|commentthread|user-review)(?:\s|$|_)')})):
        if x.parent:x.decompose()
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    og=soup.find('meta',property='og:image') or soup.find('meta',attrs={'name':'twitter:image'})
    image=urllib.parse.urljoin(url,og.get('content','')) if og else None
    if image and not valid_url(image):image=None
    pics=[];owner=owner_key(image) if 'moddb.com/' in url else None
    nodes=soup.select('.screenshot_list a.screenshot_link,.screenshot_list img,.formatted_description img,.game_description img') if '.itch.io/' in url else soup.select('article img,.article img,.body img,.images img,a[href*="/images/"] img')
    for x in nodes:
        src=(x.get('href') if x.name=='a' else x.get('data-src') or x.get('src')) or ''
        src=urllib.parse.urljoin(url,src)
        if not valid_url(src) or any(t in src.lower() for t in ['avatar','button','bannerad','tracking','rating','logo.gif']):continue
        if '.itch.io/' in url and 'img.itch.zone/' not in src:continue
        if 'moddb.com/' in url and (not owner or owner_key(src)!=owner):continue
        if src not in pics and src!=image:pics.append(src)
    videos=[]
    for x in soup.select('iframe[src],iframe[data-src]'):
        src=x.get('src') or x.get('data-src') or ''
        y=re.search(r'(?:youtube(?:-nocookie)?\.com/embed/|youtu\.be/)([A-Za-z0-9_-]{11})',src)
        if y and y[1] not in videos:videos.append(y[1])
    native=None
    if '.itch.io/' in url:
        panel=soup.select_one('.game_info_panel_widget') or soup.select_one('.more_information_toggle')
        info=panel.get_text(' ',strip=True) if panel else ''
        m=re.search(r'Rated\s+([0-9.]+)\s+out of\s+([0-9.]+).*?\(([0-9,]+)\s+total ratings\)',info,re.S)
        if m:native={'provider':'itch.io','value':float(m[1]),'max':float(m[2]),'count':int(m[3].replace(',','')),'checkedAt':NOW,'sourceUrl':url}
    return {'title':title,'image':image,'pictures':pics,'youtube':videos,'nativeRating':native}

def update(g,force=False):
    prior=g.get('mediaCheckedAt')
    if prior and g.get('mediaParserVersion')==PARSER_VERSION and not force and g.get('image') and (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(prior)).total_seconds()<86400:return g
    try:
        url=g.get('mediaPage') or g['primaryUrl'];page,resolved=fetch(url);p=parse(page,resolved)
        if not p['image'] and not p['pictures']:raise ValueError('No publisher artwork parsed; previous media retained')
        g['image']=p['image'] or p['pictures'][0]
        g['screenshots']=[];seen=set()
        for original in p['pictures']:
            src=full_image(original) if 'moddb.com/' in url else original
            if src in seen or src==g['image']:continue
            seen.add(src);g['screenshots'].append({'src':src,'thumbnail':original,'sourceUrl':url,'alt':g['name']+' - creator-published image','credit':'Creator / '+g['provider'],'verified':True,'role':'project-gallery'})
        if p['youtube']:g['trailers']=[{'name':'Creator-published video','youtube':v,'sourceUrl':url,'watchUrl':'https://www.youtube.com/watch?v='+v,'poster':g['image']} for v in p['youtube']]
        if p['nativeRating']:g['externalRating']=p['nativeRating']
        g['mediaParserVersion']=PARSER_VERSION;g['mediaCheckedAt']=NOW;g['mediaPageHash']=hashlib.sha256(page.encode()).hexdigest();g.pop('mediaRefreshError',None)
        g['sources']=list({s['url']:s for s in g['sources']+[{'provider':'Official media','url':url,'verified':True,'lastChecked':NOW}]}.values())
        print('MEDIA',g['name'],len(g['screenshots']),'images',len(g['trailers']),'videos',flush=True)
    except Exception as e:
        # Reject previously collected unrelated assets even if the provider is offline.
        if 'moddb.com/' in (g.get('mediaPage') or g['primaryUrl']):
            owner=owner_key(g.get('image'));g['screenshots']=[s for s in g.get('screenshots',[]) if owner and owner_key(s['src'])==owner]
        g['mediaRefreshError']=str(e);print('MEDIA RETAINED',g['name'],str(e),flush=True)
    return g

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');args=ap.parse_args()
    path=ROOT/'data/shooters-external.json';d=json.loads(path.read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:d['items']=list(pool.map(lambda g:update(g,args.force),d['items']))
    d['mediaRefreshedAt']=NOW;path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    report={'checkedAt':NOW,'parserVersion':PARSER_VERSION,'records':len(d['items']),'withArtwork':sum(bool(g.get('image')) for g in d['items']),'withTrailers':sum(bool(g.get('trailers')) for g in d['items']),'failures':[{'id':g['id'],'url':g.get('mediaPage',g['primaryUrl']),'error':g['mediaRefreshError']} for g in d['items'] if g.get('mediaRefreshError')]}
    (ROOT/'data/external-media-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
