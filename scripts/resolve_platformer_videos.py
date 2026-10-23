#!/usr/bin/env python3
"""Resolve reviewed media gaps, with exact product matching and source evidence.

This builds an additive overlay; it never changes game identities, editions,
release dates, ratings, or existing media. Candidate URLs are accepted only
when the exact source and a real media response agree. Playback is a separate
browser gate. Original announcement dates do not change current availability.
"""
from __future__ import annotations
import concurrent.futures,datetime as dt,hashlib,json,pathlib,re,unicodedata,urllib.parse,urllib.request
from bs4 import BeautifulSoup
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat();Q=R/'qa/platformer-video-resolution';Q.mkdir(parents=True,exist_ok=True)
UA='Mozilla/5.0 (compatible; GamesLibrary exact-source media verification)'
TARGET=R/'data/platformers-media-reviewed.json'

def get(url,limit=6000000):
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=30) as response:
        data=response.read(limit+1)
        if len(data)>limit:raise ValueError('Source exceeds bounded response size')
        return data,response.url

def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.casefold().replace('&','and')) if c.isascii() and c.isalnum())

def html_page(url):
    raw,resolved=get(url);soup=BeautifulSoup(raw,'html.parser')
    evidence={'sourceUrl':url,'resolvedUrl':resolved,'pageSha256':hashlib.sha256(raw).hexdigest(),'checkedAt':NOW,'pageTitle':soup.title.get_text(' ',strip=True) if soup.title else ''}
    (Q/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.html')).write_bytes(raw)
    return soup,evidence

def probe_mp4(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Range':'bytes=0-4095'})
    with urllib.request.urlopen(req,timeout=35) as response:
        first=response.read(4096)
        assert b'ftyp' in first[:64], 'Not an MP4 header'
        assert urllib.parse.urlsplit(response.url).hostname=='assets.nintendo.com','Unexpected media host'
        return {'url':url,'resolvedUrl':response.url,'status':response.status,'contentType':response.headers.get('Content-Type'),'contentRange':response.headers.get('Content-Range'),'headerSha256':hashlib.sha256(first).hexdigest()}

def cloudinary(public_id):
    assert public_id.startswith(('/store/software/','/Legacy Videos/','Legacy Videos/')),'Unapproved public asset path'
    url='https://assets.nintendo.com/video/upload/'+urllib.parse.quote(public_id.lstrip('/'),safe='/')+'.mp4'
    proof=probe_mp4(url)
    return url,proof

def nintendo_product(g):
    source=g['primaryUrl'];soup,proof=html_page(source)
    tag=soup.find('script',id='__NEXT_DATA__');assert tag,'Nintendo page data absent'
    obj=json.loads(tag.get_text());state=obj['props']['pageProps']['initialApolloState'];slug=urllib.parse.urlsplit(source).path.strip('/').split('/')[-1]
    matches=[x for key,x in state.items() if key.startswith('Product:') and isinstance(x,dict) and x.get('urlKey')==slug]
    assert len(matches)==1,'Exact Nintendo product not uniquely identified'
    product=matches[0];proof.update(productName=product['name'],sku=product.get('sku'),urlKey=slug)
    assets=[a for a in product.get('productGallery',[]) if isinstance(a,dict) and a.get('resourceType')=='video' and a.get('type')=='upload']
    assert assets,'Exact product has no video; recommendations are not accepted'
    public_id=assets[0]['publicId'];url,probe=cloudinary(public_id);proof.update(publicId=public_id,probe=probe)
    return {'name':product['name']+' — official product video','mp4':url,'poster':g.get('image'),'sourceUrl':source,'watchUrl':source,'credit':'Nintendo — exact product gallery','official':True,'verified':True,'verifiedAt':NOW,'editionNote':'Video belongs to the exact product slug shown in the source; no recommendation-carousel footage is substituted.'},proof

PLAY_PAGES={
'external:super-mario-odyssey':'https://play.nintendo.com/media/videos/super-mario-odyssey-nintendo-switch-trailer/',
'external:super-mario-maker-2':'https://play.nintendo.com/media/videos/super-mario-maker-2-trailer-nintendo-switch/',
}
def play_nintendo(g):
    source=PLAY_PAGES[g['id']];soup,proof=html_page(source)
    assert norm(g['name']) in norm(soup.get_text(' ',strip=True)),'Exact game title absent'
    tags=soup.find_all('play-video');assert len(tags)==1,'Expected one featured Play Nintendo video'
    tag=tags[0];assert tag.get('data-type')=='CLOUDINARY','Unsupported featured video provider'
    public_id=tag['data-videoid'];url,probe=cloudinary(public_id);proof.update(publicId=public_id,probe=probe)
    return {'name':g['name']+' — Nintendo trailer','mp4':url,'poster':g.get('image'),'sourceUrl':source,'watchUrl':source,'credit':'Play Nintendo — featured game video','official':True,'verified':True,'verifiedAt':NOW},proof

# Reviewed sources. A publisher-owned upload is preferred; GIGAZINE's own
# captured Celeste 64 footage is explicitly credited as editorial gameplay.
YOUTUBE={
 'external:yoshi-crafted-world':{'ids':['dcndZNVUxFM'],'terms':['yoshi','crafted','world'],'authors':['nintendo'],'official':True,'source':'https://www.youtube.com/watch?v=dcndZNVUxFM'},
 'steam:213610':{'ids':['zQwXwsToHTg'],'terms':['sonic','adventure','2'],'authors':['sega','sonic'],'official':True,'source':'https://www.youtube.com/watch?v=zQwXwsToHTg','editionNote':'Official HD re-release footage. This is not a claim that the footage was captured on PC.'},
 'steam:1730680':{'ids':['zCnxnsagRdk'],'pages':['https://www.bandainamcoent.com/news/celebrate-klonoa-25th-anniversary-klonoa-phantasy-reverie-series'],'terms':['klonoa','phantasy','reverie'],'authors':['bandai','nintendo','playstation'],'official':True},
 'steam:2661310':{'pages':['https://www.yachtclubgames.com/blog/shovel-knight-shovel-of-hope-dx-launches-in-2025/'],'terms':['shovel','hope','dx'],'authors':['yachtclub','nintendo'],'official':True,'editionNote':'Announcement footage for Shovel of Hope DX. The historical article is not proof of a current release; the catalog retains the current Steam watchlist state.'},
 'steam:227600':{'ids':['K-rfsYYLmgs'],'pages':['https://blog.playstation.com/2013/05/30/castle-of-illusion-reimagining-a-classic/'],'terms':['castle','illusion'],'authors':['sega','playstation'],'official':True,'editionNote':'Official footage for the 2013 re-imagining. A making-of feature can also show the 1990 original for comparison; it is not a separate game entry.'},
 'external:celeste-64':{'pages':['https://gigazine.net/news/20240131-celeste-64/'],'terms':['celeste','64'],'authors':['gigazine'],'official':False,'editionNote':'GIGAZINE editorial gameplay of Celeste 64, not a developer trailer and not a library hands-on review.'},
}

def youtube(g):
    spec=YOUTUBE[g['id']];candidates=[(i,spec.get('source','https://www.youtube.com/watch?v='+i),None) for i in spec.get('ids',[])];errors=[]
    for source in spec.get('pages',[]):
        try:
            soup,proof=html_page(source)
            for node in soup.select('.comments,#comments,.related-posts,.related'):node.decompose()
            for iframe in soup.find_all('iframe'):
                match=re.search(r'youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]{11})',iframe.get('src','') or iframe.get('data-src',''))
                if match:candidates.append((match[1],source,proof))
            for a in soup.find_all('a',href=True):
                match=re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})',a['href'])
                if match:candidates.append((match[1],source,proof))
        except Exception as exc:errors.append(source+': '+str(exc))
    seen=set()
    for vid,source,proof in candidates:
        if vid in seen:continue
        seen.add(vid)
        try:
            watch='https://www.youtube.com/watch?v='+vid;api='https://www.youtube.com/oembed?'+urllib.parse.urlencode({'url':watch,'format':'json'})
            raw,_=get(api,100000);data=json.loads(raw);title=norm(data['title']);author=norm(data['author_name'])
            assert all(norm(term) in title for term in spec['terms']),'Wrong title: '+data['title']
            assert any(norm(a) in author for a in spec['authors']),'Unreviewed uploader: '+data['author_name']
            record={'name':data['title'],'youtube':vid,'poster':data.get('thumbnail_url') or g.get('image'),'sourceUrl':source,'watchUrl':watch,'credit':data['author_name']+(' — official upload' if spec['official'] else ' — credited editorial gameplay'),'official':spec['official'],'verified':True,'verifiedAt':NOW}
            if spec.get('editionNote'):record['editionNote']=spec['editionNote']
            return record,{'sourceUrl':source,'pageEvidence':proof,'oembedUrl':api,'title':data['title'],'author':data['author_name'],'authorUrl':data.get('author_url'),'checkedAt':NOW}
        except Exception as exc:errors.append(vid+': '+str(exc))
    raise ValueError('No exact video passed title/uploader verification: '+repr(errors))

def resolve(g):
    try:
        if g['id'] in PLAY_PAGES:video,proof=play_nintendo(g)
        elif g['id'] in YOUTUBE:video,proof=youtube(g)
        elif urllib.parse.urlsplit(g['primaryUrl']).hostname=='www.nintendo.com':video,proof=nintendo_product(g)
        else:raise ValueError('No reviewed external video source; public browser capture handled separately')
        print('RESOLVED',g['id'],video['name'],flush=True)
        return g['id'],{'trailers':[video],'sources':[{'provider':'Platformer exact-video verification','url':proof['sourceUrl'],'verified':True,'lastChecked':NOW}],'mediaEvidence':proof},None
    except Exception as exc:
        print('GAP',g['id'],str(exc),flush=True);return g['id'],None,{'id':g['id'],'name':g['name'],'reason':str(exc)}

def main():
    data=json.loads((R/'data/catalog.json').read_text());by={g['id']:g for g in data['items']};gaps=json.loads((R/'data/platformers-study-report.json').read_text())['mediaGaps'];games=[by[x['id']] for x in gaps if x['videoMissing']]
    output=json.loads(TARGET.read_text()) if TARGET.exists() else {'schemaVersion':1,'overrides':{}}
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(resolve,games))
    for ident,extra,error in results:
        if extra:output['overrides'][ident]=extra
    output['checkedAt']=NOW;output['policy']='Additive, exact-edition media. Official footage and editorial captures retain distinct credits; URL verification is separate from actual playback.'
    TARGET.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    report={'checkedAt':NOW,'accepted':len(output['overrides']),'gaps':[error for _,_,error in results if error],'ids':sorted(output['overrides'])}
    (Q/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
