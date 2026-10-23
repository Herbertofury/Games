#!/usr/bin/env python3
"""Refresh official Steam facts; never turn missing data into invented facts."""
import argparse, concurrent.futures, csv, datetime as dt, difflib, hashlib, html, json, pathlib, re, time, urllib.request, urllib.parse, urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1]
NOW=dt.datetime.now(dt.timezone.utc).isoformat()
UA='GamesCatalog/1.0 (+https://github.com/Herbertofury/Games)'
def get(url):
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)
        except (urllib.error.URLError,TimeoutError,ValueError) as e:
            if attempt==2: raise
            delay=2**(attempt+1)
            if isinstance(e,urllib.error.HTTPError) and e.code==429: delay=max(delay,int(e.headers.get('Retry-After','10')))
            time.sleep(min(delay,60))
def reviews_url(appid):
    params={'appid':int(appid),'languages':['all'],'purchase_type':1,'review_type':0,'filter':0,'day_range':0,'num_per_page':1,'display_language':'english'}
    return 'https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/?'+urllib.parse.urlencode({'input_json':json.dumps(params,separators=(',',':'))})
def reviews_query(appid):
    payload=get(reviews_url(appid));response=payload.get('response',payload)
    q=response.get('query_summary')
    if not isinstance(q,dict) or 'total_reviews' not in q:raise ValueError('Steam review summary was not returned')
    for key in ('total_positive','total_negative','total_reviews'):q[key]=int(q.get(key,0))
    if q['total_positive']+q['total_negative']!=q['total_reviews']:raise ValueError('Steam review totals do not reconcile')
    return q
def repair_reviews(g):
    if g.get('verification')!='verified':return g
    try:
        q=reviews_query(g['appid']);total=q['total_reviews']
        g.update(rating=round(100*q['total_positive']/total,1) if total else None,reviewCount=total,reviewLabel=q.get('review_score_desc'),reviewError=None,reviewsVerifiedAt=NOW)
        g['warnings']=[w for w in g.get('warnings',[]) if w not in ('Small review sample','Review refresh unavailable')]
        if total<100:g['warnings'].append('Small review sample')
        g['sources']=[x for x in g.get('sources',[]) if x.get('provider')!='Steam reviews API']+[{'provider':'Steam reviews API','url':reviews_url(g['appid']),'verified':True,'lastChecked':NOW}]
    except Exception as e:
        g['reviewError']=str(e)
        g['warnings']=list(dict.fromkeys(g.get('warnings',[])+['Review refresh unavailable']))
    return g
def text(s): return html.unescape(re.sub('<[^>]+>',' ',s or '')).strip()
def norm(s): return re.sub('[^a-z0-9]','',s.lower())
def match(a,b):
    a,b=norm(a),norm(b)
    return a==b or (min(len(a),len(b))>=9 and (a in b or b in a)) or difflib.SequenceMatcher(None,a,b).ratio()>=0.84
def details(appid):
    x=get(f'https://store.steampowered.com/api/appdetails?appids={appid}&l=english&cc=us').get(str(appid),{})
    return x.get('data') if x.get('success') else None
def date_iso(s):
    for fmt in ('%b %d, %Y','%d %b, %Y','%B %d, %Y','%d %B, %Y'):
        try: return dt.datetime.strptime(s,fmt).date().isoformat()
        except ValueError: pass
    return None
def resolve(seed,old,force):
    sid=str(seed['appid']); prior=old.get(sid)
    if prior and not force and prior.get('verifiedAt'):
        age=dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(prior['verifiedAt'])
        if age.total_seconds()<86400:
            prior.update(collection=seed['collection'],fit=int(seed['fit']))
            return repair_reviews(prior) if prior.get('reviewError') else prior
    try:
        aid=int(sid); d=details(aid)
        if not d or not match(seed['name'],d.get('name','')):
            results=get('https://store.steampowered.com/api/storesearch/?'+urllib.parse.urlencode({'term':seed['name'],'l':'english','cc':'us'})).get('items',[])
            exact=next((x for x in results if match(seed['name'],x.get('name',''))),None)
            if exact:
                aid=exact['id'];d=details(aid)
        if not d or not match(seed['name'],d.get('name','')) or d.get('type')!='game':
            raise ValueError('Steam identity not confirmed'+(': '+d.get('name','') if d else ''))
        u=f'https://store.steampowered.com/app/{aid}/'; review_error=None
        try:
            q=reviews_query(aid)
        except Exception as e:
            q={'total_reviews':prior.get('reviewCount',0),'total_positive':round((prior.get('rating') or 0)*prior.get('reviewCount',0)/100),'review_score_desc':prior.get('reviewLabel')} if prior else {}
            review_error=str(e)
        total=q.get('total_reviews',0);pos=q.get('total_positive',0)
        cats=[x['description'] for x in d.get('categories',[])];genres=[x['description'] for x in d.get('genres',[])]
        release=d.get('release_date',{});price=d.get('price_overview',{})
        screenshots=[{'src':x['path_full'],'thumbnail':x['path_thumbnail'],'sourceUrl':u,'alt':d['name']+' official Steam screenshot','credit':'Developer / Steam','verified':True} for x in d.get('screenshots',[])]
        movies=[]
        for x in d.get('movies',[]):
            mp4=x.get('mp4',{});webm=x.get('webm',{})
            movies.append({'name':x.get('name','Official trailer'),'poster':x.get('thumbnail'),'mp4':mp4.get('max') or mp4.get('480'),'webm':webm.get('max') or webm.get('480'),'hls':x.get('hls_h264') or x.get('hls_av1'),'sourceUrl':u,'id':x.get('id')})
        searchable=' '.join([d.get('short_description',''),text(d.get('about_the_game','')),seed['collection']]).lower()
        tags=[seed['collection']]+genres
        for term,label in [('roguel','Roguelite'),('bullet heaven','Bullet heaven'),('survivors','Survivors-like'),('loot','Loot'),('necroman','Necromancy'),('pixel','Pixel art'),('dungeon','Dungeon crawler'),('boss','Boss fights'),('craft','Crafting')]:
            if term in searchable: tags.append(label)
        if any('co-op' in x.lower() for x in cats):tags.append('Co-op')
        if 'Early Access' in genres:tags.append('Early Access')
        status='Upcoming' if release.get('coming_soon') else 'Early Access' if 'Early Access' in genres else 'Released'
        return {'id':'steam:'+str(aid),'appid':aid,'seedId':sid,'seedName':seed['name'],'name':d['name'],'collection':seed['collection'],'fit':int(seed['fit']),'summary':text(d.get('short_description','')),'developers':d.get('developers',[]),'publishers':d.get('publishers',[]),'genres':genres,'tags':sorted(set(tags)),'features':cats,'status':status,'releaseDate':date_iso(release.get('date','')),'releaseLabel':release.get('date','Unknown'),'comingSoon':bool(release.get('coming_soon')),'free':bool(d.get('is_free')),'price':price.get('final_formatted'),'priceMinor':price.get('final'),'currency':price.get('currency'),'discount':price.get('discount_percent',0),'platforms':[k for k,v in d.get('platforms',{}).items() if v],'rating':round(100*pos/total,1) if total else None,'reviewCount':total,'reviewLabel':q.get('review_score_desc'),'reviewError':review_error,'reviewsVerifiedAt':NOW if not review_error else (prior or {}).get('reviewsVerifiedAt'),'metacritic':d.get('metacritic'),'image':d.get('header_image'),'background':d.get('background_raw') or d.get('background'),'screenshots':screenshots,'trailers':movies,'steamUrl':u,'website':d.get('website'),'verifiedAt':NOW,'verification':'verified','sources':[{'provider':'Steam','url':u,'verified':True,'lastChecked':NOW},{'provider':'Steam store API','url':f'https://store.steampowered.com/api/appdetails?appids={aid}&l=english&cc=us','verified':True,'lastChecked':NOW},{'provider':'Steam reviews API','url':reviews_url(aid),'verified':not review_error,'lastChecked':NOW}],'warnings':(['Small review sample'] if total<100 and not review_error else [])+(['Review refresh unavailable'] if review_error else [])}
    except Exception as e:
        if prior and prior.get('verification')=='verified':
            prior['warnings']=list(set(prior.get('warnings',[])+['Refresh failed; retained prior verified snapshot']))
            prior['lastRefreshError']=str(e);return prior
        return {'id':'pending:'+sid,'appid':int(sid),'seedId':sid,'seedName':seed['name'],'name':seed['name'],'collection':seed['collection'],'fit':None,'summary':'This recommendation is retained from the earlier conversation. Its Steam identity or current availability still needs verification.','tags':[seed['collection']],'genres':[],'developers':[],'platforms':[],'features':[],'status':'Needs verification','verification':'unresolved','reviewCount':0,'rating':None,'releaseDate':None,'releaseLabel':'Unverified','free':False,'steamUrl':f'https://store.steampowered.com/app/{sid}/','sources':[],'warnings':[str(e)],'trailers':[],'screenshots':[]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');args=ap.parse_args()
    seeds=list(csv.DictReader((ROOT/'data/seeds.tsv').open(),delimiter='\t'))
    assert len({s['appid'] for s in seeds})==len(seeds),'Duplicate seed IDs'
    target=ROOT/'data/catalog.json';old={}
    if target.exists():old={str(g.get('seedId') or g.get('appid')):g for g in json.loads(target.read_text()).get('items',[]) if g.get('seedId') or g.get('appid')}
    out=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs={pool.submit(resolve,s,old,args.force):s for s in seeds}
        for job in concurrent.futures.as_completed(jobs):
            g=job.result();out.append(g);print(g['verification'],g['name'],flush=True)
    out.sort(key=lambda x:x['name'].casefold())
    ids=[g['id'] for g in out];assert len(set(ids))==len(ids),'Resolved IDs collide; reconcile seeds before publishing'
    facts={'schemaVersion':1,'catalogId':'herbertofury-games','title':'Games','generatedAt':NOW,'sourceRepository':'https://github.com/Herbertofury/Games','sourceWiki':'https://github.com/Herbertofury/Games/wiki','sources':[{'provider':'Conversation','kind':'discovery','description':'Both earlier recommendation lists, plus Vampire Survivors as the reference game. Claims are not treated as verified facts.'},{'provider':'Steam','kind':'canonical-facts','description':'Official store metadata, screenshots, trailers and all-language, all-purchase-type review totals.'}],'build':{'generator':'games-catalog/1.0.0','seedHash':hashlib.sha256((ROOT/'data/seeds.tsv').read_bytes()).hexdigest(),'inputCount':len(seeds),'verifiedCount':sum(x['verification']=='verified' for x in out),'unresolvedCount':sum(x['verification']!='verified' for x in out),'mediaCount':sum(len(x['screenshots'])+len(x['trailers'])+bool(x.get('image')) for x in out)},'items':out}
    facts['build']['datasetHash']=hashlib.sha256(json.dumps(out,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    target.write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(facts['build'],indent=2))
if __name__=='__main__':main()
