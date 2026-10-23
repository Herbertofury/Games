#!/usr/bin/env python3
"""Build reviewed non-Steam platformers; scrape only exact-page metadata.

Identity, editions and platform requirements are manually researched. A page
request can enrich media, not invent availability, release dates or reviews.
Missing media is explicit and never replaced with a different franchise image.
"""
from __future__ import annotations
import concurrent.futures, datetime as dt, hashlib, json, pathlib, re, unicodedata, urllib.parse, urllib.request
from bs4 import BeautifulSoup
ROOT = pathlib.Path(__file__).resolve().parents[1]
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
ALLOWED = {'www.nintendo.com', 'www.playstation.com', 'maddymakesgamesinc.itch.io', 'www.supertux.org'}

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s.casefold()) if c.isascii() and c.isalnum())

def exact_media(g):
    url = g['primaryUrl']
    assert urllib.parse.urlsplit(url).hostname in ALLOWED
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; GamesLibrary/1.0; exact source media audit)'})
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(5_000_001)
            assert len(raw) <= 5_000_000, 'Oversized source page'
            assert urllib.parse.urlsplit(response.url).hostname in ALLOWED, 'Unexpected redirect host'
        soup = BeautifulSoup(raw, 'html.parser')
        title = soup.title.get_text(' ', strip=True) if soup.title else ''
        assert not any(x in title.lower() for x in ['access denied', 'just a moment', 'page not found']), 'Source page blocked'
        tokens = [t for t in re.findall('[a-z0-9]+', g['name'].lower()) if len(t)>3 and t not in ['edition','nintendo','switch','classic','fragments']]
        assert any(norm(t) in norm(title) for t in tokens), 'Page title did not identify the reviewed game'
        tag = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name':'twitter:image'})
        image = urllib.parse.urljoin(url, tag.get('content','')) if tag else None
        if image and urllib.parse.urlsplit(image).scheme == 'https':
            g['image'] = image
            g['sources'].append({'provider':'Exact-page Open Graph artwork', 'url':url, 'verified':True, 'lastChecked':NOW})
        # Creator-page galleries and their directly embedded videos can be
        # attributed safely. Console recommendation carousels are not scraped.
        if '.itch.io/' in url:
            for panel in soup.select('.comments_widget,.comments,.community_posts'): panel.decompose()
            pics=[]
            for a in soup.select('.screenshot_list a.screenshot_link'):
                src=urllib.parse.urljoin(url,a.get('href',''))
                if urllib.parse.urlsplit(src).hostname=='img.itch.zone' and src not in pics:pics.append(src)
            g['screenshots']=[{'src':s,'thumbnail':s,'sourceUrl':url,'alt':g['name']+' creator screenshot','credit':'Creator / itch.io','verified':True} for s in pics]
            videos=[]
            for iframe in soup.select('.video_embed iframe,.formatted_description iframe,.game_description iframe'):
                match=re.search(r'youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]{11})',iframe.get('src',''))
                if match and match[1] not in videos:videos.append(match[1])
            g['trailers']=[{'name':'Creator-published video','youtube':v,'sourceUrl':url,'watchUrl':'https://www.youtube.com/watch?v='+v,'poster':g.get('image')} for v in videos]
            info=soup.select_one('.game_info_panel_widget')
            match=re.search(r'Rated\s+([0-9.]+)\s+out of\s+([0-9.]+).*?\(([0-9,]+)\s+total ratings\)',info.get_text(' ',strip=True) if info else '',re.S)
            if match:g['externalRating']={'provider':'itch.io','value':float(match[1]),'max':float(match[2]),'count':int(match[3].replace(',','')),'sourceUrl':url,'checkedAt':NOW}
        g['mediaCheckedAt']=NOW
        g['mediaPageHash']=hashlib.sha256(raw).hexdigest()
        g.pop('mediaRefreshError',None)
    except Exception as exc:
        g['mediaRefreshError']=str(exc)
    if not g.get('image'):g['warnings'].append('Exact artwork not collected; the official project page remains available.')
    if not g.get('trailers'):g['warnings'].append('No independently parsed embedded trailer; use the official page for video.')
    print('EXTERNAL',g['name'],'image='+str(bool(g.get('image'))),g.get('mediaRefreshError',''),flush=True)
    return g

def main():
    source=json.loads((ROOT/'data/platformers-external-seeds.json').read_text())
    target=ROOT/'data/platformers-external.json'
    old={g['id']:g for g in json.loads(target.read_text())['items']} if target.exists() else {}
    items=[]
    for raw in source['records']:
        row=dict(zip(source['fields'],raw));ident='external:'+row['key'];date=row['releaseDate']
        store_kind='browser' if 'Browser' in row['platforms'] else 'download' if row['free'] and row['provider']!='PlayStation' else 'project' if row['free'] else 'store'
        g={'id':ident,'appid':None,'seedId':ident,'seedName':row['name'],'name':row['name'],'collection':row['collection'],'collections':[row['collection']],'hubs':['Platformers'],'fit':row['fit'],'editorialFit':row['fit'],'summary':row['why'],'curatorWhy':row['why'],'recommendationCaution':row['caution'],'requirements':row['caution'],'developers':[],'publishers':[row['provider']] if row['provider'] in ['Nintendo','PlayStation'] else [],'genres':['Platformer'],'tags':['Platformer',row['collection']]+(['Free creator release'] if row['collection']=='Free creator releases' else ['Console source']),'features':[],'platforms':row['platforms'],'status':'Released','comingSoon':False,'free':row['free'],'releaseDate':date,'releaseLabel':date or 'Original date not independently recorded','rating':None,'reviewCount':0,'reviewLabel':None,'image':None,'screenshots':[],'trailers':[],'primaryUrl':row['url'],'steamUrl':None,'website':row['url'],'provider':row['provider'],'kind':'Standalone game','genreScope':'Free creator platformer' if row['collection']=='Free creator releases' else 'Console platformer / exact edition','confidence':'Source-grounded editorial selection','verification':'verified','verifiedAt':source['reviewedAt']+'T00:00:00+00:00','researchCheckedAt':source['reviewedAt'],'storefronts':[{'provider':row['provider'],'url':row['url'],'kind':store_kind,'verified':True,'lastChecked':source['reviewedAt']}],'sources':[{'provider':row['provider'],'url':row['url'],'verified':True,'lastChecked':source['reviewedAt']}],'warnings':[],'platformerInfo':{'focus':row['collection'],'platformScope':'Only the hardware or builds verified on the linked official page are asserted.','editionNote':row['caution'],'reviewBasis':'No Steam percentage is invented for a non-Steam game.'}}
        if row['key']=='kirby-forgotten-land':g['originalReleaseYear']=2022
        if row['key']=='super-mario-galaxy-collection':g['kind']='Classic collection';g['releaseNote']='2025 enhanced package of the two earlier Galaxy games, counted once.'
        if row['key'] in ['celeste-64','celeste-classic-2']:
            g['sources'].append({'provider':'Creator release chronology','url':'https://maddymakesgames.com/','verified':True,'lastChecked':source['reviewedAt']})
        if row['key']=='supertux':g['storefronts'].append({'provider':'Official downloads','url':'https://www.supertux.org/download.html','kind':'download','verified':True,'lastChecked':source['reviewedAt']})
        for key in ['image','screenshots','trailers','externalRating']:
            if old.get(ident,{}).get(key):g[key]=old[ident][key]
        items.append(g)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:items=list(pool.map(exact_media,items))
    target.write_text(json.dumps({'schemaVersion':1,'generatedAt':NOW,'hub':'Platformers','items':items},ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/platformers-external-report.json').write_text(json.dumps({'checkedAt':NOW,'records':len(items),'withImages':sum(bool(g.get('image')) for g in items),'withVideos':sum(bool(g.get('trailers')) for g in items),'gaps':[{'id':g['id'],'warnings':g['warnings'],'mediaError':g.get('mediaRefreshError')} for g in items if g['warnings']]},indent=2)+'\n')
if __name__=='__main__':main()
