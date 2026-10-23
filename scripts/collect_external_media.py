#!/usr/bin/env python3
"""Read public creator-page media, preserving prior data on provider failures.

No paid posts, credentials, arbitrary game downloads, or user comments are read.
Media and native-platform review snapshots are separate from editorial verification.
"""
import argparse, concurrent.futures, datetime as dt, hashlib, json, pathlib, re, time, urllib.error, urllib.parse, urllib.request
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
NOW=dt.datetime.now(dt.timezone.utc).isoformat()
UA='Mozilla/5.0 (compatible; GamesLibrary/1.1; +https://github.com/Herbertofury/Games)'
ALLOWED=('itch.io','moddb.com','realm667.com','slipseer.com','amelieclanglois.com','gog.com','epicgames.com','newgrounds.com','indiedb.com')
def valid_url(u):
    p=urllib.parse.urlsplit(u)
    return p.scheme=='https' and bool(p.hostname) and not p.username and not p.password

def fetch(url):
    host=urllib.parse.urlsplit(url).hostname or ''
    if not valid_url(url) or not any(host==h or host.endswith('.'+h) for h in ALLOWED):raise ValueError('Unapproved public media host')
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            data=r.read(5_000_001)
            if len(data)>5_000_000:raise ValueError('Oversized metadata page; retain previous snapshot')
            return data.decode('utf-8',errors='replace'),r.url
    except urllib.error.HTTPError as e:
        if e.code==429:
            wait=e.headers.get('Retry-After','10')
            time.sleep(min(30,int(wait) if wait.isdigit() else 10))
            with urllib.request.urlopen(req,timeout=25) as r:return r.read(5_000_000).decode('utf-8',errors='replace'),r.url
        raise

def parse(page,url):
    soup=BeautifulSoup(page,'html.parser')
    # Embedded comment/review media is user-generated, not publisher media.
    for x in list(soup.select('.comments,.comment_list,.community_posts,.review_list,.comments_widget,.post_grid')):
        x.decompose()
    for x in list(soup.find_all(attrs={'class':re.compile(r'^(?:comment|commentrow|commentthread|user-review)(?:\s|$|_)')})):
        if x.parent:x.decompose()
    title=(soup.title.get_text(' ',strip=True) if soup.title else '')
    og=soup.find('meta',property='og:image') or soup.find('meta',attrs={'name':'twitter:image'})
    image=urllib.parse.urljoin(url,og.get('content','')) if og else None
    if image and not valid_url(image):image=None
    pics=[]
    if '.itch.io/' in url:
        nodes=soup.select('.screenshot_list a.screenshot_link,.screenshot_list img,.formatted_description img,.game_description img')
    else:
        nodes=soup.select('article img,.article img,.body img,.images img,a[href*="/images/"] img')
    for x in nodes:
        src=(x.get('href') if x.name=='a' else x.get('data-src') or x.get('src')) or ''
        src=urllib.parse.urljoin(url,src)
        if not valid_url(src) or any(t in src.lower() for t in ['avatar','button','bannerad','tracking','rating','logo.gif']):continue
        if '.itch.io/' in url and 'img.itch.zone/' not in src:continue
        if 'moddb.com/' in url and not ('media.moddb.com/' in src and any(z in src for z in ['/images/','/cache/images/'])):continue
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
    if prior and not force and g.get('image') and (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(prior)).total_seconds()<86400:return g
    try:
        url=g.get('mediaPage') or g['primaryUrl']
        page,resolved=fetch(url);p=parse(page,resolved)
        if not p['image'] and not p['pictures']:raise ValueError('No publisher artwork parsed; previous media retained')
        g['image']=p['image'] or p['pictures'][0]
        if p['pictures']:
            g['screenshots']=[{'src':s,'thumbnail':s,'sourceUrl':url,'alt':g['name']+' - creator-published image','credit':'Creator / '+g['provider'],'verified':True,'role':'project-gallery'} for s in p['pictures']]
        if p['youtube']:
            g['trailers']=[{'name':'Creator-published video','youtube':v,'sourceUrl':url,'watchUrl':'https://www.youtube.com/watch?v='+v,'poster':g['image']} for v in p['youtube']]
        if p['nativeRating']:g['externalRating']=p['nativeRating']
        g['mediaCheckedAt']=NOW;g['mediaPageHash']=hashlib.sha256(page.encode()).hexdigest();g.pop('mediaRefreshError',None)
        g['sources']=list({s['url']:s for s in g['sources']+[{'provider':'Official media','url':url,'verified':True,'lastChecked':NOW}]}.values())
        print('MEDIA',g['name'],len(g['screenshots']),'images',len(g['trailers']),'videos',flush=True)
    except Exception as e:
        g['mediaRefreshError']=str(e);print('MEDIA RETAINED',g['name'],str(e),flush=True)
    return g

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');args=ap.parse_args()
    path=ROOT/'data/shooters-external.json';d=json.loads(path.read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:d['items']=list(pool.map(lambda g:update(g,args.force),d['items']))
    d['mediaRefreshedAt']=NOW
    path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    report={'checkedAt':NOW,'records':len(d['items']),'withArtwork':sum(bool(g.get('image')) for g in d['items']),'withTrailers':sum(bool(g.get('trailers')) for g in d['items']),'failures':[{'id':g['id'],'url':g.get('mediaPage',g['primaryUrl']),'error':g['mediaRefreshError']} for g in d['items'] if g.get('mediaRefreshError')]}
    (ROOT/'data/external-media-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
